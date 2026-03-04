from fastapi import APIRouter, HTTPException
from configurations import db
from datetime import datetime
from database.Interviews.models import InterviewComplete
from bson import ObjectId
from AI_Utility.genai import evaluateUserBasedOnTranscribe

conclusion_router = APIRouter()
interview_collection = db["Interviews"]

@conclusion_router.post("/metrics")
def complete_interview(data: InterviewComplete):
    try:
        # EVALUATE THE USER HERE
        evaluation = evaluateUserBasedOnTranscribe(data)
        if "error" in evaluation: raise HTTPException(status_code=500, detail=evaluation["details"])
        
        rubrics = {
            "communication_skills": evaluation.get("communication_skills"),
            "technical_knowledge": evaluation.get("technical_knowledge"),
            "problem_solving": evaluation.get("problem_solving"),
            "cultural_role_fit": evaluation.get("cultural_role_fit"),
            "confidence_clarity": evaluation.get("confidence_clarity"),
        }

        detailed_feedback = evaluation.get("detailed_feedback")
        areas_for_improvement = evaluation.get("areas_for_improvement")


        # THIS PART UPDATES THE INTERVIEW SECTION WITH METRICS AND CHAT BETWEEN USER AND AI
        interview_id = ObjectId(data.interview_id)
        db["Interviews"].update_one(
            {"_id": interview_id},
            {
                "$set": {
                    "metrics": rubrics,
                    "finalRemark": detailed_feedback,
                    "areas_for_improvement": areas_for_improvement,
                    "conversation": data.transcribe,
                    "completedAt": datetime.utcnow()
                }
            }
        )

        return_response = {
            "metrics": rubrics,
            "finalRemark": detailed_feedback,
            "areas_for_improvement": areas_for_improvement,
            "conversation": data.transcribe
        }

        return {"response": return_response}

    except HTTPException as hex:
        raise hex
    except Exception as ex:
        raise HTTPException(
            status_code=500,
            detail=f"Some exception occured in Feedback/routes.py/complete_interview() /feedback/metrics :: {ex}"
        )