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

        total_score = sum(rubrics.values())
        percentage = (total_score / 500) * 100

        if percentage < 50: overall_status = "Bad"
        elif 50 <= percentage < 75: overall_status = "Average"
        elif 75 <= percentage < 90: overall_status = "Good"
        else: overall_status = "Outstanding"

        detailed_feedback = evaluation.get("detailed_feedback")
        areas_for_improvement = evaluation.get("areas_for_improvement")
        weaknesses = evaluation.get("weaknesses", [])


        interview_id = ObjectId(data.interview_id)
        db["Interviews"].update_one(
            {"_id": interview_id},
            {
                "$set": {
                    "metrics": rubrics,
                    "finalRemark": detailed_feedback,
                    "overall_feedback": overall_status,
                    "areas_for_improvement": areas_for_improvement,
                    "weaknesses": weaknesses,
                    "conversation": data.transcribe,
                    "completedAt": datetime.utcnow()
                }
            }
        )

        # UPDATE LEARNING PATH
        interview_doc = db["Interviews"].find_one({"_id": interview_id})
        user_id = interview_doc.get("user_id")
        learning_path = db["learning_path"].find_one({"user_id": ObjectId(user_id)})
        
        if learning_path:
            current_lv = learning_path.get("current_level", 1)
            assignment_index = current_lv - 1

            existing_assignments = learning_path.get("assignments_status", [])
            previous_score = 0
            if 0 <= assignment_index < len(existing_assignments):
                previous_score = existing_assignments[assignment_index].get("score", 0)

            # update_query = {
            #     f"assignments_status.{assignment_index}.score": percentage,
            #     f"assignments_status.{assignment_index}.completed_at": datetime.utcnow(),
            #     f"assignments_status.{assignment_index}.weakness": weaknesses
            # }

            update_query = {}

            if percentage > previous_score:
                update_query[f"assignments_status.{assignment_index}.score"] = percentage
                update_query[f"assignments_status.{assignment_index}.weakness"] = weaknesses
                update_query[f"assignments_status.{assignment_index}.completed_at"] = datetime.utcnow()

            if percentage >= 75:
                update_query.update({
                    f"assignments_status.{assignment_index}.status": "completed",
                    "current_level": current_lv + 1,
                    "overall_progress": min(learning_path.get("overall_progress", 0) + 10, 100)
                })
                xp_gain = percentage * 10
                db["learning_path"].update_one(
                    {"user_id": user_id},
                    {
                        "$set": update_query,
                        "$inc": {"total_xp": xp_gain}
                    }
                )
            else:
                # update_query.update({f"assignments_status.{current_lv - 1}.status": "failed"})
                current_status = existing_assignments[assignment_index].get("status") if assignment_index < len(existing_assignments) else None
                if current_status != "completed":
                    update_query[f"assignments_status.{assignment_index}.status"] = "failed"
                
                if update_query:
                    db["learning_path"].update_one(
                        {"user_id": user_id},
                        {"$set": update_query}
                    )

        return_response = {
            "metrics": rubrics,
            "percentage": round(percentage, 2),
            "overall_feedback": overall_status,
            "finalRemark": detailed_feedback,
            "areas_for_improvement": areas_for_improvement,
            "weaknesses": weaknesses,
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