from fastapi import APIRouter, HTTPException
from configurations import db
from datetime import datetime
from database.Interviews.models import InterviewComplete
from bson import ObjectId

conclusion_router = APIRouter()
interview_collection = db["Interviews"]

@conclusion_router.post("/complete")
def complete_interview(data: InterviewComplete):
    try:
        interview_id = ObjectId(data.interview_id)
        user_id = ObjectId(data.user_id)

        db["Interviews"].update_one(
            {"_id": interview_id},
            {
                "$set": {
                    "response": data.response,
                    "rubrics": {
                        "communication": data.communication,
                        "technicalKnowledge": data.technicalKnowledge,
                        "problemSolving": data.problemSolving,
                        "culturalFit": data.culturalFit,
                        "confidence": data.confidence
                    },
                    "finalRemark": data.finalRemark,
                    "completedAt": datetime.utcnow()
                }
            }
        )

        db["users"].update_one(
            {"_id": user_id},
            {"$push": {"interviews_attended": interview_id}}
        )

        return {"message": "Interview completed successfully"}

    except HTTPException as hex:
        raise hex
    except Exception as ex:
        return HTTPException(
            status_code=500,
            detail=f"Some exception occured in Conclusion/routes.py/complete_interview() /conclude/complete :: {ex}"
        )