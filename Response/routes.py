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

        # DUMMY IF GEMINI IS DOWN
        # ai_response = {
        #     "questions": [
        #         "what is an array?",
        #         "what is difference between arraylist and hashmap",
        #         "give a real world use case of hashmap and hashset",
        #         "tell me about this MVC project of yours"
        #     ]
        # }

        result = interview_collection.insert_one(interview_doc)
        interview_id = str(result.inserted_id)

        # adding user_id to interview not reverse
        # users_collection.update_one(
        #     {"_id": ObjectId(data.user_id)},
        #     {"$push": {"interviews_attended": ObjectId(interview_id)}}
        # )

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



def createUserInterviewDTO(data):
    uidto = UserInterviewDTO()
    
    user_id = ObjectId(data["user_id"])
    user_data = users_collection.find_one({"_id": user_id})

    if not user_data:
        return None

    uidto.username = user_data.get("name", "")
    uidto.domain = user_data.get("domain", "")
    uidto.performanceLevel = user_data.get("performanceLevel", "easy")

    uidto.numQuestions = data.get("numQuestions")
    uidto.proficiency = data.get("proficiency")
    uidto.topic = data.get("topic")
    return uidto