from typing import List, Dict, Any
import json

# ---------------- FINAL INTERVIEW UTILITIES ----------------

def getFinalInterviewQuestions(user_data: Dict, user_path: Dict, num_q: int):
    """
    Aggregates all topics and unique weaknesses to generate 
    a comprehensive 'Final' exam.
    """
    # 1. Extract all topic names from the learning path
    assignments = user_path.get("assignments_status", [])
    all_topics = [a.get("title") for a in assignments if a.get("title")]
    
    # 2. Extract and Deduplicate all weaknesses
    raw_weaknesses = []
    for a in assignments:
        ws = a.get("weakness", [])
        if isinstance(ws, list):
            raw_weaknesses.extend(ws)
    
    # Clean, Title Case, and Deduplicate
    unique_weaknesses = list(set([w.strip().title() for w in raw_weaknesses if w]))

    # 3. Construct the prompt specifically for a "Final" Intermediate assessment
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
            model="gemini-2.0-flash", # Use latest stable
            contents=prompt,
            config={
                "system_instruction": system_instruction,
                "response_mime_type": "application/json",
                "temperature": 0.75,
            },
        )
        return _safe_json_loads(response.text)
    except Exception as e:
        return {"error": str(e)}

def evaluateFinalInterview(data: InterviewFinalComplete):
    """
    Strictly evaluates the final performance without saving to DB.
    """
    prompt = f"""
    Evaluate this FINAL INTERMEDIATE INTERVIEW transcript:
    {data.transcribe}

    Provide a comprehensive breakdown:
    - Scores (0-100) for communication, technical, and problem-solving.
    - A 'detailed_feedback' string: "Good", "Average", or "Bad".
    - A list of 'areas_for_improvement'.
    
    This is the end of their course, so be very specific about whether they are job-ready.
    Return response as JSON.
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": EvaluationMetrics
            }
        )
        return json.loads(response.text)
    except Exception as e:
        return {"error": "Evaluation failed", "details": str(e)}