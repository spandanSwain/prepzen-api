from fastapi import APIRouter, HTTPException
from configurations import db
from bson import ObjectId
from database.Dashboards.models import UserDashboard

dashboard_router = APIRouter()
users_collection = db["users"]
domain_collection = db["domain"]
interview_collection = db["Interviews"]
quiz_collection = db["quiz"]

@dashboard_router.post("/get-content")
def get_dashboard_content(user: UserDashboard):
    try:
        existing_user = users_collection.find_one({"employee_id": str(user.employee_id)})
        if not existing_user: 
            raise HTTPException(status_code=404, detail="User not found")
        
        user_id = existing_user["_id"]
        
        interviews = list(interview_collection.find({"user_id": user_id}))
        total_interviews = len(interviews)

        cumulative_score = 0
        topic_performance = {}

        for i in interviews:
            m = i.get("metrics", {})
            interview_total = (
                m.get("communication_skills", 0) +
                m.get("technical_knowledge", 0) +
                m.get("problem_solving", 0) +
                m.get("cultural_role_fit", 0) +
                m.get("confidence_clarity", 0)
            )
            
            interview_pct = (interview_total / 500) * 100
            cumulative_score += interview_pct

        avg_interview_score = (cumulative_score / total_interviews) if total_interviews > 0 else 0

        quizzes = list(quiz_collection.find({"user_id": user_id}))
        total_quizzes = len(quizzes)
        passed_quizzes = [q for q in quizzes if q.get("status") == "pass"]

        return {
            "metrics": {
                "total_interviews": total_interviews,
                "quiz_ratio": f"{len(passed_quizzes)}/{total_quizzes}",
                "avg_interview_score": f"{avg_interview_score}%",
            },
            "quiz_overview": serialize_list(quizzes),
        }

    except HTTPException as hex:
        raise hex
    except Exception as ex:
        raise HTTPException(
            status_code=500,
            detail=f"Some exception occured in Dashboard/routes.py/get_dashboard_content() /dashboard/get-content :: {ex}"
        )
    
def serialize_list(items):
    for item in items:
        item["_id"] = str(item["_id"])
        if "user_id" in item: item["user_id"] = str(item["user_id"])
    return items