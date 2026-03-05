from fastapi import APIRouter, HTTPException
from configurations import db
from database.Quiz.models import UserQuiz, QuizScore
from AI_Utility.quiz import generateQuizFromGemini
from datetime import datetime

quiz_router = APIRouter()
users_collection = db["users"]
domain_collection = db["domain"]
quiz_collection = db["quiz"]

@quiz_router.post("/get-quiz")
def get_quiz(user: UserQuiz):
    try:
        user_doc = users_collection.find_one({"employee_id": str(user.employee_id)})
        if not user_doc: raise HTTPException(status_code=404, detail="User not found")

        user_oid = str(user_doc["_id"])
        domain_id = user_doc.get("domain")
        if not domain_id: raise HTTPException(status_code=400, detail="User has no domain assigned")
        
        domain_doc = domain_collection.find_one({"_id": domain_id})
        if not domain_doc: raise HTTPException(status_code=404, detail="Domain details not found")

        domain_name = domain_doc.get("domain_name", "General")

        # 4. Generate the Quiz using your AI Utility
        # Passing domain_name and a default count of 10
        quiz_data = generateQuizFromGemini({
            "domain": domain_name,
            "count": 10
        })

        return {
            "status_code": 200,
            "user_id": user_oid,
            "domain": domain_name,
            "quiz": quiz_data
        }
    except HTTPException as hex:
        raise hex
    except Exception as ex:
        raise HTTPException(
            status_code=500,
            detail=f"Some exception occured in Auth/routes.py/get_quiz() /quiz/get-quiz :: {ex}"
        )

@quiz_router.post("/get-score")
def calculate_quiz_score(data: QuizScore):
    try:
        user_doc = users_collection.find_one({"employee_id": str(data.employee_id)})
        if not user_doc: raise HTTPException(status_code=404, detail="User not found for the given employee_id")
        
        user_id = user_doc["_id"]
        numeric_score = 0
        try:
            numeric_score = float(data.score)
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Invalid score format. Must be a number.")
        
        quiz_record = {
            "user_id": user_id,
            "employee_id": str(data.employee_id),
            "score": data.score,
            "status": "pass" if numeric_score >= 75 else "fail",
            "updatedAt": datetime.utcnow()
        }
        quiz_collection.insert_one(quiz_record)

        return {
            "status_code": 200,
            "data": {
                "user_id": str(user_id),
                "score": data.score,
                "status": "pass" if numeric_score >= 75 else "fail"
            }
        }
    except HTTPException as hex:
        raise hex
    except Exception as ex:
        raise HTTPException(
            status_code=500,
            detail=f"Some exception occured in Auth/routes.py/calculate_quiz_score() /quiz/get-score :: {ex}"
        )