from fastapi import APIRouter, HTTPException
from configurations import db
from database.Domains.models import UserDomain
from bson import ObjectId

domain_router = APIRouter()
domain_collection = db["domain"]
users_collection = db["users"]
path_collection = db["learning_path"]

@domain_router.get("/get-domain")
def get_domains():
    try:
        raw_domains = domain_collection.find()
        list_domains = list(raw_domains)
        domains = []

        for domain in list_domains:
            temp = {}
            temp["domain_id"] = str(domain["_id"])
            temp["domain_name"] = domain["domain_name"]
            domains.append(temp)

        return {
            "status_code": 200,
            "domains": domains
        }
    except HTTPException as hex:
        raise hex
    except Exception as ex:
        raise HTTPException(
            status_code=500,
            detail=f"Some exception occured in Domain/routes.py/get_domains() /domain/get-domain :: {ex}"
        )


@domain_router.post("/update-user-domain")
def update_users_domain(user: UserDomain):
    try:
        existing_user = users_collection.find_one({"employee_id": str(user.employee_id)})
        if not existing_user: raise HTTPException(status_code=404, detail="User not found")

        domain_id = ObjectId(user.domain_id)
        result = users_collection.update_one(
            {"_id": existing_user["_id"]},
            {"$set": {"domain": domain_id}}
        )

        # CREATE LEARNING PATH COLLECTION AND ADD THE USER
        domain_data = domain_collection.find_one({"_id": domain_id})
        if not domain_data: raise HTTPException(status_code=404, detail="Domain not found")
        
        assignments_status = []
        for assignment in domain_data.get("assignments", []):
            assignments_status.append({
                "assignment_id": str(assignment["id"]),
                "title": assignment["title"],
                "workload_hours": assignment["workload_hours"],
                "curriculum": assignment["curriculum"],
                "links": assignment["links"],
                "status": "pending",
                "score": 0,
                "completed_at": None,
                "weakness": []
            })

        initial_skills = {}
        
        path_dict = {
            "user_id": existing_user["_id"],
            "domain_id": domain_id,
            "overall_progress": 0.0,
            "current_level": 1,
            "total_xp": 0,
            "assignments_status": assignments_status,
            "skill_mastery": initial_skills,
        }

        path_collection.update_one(
            {"user_id": existing_user["_id"]},
            {"$set": path_dict},
            upsert=True
        )

        if result.modified_count == 0:
            return {
                "status_code": 200,
                "message": "No changes made (domain may already be set)"
            }

        return {
            "status_code": 200,
            "message": "User domain updated successfully"
        }
    except HTTPException as hex:
        raise hex
    except Exception as ex:
        raise HTTPException(
            status_code=500,
            detail=f"Some exception occured in Domain/routes.py/update_users_domain() /domain/update-user-domain :: {ex}"
        )