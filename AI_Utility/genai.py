import os
import json
import re
from google import genai
from dotenv import load_dotenv
from database.Interviews.models import InterviewComplete
from database.DTOs.user_interview_question import UserInterviewDTO
from database.Interviews.models import InterviewFinalComplete
from database.DTOs.evaluation_metrics import EvaluationMetrics
from typing import List, Dict, Any, Tuple

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# HELPERS
def _voice_safe_sanitize(questions: List[str]) -> List[str]:
    """
    Removes characters that confuse Voice Agents/TTS engines.
    """
    cleaned = []
    for q in questions:
        q = q.replace("*", "").replace("/", " or ").replace("\\", " ")
        q = re.sub(r'#{1,6}\s?', '', q) 
        q = " ".join(q.split())
        if q:
            cleaned.append(q)
    return cleaned


def _clamp_num_questions(n: int | None) -> int:
    try:
        if n is None: return 15
        n = int(n)
    except Exception: return 15
    return max(12, min(17, n))

def _as_list(value) -> list[str]:
    if value is None: return []
    if isinstance(value, str):
        if "," in value:
            return [p.strip() for p in value.split(",") if p.strip()]
        return [value.strip()] if value.strip() else []
    if isinstance(value, (list, tuple, set)):
        return [str(v).strip() for v in value if str(v).strip()]
    return []

