from fastapi import APIRouter, HTTPException
from configurations import db
from datetime import datetime
from database.Interviews.models import Interviews
from AI_Utility.genai import getDataFromGemini

response_router = APIRouter()
interview_collection = db["Interviews"]

@response_router.post("/start-interview")
def start_interview(data: Interviews):
    try:
        # STRUCTURE WILL CHANGE
        interview_doc = {
            "domain": data.domain,
            "proficiency": data.proficiency,
            "topic": data.topic,
            "createdAt": datetime.utcnow(),
            "response": None
        }

        result = interview_collection.insert_one(interview_doc)
        interview_id = str(result.inserted_id)

        ai_response = getDataFromGemini(data.domain, data.topic, data.proficiency)

        # ASK HARIOM - if we need to add this response in mongo
        # interview_collection.update_one(
        #     {"_id": result.inserted_id},
        #     {"$set": {"aiResponse": ai_response}}
        # )

        return {
            "interview_id": interview_id,
            "response": ai_response
        }

    except HTTPException as hex:
        raise hex
    except Exception as ex:
        return HTTPException(
            status_code=500,
            detail=f"Some exception occured in Response/routes.py/start_intervieww() /response/start-interview :: {ex}"
        )

"""
hariom will send a json/ response having the domain, proficiency, topic
set these in mongo db -> then call ai (ajay function) -> send ajay's response to hariom
POST REQUEST
"""
