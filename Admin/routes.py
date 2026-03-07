from fastapi import APIRouter, HTTPException
from configurations import db
from bson import ObjectId
from datetime import datetime

admin_router = APIRouter()

# Collections
users_collection = db["users"]
domain_collection = db["domain"]
interview_collection = db["Interviews"]
quiz_collection = db["quiz"]
path_collection = db["learning_path"]

@admin_router.get("/dashboard")
def get_admin_dashboard():
    try:
        total_students = users_collection.count_documents({"role": "student"})

        pipeline_completion = [
            {
                "$project": {
                    "all_completed": {
                        "$allElementsTrue": {
                            "$map": {
                                "input": "$assignments_status",
                                "as": "status",
                                "in": { "$eq": ["$$status.status", "completed"] }
                            }
                        }
                    }
                }
            },
            {
                "$group": {
                    "_id": None,
                    "completed_count": { "$sum": { "$cond": ["$all_completed", 1, 0] } },
                    "total_paths": { "$sum": 1 }
                }
            }
        ]
        completion_data = path_collection.aggregate(pipeline_completion).to_list(1)
        
        fully_completed_users = completion_data[0]["completed_count"] if completion_data else 0
        total_paths = completion_data[0]["total_paths"] if completion_data else 1
        completion_percentage = (fully_completed_users / total_paths) * 100 if total_paths > 0 else 0

        total_interviews = interview_collection.count_documents({})

        high_performers = quiz_collection.count_documents({"score": {"$gt": "75"}})

        pipeline_domains = [
            {
                "$group": {
                    "_id": "$domain",
                    "total_users": { "$sum": 1 }
                }
            },
            {
                "$lookup": {
                    "from": "domain",
                    "localField": "_id",
                    "foreignField": "_id",
                    "as": "domain_info"
                }
            },
            { "$unwind": "$domain_info" },
            {
                "$project": {
                    "_id": 1,
                    "domain_name": "$domain_info.domain_name",
                    "count": "$total_users"
                }
            }
        ]
        domain_distribution = users_collection.aggregate(pipeline_domains).to_list(None)

        pipeline_bad_students = [
            { "$match": { "status": "fail" } },
            { "$sort": { "score": 1 } },
            { "$limit": 2 },
            {
                "$lookup": {
                    "from": "users",
                    "localField": "user_id",
                    "foreignField": "_id",
                    "as": "user_info"
                }
            },
            { "$unwind": "$user_info" },
            {
                "$project": {
                    "_id": 1,
                    "user_id": 1,
                    "username": "$user_info.username",
                    "employee_id": 1,
                    "score": 1,
                    "status": 1,
                    "updatedAt": 1
                }
            }
        ]

        bad_students_cursor = quiz_collection.aggregate(pipeline_bad_students)
        bad_students = bad_students_cursor.to_list(None)

        response_data = {
            "total_students": total_students,
            "completion_stats": {
                "percentage": round(completion_percentage, 2),
                "fully_completed_count": fully_completed_users
            },
            "total_interviews": total_interviews,
            "high_performers_count": high_performers,
            "domain_distribution": domain_distribution,
            "underperforming_students": bad_students
        }
        return serialize_mongo(response_data)
    except Exception as ex:
        raise HTTPException(
            status_code=500,
            detail=f"Error in get_admin_dashboard: {ex}"
        )

@admin_router.get("/domain-users/{domain_id}")
def get_users_by_domain(domain_id: str):
    try:
        users = users_collection.find({"domain": ObjectId(domain_id)}).to_list(None)
        for user in users:
            user["_id"] = str(user["_id"])
            user["domain"] = str(user["domain"])

            path = path_collection.find_one({"user_id": ObjectId(user["_id"])})
            if path and "assignments_status" in path:
                assignments = path["assignments_status"]
                total_assignments = len(assignments)
                
                completed_count = sum(1 for a in assignments if a.get("status") == "completed")
                
                if total_assignments > 0:
                    user["path_progress"] = int((completed_count / total_assignments) * 100)
                else: user["path_progress"] = 0
            else:
                user["path_progress"] = 0
        return users
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))
    
def serialize_mongo(data):
    if isinstance(data, list): return [serialize_mongo(item) for item in data]
    if isinstance(data, dict):
        return {k: (str(v) if isinstance(v, ObjectId) else serialize_mongo(v)) for k, v in data.items()}
    return data