def _percent_allocation(total: int, spec: list[Tuple[str, float]]) -> Dict[str, int]:
    raw = [(label, p * total) for label, p in spec]
    floors = {label: int(v // 1) for label, v in raw}
    remainder = total - sum(floors.values())
    fracs = sorted(((label, v - int(v // 1)) for label, v in raw), key=lambda x: x[1], reverse=True)
    for i in range(remainder):
        floors[fracs[i % len(fracs)][0]] += 1
    return floors

def _build_distribution(level: int, num_q: int, weaknesses: List[str]) -> Tuple[Dict[str, int], Dict[str, Any]]:
    policy = {"difficulty": "mixed", "notes": []}
    if int(level) == 1:
        spec = [("imp_provided", 0.55), ("basic_provided", 0.25), ("prob_provided", 0.20)]
        counts = _percent_allocation(num_q, spec)
        counts.update({"imp_weakness": 0, "lessimp_weakness": 0})
        policy.update({"difficulty": "easy-to-moderate", "notes": ["Level 1: Restricted to provided topics (55/25/20)."]})
        return counts, policy

    has_weak = len(weaknesses) > 0
    if not has_weak:
        spec = [("imp_provided", 0.60), ("basic_provided", 0.20), ("prob_provided", 0.20)]
        counts = _percent_allocation(num_q, spec)
        counts.update({"imp_weakness": 0, "lessimp_weakness": 0})
        policy.update({"difficulty": "moderate-to-hard", "notes": ["No weaknesses: Redistributed 30% to provided topics."]})
        return counts, policy

    spec = [("imp_provided", 0.40), ("basic_provided", 0.20), ("prob_provided", 0.10), ("imp_weakness", 0.20), ("lessimp_weakness", 0.10)]
    counts = _percent_allocation(num_q, spec)
    if len(weaknesses) < 4:
        policy["difficulty"] = "moderate-to-hard"
        cap = max(2, len(weaknesses) * 2)
        wk_total = counts["imp_weakness"] + counts["lessimp_weakness"]
        if wk_total > cap:
            overflow = wk_total - cap
            move_imp = min(overflow, counts["imp_weakness"])
            counts["imp_weakness"] -= move_imp
            counts["imp_provided"] += move_imp
            overflow -= move_imp
            if overflow > 0:
                move_less = min(overflow, counts["lessimp_weakness"])
                counts["lessimp_weakness"] -= move_less
                counts["prob_provided"] += move_less
            policy["notes"].append(f"Capped weaknesses at {cap}; overflow redistributed.")
    return counts, policy

def _sanitize_questions(questions: List[str]) -> List[str]:
    cleaned, seen = [], set()
    for q in questions:
        q = str(q).strip().lstrip(" -0123456789).:").strip()
        q = q.replace("/", " ").replace("*", " ")
        if q and q.lower() not in seen:
            cleaned.append(q)
            seen.add(q.lower())
    return cleaned

def _safe_json_loads(text: str) -> Dict[str, Any]:
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) and "questions" in data else {"questions": data if isinstance(data, list) else [text]}
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if -1 < start < end:
            try: return json.loads(text[start:end+1])
            except: pass
        return {"questions": [text]}

def _make_prompt(domain, proficiency, username, performance_level, level, num_q, provided_topics, weaknesses, counts, policy):
    system_instruction = (
        "You are a strict JSON generator. Return ONLY a JSON object with a key 'questions' mapping to an array of strings. "
        "No markdown, no comments, no special characters like / or *."
    )
    
    lines = [f"- {v} {k.replace('_', ' ')} questions." for k, v in counts.items() if v > 0]
    prompt = (
        f"Act as a Senior {domain} Interviewer for a {proficiency} candidate ({username}).\n"
        f"Level: {level}; Performance: {performance_level}. Generate exactly {num_q} questions.\n"
        f"Topics: {', '.join(provided_topics)}. Weaknesses: {', '.join(weaknesses) if weaknesses else 'None'}.\n"
        f"Distribution:\n{chr(10).join(lines)}\nDifficulty: {policy['difficulty']}.\n"
        f"Rule: No '/' or '*'. Concise questions (1-2 mins). Return JSON ONLY: "
        f'{{"questions": ["Q1", "Q2"]}}'
    )
    return system_instruction, prompt

def _call_gemini(prompt: str, system_instruction: str, difficulty: str) -> Dict[str, Any]:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={
            "system_instruction": system_instruction,
            "response_mime_type": "application/json",
            "temperature": 0.8 if difficulty == "moderate-to-hard" else 0.7,
        },
    )
    return _safe_json_loads(response.text)

# ---------------- MAIN FUNCTION ----------------

def getDataFromGemini(user: UserInterviewDTO):
    try:
        domain = getattr(user, "domain", "Technology")
        username = getattr(user, "username", "Candidate")
        level = int(getattr(user, "level", 2))
        num_q = _clamp_num_questions(getattr(user, "numQuestions", None))
        
        provided_topics = _as_list(getattr(user, "topics", None)) or _as_list(getattr(user, "topic", None)) or ["Core Fundamentals"]
        weaknesses = _as_list(getattr(user, "weaknesses", None))
        
        counts, policy = _build_distribution(level, num_q, weaknesses)
        system_instruction, prompt = _make_prompt(
            domain, getattr(user, "proficiency", f"Level {level}"), username, 
            getattr(user, "performanceLevel", "average"), level, num_q, 
            provided_topics, weaknesses, counts, policy
        )

        result = _call_gemini(prompt, system_instruction, policy["difficulty"])
        questions = _sanitize_questions(result.get("questions", []))

        if len(questions) != num_q:
            corrective_prompt = f"{prompt}\n\nERROR: You returned {len(questions)} questions. Return EXACTLY {num_q} now."
            result = _call_gemini(corrective_prompt, system_instruction, policy["difficulty"])
            questions = _sanitize_questions(result.get("questions", []))

        return {"questions": questions[:num_q]}
    except Exception as e:
        return {"error": "Failed to generate questions", "details": str(e)}


def evaluateUserBasedOnTranscribe(data: InterviewComplete):
    system_instruction = """
        You are a professional interviewer analyzing a mock interview. Evaluate the candidate strictly based on the provided transcript.
        When identifying weaknesses, use standard industry terminology (e.g., 'REST API Fundamentals' instead of 'He doesn't know APIs')
        to ensure consistency across multiple interview sessions.
    """
    
    prompt = f"""
    Analyze the following interview transcript:
    {data.transcribe}

    Task:
    Provide a score (0-100) for each category and a critical evaluation. 
    Do not be lenient; point out mistakes or gaps in knowledge clearly.

    Evaluation Criteria:
    - communication_skills: (0-100)
    - technical_knowledge: (0-100)
    - problem_solving: (0-100)
    - cultural_role_fit: (0-100)
    - confidence_clarity: (0-100)
    
    New Required Formatting:
    1. detailed_feedback: This must be exactly ONE of these three strings: "Good", "Average", or "Bad" based on the overall performance.
    2. areas_for_improvement: This must be a JSON array (list) of strings containing specific, actionable critiques.
    3. weaknesses: Identify specific technical or soft skill gaps. 
       - Return as a JSON array of strings: ["Topic A", "Topic B"].
       - Use concise, standard titles for topics (e.g., 'Asynchronous Programming', 'SQL Indexing').
       - These will be used to generate future questions, so be precise.
    Return the response ONLY as a JSON object.
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "system_instruction": system_instruction,
                "response_mime_type": "application/json",
                "response_schema": EvaluationMetrics
            }
        )
        
        evaluation_json = json.loads(response.text)
        return evaluation_json

    except Exception as e:
        return {
            "error": "Failed to generate evaluation",
            "details": str(e)
        }
    
def getFinalInterviewQuestions(user_data: Dict, user_path: Dict, num_q: int):
    assignments = user_path.get("assignments_status", [])
    all_topics = [a.get("title") for a in assignments if a.get("title")]
    
    raw_weaknesses = []
    for a in assignments:
        ws = a.get("weakness", [])
        if isinstance(ws, list):
            raw_weaknesses.extend(ws)
    
    unique_weaknesses = list(set([w.strip().title() for w in raw_weaknesses if w]))

    system_instruction = (
        "You are a Senior Technical Examiner. Return ONLY a JSON object with a key 'questions' "
        "mapping to an array of strings. No markdown, no comments."
    )
    
    prompt = (
        f"Conduct a FINAL Intermediate Level assessment for {user_data.get('username', 'Candidate')}.\n"
        f"The candidate has completed a learning path in {user_data.get('domain', 'Technology')}.\n"
        f"Total Questions required: {num_q}.\n\n"
        f"Syllabus (Topics Covered): {', '.join(all_topics)}.\n"
        f"Historical Weaknesses to focus on: {', '.join(unique_weaknesses) if unique_weaknesses else 'None'}.\n\n"
        f"Instructions:\n"
        f"- Ensure questions are at an INTERMEDIATE level.\n"
        f"- Cover the broad syllabus but weight 40% of questions towards the weaknesses.\n"
        f"- Return JSON: {{\"questions\": [\"Q1\", \"Q2\"]}}"
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "system_instruction": system_instruction,
                "response_mime_type": "application/json",
                "temperature": 0.75,
            },
        )
        data = _safe_json_loads(response.text)
        data["questions"] = _voice_safe_sanitize(data.get("questions", []))
        return data
    except Exception as e:
        return {"error": str(e)}


def evaluateFinalInterview(data: InterviewFinalComplete):
    system_instruction = """
        You are a professional interviewer analyzing a final interview. Evaluate the candidate strictly based on the provided transcript.
        When identifying weaknesses, use standard industry terminology (e.g., 'REST API Fundamentals' instead of 'He doesn't know APIs')
        to ensure consistency across multiple interview sessions.
    """
    
    prompt = f"""
    Analyze the following interview transcript:
    {data.transcribe}

    Task:
    Provide a score (0-100) for each category and a critical evaluation. 
    Do not be lenient; point out mistakes or gaps in knowledge clearly.

    Evaluation Criteria:
    - communication_skills: (0-100)
    - technical_knowledge: (0-100)
    - problem_solving: (0-100)
    - cultural_role_fit: (0-100)
    - confidence_clarity: (0-100)
    
    New Required Formatting:
    1. detailed_feedback: This must be exactly ONE of these three strings: "Good", "Average", or "Bad" based on the overall performance.
    2. areas_for_improvement: This must be a JSON array (list) of strings containing specific, actionable critiques.
    3. weaknesses: Identify specific technical or soft skill gaps. 
       - Return as a JSON array of strings: ["Topic A", "Topic B"].
       - Use concise, standard titles for topics (e.g., 'Asynchronous Programming', 'SQL Indexing').
       - These will be used to generate future questions, so be precise.
    Return the response ONLY as a JSON object.
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "system_instruction": system_instruction,
                "response_mime_type": "application/json",
                "response_schema": EvaluationMetrics
            }
        )
        
        evaluation_json = json.loads(response.text)
        return evaluation_json
    except Exception as e:
        return {"error": "Evaluation failed", "details": str(e)}
