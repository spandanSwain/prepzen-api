from fastapi import APIRouter, HTTPException
from configurations import db
from datetime import datetime
from database.Users.models import FinalUsers
from database.Interviews.models import InterviewFinalComplete
from AI_Utility.genai import getFinalInterviewQuestions, evaluateFinalInterview
from bson import ObjectId

final_router = APIRouter()
users_collection = db["users"]
domain_collection = db["domain"]
path_collection = db["learning_path"]

@final_router.post("/start-interview")
def final_get_questions(user: FinalUsers):
    try:
        user_data = users_collection.find_one({"employee_id": user.employee_id})
        if not user_data:
            return HTTPException(
                status_code=404,
                detail="User not found"
            )
        
        user_path = path_collection.find_one({"user_id": user_data["_id"]})
        if not user_path:
            raise HTTPException(
                status_code=404,
                detail="Learning path not found for this user"
            )
        
        num_q = int(user.numQuestions) if user.numQuestions.isdigit() else 15
        questions_data = getFinalInterviewQuestions(user_data, user_path, num_q)
        
        return {
            "status": "success",
            "type": "FINAL_INTERVIEW",
            "proficiency": "Intermediate",
            "data": questions_data
        }
    except HTTPException as hex:
        raise hex
    except Exception as ex:
        raise HTTPException(
            status_code=500,
            detail=f"Some exception occured in Final/routes.py/final_get_questions() /final/start-interview :: {ex}"
        )
    

@final_router.post("/metrics")
def final_evaluation(data: InterviewFinalComplete):
    try:
        evaluation = evaluateFinalInterview(data)
        return {
            "evaluation": evaluation
        }
    except HTTPException as hex:
        raise hex
    except Exception as ex:
        raise HTTPException(
            status_code=500,
            detail=f"Some exception occured in Final/routes.py/final_evaluation() /final/metrics :: {ex}"
        )