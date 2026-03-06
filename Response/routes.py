from fastapi import APIRouter, HTTPException
from configurations import db
from datetime import datetime
from database.Interviews.models import Interviews
from database.DTOs.user_interview_question import UserInterviewDTO
from AI_Utility.genai import getDataFromGemini
from bson import ObjectId

response_router = APIRouter()
interview_collection = db["Interviews"]
users_collection = db["users"]
path_collection = db["learning_path"]

@response_router.post("/schedule-interview")
def start_interview(data: Interviews):
    try:
        interview_doc = {
            "user_id": ObjectId(data.user_id),
            "proficiency": data.proficiency,
            "topic": data.topic,
            "numQuestions": data.numQuestions,
            "createdAt": datetime.utcnow(),
        }

        userObj: UserInterviewDTO = createUserInterviewDTO(interview_doc)

        if not userObj: raise HTTPException(status_code=404, detail="User not found")
        
        # FIX THIS ASAP
        ai_response = getDataFromGemini(userObj)

        result = interview_collection.insert_one(interview_doc)
        interview_id = str(result.inserted_id)

        return {
            "interview_id": interview_id,
            "response": ai_response
        }

    except HTTPException as hex:
        raise hex
    except Exception as ex:
        raise HTTPException(
            status_code=500,
            detail=f"Some exception occured in Response/routes.py/schedule_interview() /response/start-interview :: {ex}"
        )



def createUserInterviewDTO(data: dict):     
    user_id = ObjectId(data["user_id"])
    user_data = users_collection.find_one({"_id": user_id})
    if not user_data: return None

    user_path = path_collection.find_one({"user_id": user_id})
    if not user_path: return None

    target_assignment_id = str(data["topic"])
    assignment_details = next(
        (a for a in user_path.get("assignments_status", []) if str(a["assignment_id"]) == target_assignment_id), 
        None
    )

    if not assignment_details: return None

    return UserInterviewDTO(
        username=user_data.get("name") or user_data.get("username", "Candidate"),
        domain=str(user_data.get("domain", "Technology")),
        performanceLevel=user_data.get("performanceLevel", "average"),
        
        proficiency=data["proficiency"],
        level=user_path.get("current_level", 1),
        
        topic=str(assignment_details.get("title")),
        numQuestions=int(data["numQuestions"]),
        
        weaknesses=assignment_details.get("weakness", [])
    )