from fastapi import APIRouter, HTTPException
from configurations import db
from datetime import datetime, timezone
from database.Reports.models import UserReport
from bson import ObjectId

report_router = APIRouter()
users_collection = db["users"]
path_collection = db["learning_path"]

@report_router.post("/get-report")
def get_report(user: UserReport):
    try:
        user_doc = users_collection.find_one({"employee_id": str(user.employee_id)})
        if not user_doc: raise HTTPException(status_code=404, detail="User not found")

        path_doc = path_collection.find_one({"user_id": ObjectId(user_doc["_id"])})
        if not path_doc: raise HTTPException(status_code=404, detail="Learning path not found")

        completed_assignments = []
        for assignment in path_doc.get("assignments_status", []):
            if assignment.get("status") == "completed":
                raw_date = assignment.get("completed_at")
                
                formatted_date = "N/A" 
                if raw_date:
                    if isinstance(raw_date, datetime):
                        formatted_date = raw_date.strftime("%Y-%m-%d")
                    elif isinstance(raw_date, str):
                        formatted_date = raw_date[:10]

                completed_assignments.append({
                    "title": assignment["title"],
                    "score": assignment["score"],
                    "completed_date": formatted_date
                })

        return {
            "status_code": 200,
            "completed_count": len(completed_assignments),
            "reports": completed_assignments
        }
    except HTTPException as hex:
        raise hex
    except Exception as ex:
        raise HTTPException(
            status_code=500,
            detail=f"Some exception occured in Reports/routes.py/get_report() /report/get-report :: {ex}"
        )