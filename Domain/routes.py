from fastapi import APIRouter, HTTPException
from configurations import db
from database.Domains.models import UserDomain
from bson import ObjectId

domain_router = APIRouter()
domain_collection = db["domain"]
users_collection = db["users"]

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
            temp["description"] = domain["description"]
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