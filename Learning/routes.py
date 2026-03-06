from fastapi import APIRouter, HTTPException
from configurations import db
from database.Learnings.models import LearningUser
from bson import ObjectId

learning_router = APIRouter()
domain_collection = db["domain"]
users_collection = db["users"]
path_collection = db["learning_path"]

@learning_router.post("/get-path")
def get_learning_path(user: LearningUser):
    try:
        user_data = users_collection.find_one({"employee_id": str(user.employee_id)})
        if not user_data: raise HTTPException(status_code=404, detail="User not found")

        user_path = path_collection.find_one({"user_id": user_data["_id"]})
        if not user_path: raise HTTPException(status_code=404, detail="Learning path not found for this user")

        domain_template = domain_collection.find_one({"_id": user_path["domain_id"]})
        if not domain_template: raise HTTPException(status_code=404, detail="Domain content not found")

        domain_assignments = {str(a["id"]): a for a in domain_template.get("assignments", [])}

        enriched_assignments = []
        determined_current_level = "1"
        found_next_pending = False

        total_xp = 0
        completed_count = 0
        total_assignments = len(user_path.get("assignments_status", []))

        for status_item in user_path.get("assignments_status", []):
            assign_id = str(status_item["assignment_id"])
            template = domain_assignments.get(assign_id, {})
            current_status = status_item.get("status", "pending")
            display_status = current_status
            
            if current_status == "completed":
                total_xp += (status_item.get("score", 0) * 10)
                completed_count += 1
            elif not found_next_pending:
                display_status = "pending"
                determined_current_level = assign_id
                found_next_pending = True
            else:
                display_status = "disabled"

            enriched_item = {
                "assignment_id": assign_id,
                "title": template.get("title", "Unknown Topic"),
                "workload_hours": template.get("workload_hours", 0),
                "curriculum": template.get("curriculum", ""),
                "links": template.get("links", []),
                "status": display_status,
                "score": status_item.get("score", 0),
                "completed_at": status_item.get("completed_at"),
                "weakness": status_item.get("weakness", [])
            }
            enriched_assignments.append(enriched_item)
        
        overall_progress = (completed_count / total_assignments * 100) if total_assignments > 0 else 0
        
        response = {
            "user_id": str(user_data["_id"]),
            "username": user_data.get("username"),
            "domain_id": str(user_path["domain_id"]),
            "domain_name": domain_template.get("domain_name"),
            "overall_progress": overall_progress,
            "current_level": determined_current_level,
            "total_xp": total_xp,
            "assignments_status": enriched_assignments,
            "skill_mastery": user_path.get("skill_mastery", {}),
        }

        return {
            "status_code": 200,
            "response": response
        }
    
    except HTTPException as hex:
        raise hex
    except Exception as ex:
        raise HTTPException(
            status_code=500,
            detail=f"Some exception occured in Learning/routes.py/get_learning_path() /learning/get-path :: {ex}"
        )