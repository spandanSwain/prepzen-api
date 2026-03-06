from fastapi import APIRouter, HTTPException
from configurations import db
from bson import ObjectId
from database.Dashboards.models import UserDashboard

dashboard_router = APIRouter()
users_collection = db["users"]
domain_collection = db["domain"]
interview_collection = db["Interviews"]
quiz_collection = db["quiz"]
path_collection = db["learning_path"]

@dashboard_router.post("/get-content")
def get_dashboard_content(user: UserDashboard):
    try:
        existing_user = users_collection.find_one({"employee_id": str(user.employee_id)})
        if not existing_user: 
            raise HTTPException(status_code=404, detail="User not found")
        
        user_id = existing_user["_id"]
        domain_id = existing_user.get("domain")

        # LEARNING PATH PROGRESS
        user_path = path_collection.find_one({"user_id": user_id})
        path_ratio = "0/0"
        path_percentage = 0
        if user_path:
            assignments = user_path.get("assignments_status", [])
            total_assignments = len(assignments)
            completed_assignments = len([a for a in assignments if a.get("status") == "completed"])
            
            path_ratio = f"{completed_assignments}/{total_assignments}"
            if total_assignments > 0:
                path_percentage = round((completed_assignments / total_assignments) * 100, 2)
        
        # INTERVIEW PROGRESS
        interviews = list(interview_collection.find({"user_id": user_id}))
        total_interviews = len(interviews)
        cummulative_score = 0

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
            cummulative_score += interview_pct
        avg_interview_score = (cummulative_score / total_interviews) if total_interviews > 0 else 0

        # QUIZ SCORES
        quizzes = list(quiz_collection.find({"user_id": user_id}))
        total_quizzes = len(quizzes)
        passed_quizzes = [q for q in quizzes if q.get("status") == "pass"]

        # DOMAIN LEADERBOARD
        leaderboard = []
        user_rank = 0
        if domain_id:
            all_domain_paths = list(path_collection.find({"domain_id": domain_id}).sort("total_xp", -1))

            for index, path in enumerate(all_domain_paths):
                u_info = users_collection.find_one({"_id": path["user_id"]}, {"username": 1})
                if not u_info: continue

                rank_entry = {
                    "rank": index + 1,
                    "name": u_info.get("username", "Anonymous"),
                    "total_xp": path.get("total_xp", 0),
                    "completed_count": len([a for a in path.get("assignments_status", []) if a.get("status") == "completed"]),
                    "is_current_user": path["user_id"] == user_id
                }
                
                leaderboard.append(rank_entry)
                
                # Track current user's rank
                if path["user_id"] == user_id:
                    user_rank = index + 1

        return {
            "metrics": {
                "total_interviews": total_interviews,
                "quiz_ratio": f"{len(passed_quizzes)}/{total_quizzes}",
                "avg_interview_score": f"{avg_interview_score}%",
                "path_ratio": path_ratio,
                "path_percentage": f"{path_percentage}%",
                "user_rank": user_rank
            },
            "leaderboard": leaderboard,
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