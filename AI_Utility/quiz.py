import os
import json
from google import genai
from typing import List, Dict, Any
from fastapi import HTTPException
from dotenv import load_dotenv
from database.Quiz.models import QuizResponse

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def generateQuizFromGemini(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    domain = (payload.get("domain") or "").strip()
    count = int(payload.get("count") or 10)

    if not domain: 
        raise HTTPException(status_code=400, detail="Domain is required.")

    prompt = (
        f"You are an expert technical examiner for {domain}.\n\n"
        f"Task: Create a {count}-question assessment.\n"
        "Difficulty: Progression from Basic (foundational) to Medium (applied/conceptual).\n"
        "Instructions:\n"
        "1. Autonomously select the most important topics.\n"
        "2. Avoid characters like *, /, or # for voice-reader safety.\n"
        "3. Ensure questions are in ascending order of difficulty.\n"
        "4. Provide exactly 4 options per question."
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": QuizResponse,
                "temperature": 0.7
            }
        )

        data = json.loads(response.text)
        raw_quiz = data.get("quiz", [])

        return [
            {
                "id": i,
                "question": item.get("question"),
                "options": item.get("options"),
                "correct": item.get("correct")
            }
            for i, item in enumerate(raw_quiz, start=1)
        ]

    except Exception as e:
        raise HTTPException(
            status_code=502, 
            detail=f"AI generation failed: {str(e)}"
        )