from fastapi import APIRouter, HTTPException
from configurations import db
from database.Quiz.models import UserQuiz
from AI_Utility.quiz import generateQuizFromGemini

quiz_router = APIRouter()
users_collection = db["users"]
domain_collection = db["domain"]

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