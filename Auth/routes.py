from fastapi import APIRouter, HTTPException, status
from configurations import db
from Auth.hashing import hash_password, verify_password
from database.Users.models import Users, LoginUsers
from Auth.jwt_handler import create_access_token
from bson import ObjectId

auth_router = APIRouter()
users_collection = db["users"]
domain_collection = db["domain"]

@auth_router.post("/signup")
def register_user(user: Users):
    try:
        user_dict = user.model_dump()
        existing = users_collection.find_one({"employee_id": str(user.employee_id)})

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Employee ID already exists"
            )
        
        user_dict["password"] = hash_password(str(user.password))

        resp = users_collection.insert_one(user_dict)
        token = create_access_token(user.employee_id)

        user_data = {
            "_id": str(resp.inserted_id),
            "username": user.username,
            "employee_id": user.employee_id,
            "email": user.email,
            "role": user.role,
            "user_id": str(user["_id"])
        }

        return {
            "status_code": 200,
            "access_token": token,
            "token_type": "bearer",
            "user": user_data
        }

    except HTTPException as hex:
        raise hex
    except Exception as ex:
        raise HTTPException(
            status_code=500,
            detail=f"Some exception occured in Auth/routes.py/register_user() /auth/signup :: {ex}"
        )
    

@auth_router.post("/login")
def login_user(user: LoginUsers):
    try:
        employee_id = int(user.employee_id)
        employee_password = user.password
        user = users_collection.find_one({"employee_id": str(user.employee_id)})
        domain_name = ""

        if user and "domain" in user:
            domain_id = user["domain"]
            domain_doc = domain_collection.find_one({"_id": domain_id})

            if domain_doc:
                domain_name = domain_doc.get("domain_name")

        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid employee_id"
            )
        
        if not verify_password(employee_password, user["password"]):
            raise HTTPException(
                status_code=401,
                detail="Invalid password"
            )
        
        token = create_access_token(employee_id)
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "employee_id": user["employee_id"],
                "username": user["username"],
                "email": user["email"],
                "role": user["role"],
                "domain": domain_name,
                "user_id": str(user["_id"])
            }
        }

    except HTTPException as hex:
        raise hex
    except Exception as ex:
        raise HTTPException(
            status_code=500,
            detail=f"Some exception occured in Auth/routes.py/login_user() /auth/login :: {ex}"
        )