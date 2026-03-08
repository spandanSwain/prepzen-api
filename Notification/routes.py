from fastapi import APIRouter, HTTPException
from configurations import db
from bson import ObjectId
from datetime import datetime
from database.Notifications.models import NotificationToAdmin

notification_router = APIRouter()

users_collection = db["users"]
domain_collection = db["domain"]
interview_collection = db["Interviews"]
quiz_collection = db["quiz"]
path_collection = db["learning_path"]
notification_collection = db["notification"]

@notification_router.post("/send-notification")
def send_notification(data: NotificationToAdmin):
    try:
        user_doc = users_collection.find_one({"employee_id": data.employee_id})
        if not user_doc: raise HTTPException(status_code=401, detail="Invalid employee_id")

        admin_doc = users_collection.find_one({"employee_id": data.admin_id})
        if not admin_doc: raise HTTPException(status_code=401, detail="Invalid admin_id")

        user_id = user_doc.get("_id")
        admin = admin_doc.get("_id")

        notification_doc = {
            "student": user_id,
            "admin": admin,
            "employee_id": data.employee_id,
            "admin_id": data.admin_id,
            "message": data.message,
            "type": data.type,
            "is_read": False,
            "created_at": datetime.utcnow()
        }
        result = notification_collection.insert_one(notification_doc)
        
        return {
            "status": "success", 
            "message": "Notification sent", 
            "id": str(result.inserted_id)
        }
    except HTTPException as hex:
        raise hex
    except Exception as ex:
        raise HTTPException(
            status_code=500,
            detail=f"Some exception occured in Notification/routes.py/send_notification() /notification/send-notification :: {ex}"
        )

  
@notification_router.patch("/mark-read/{notification_id}")
def mark_read(notification_id: str):
    try:
        result = notification_collection.update_one(
            {"_id": ObjectId(notification_id)},
            {"$set": {"is_read": True}}
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Notification not found")

        return {"status": "success", "message": "Notification marked as read"}
    except HTTPException as hex:
        raise hex
    except Exception as ex:
        raise HTTPException(
            status_code=500,
            detail=f"Some exception occured in Notification/routes.py/mark_read() /notification/mark-read :: {ex}"
        )
    

@notification_router.get("/get-notifications/{employee_id}")
def get_notifications(employee_id: str):
    try:
        query = {
            "employee_id": employee_id,
            "is_read": False
        }

        notifications = list(notification_collection.find(query).sort("created_at", -1))

        for n in notifications:
            n["_id"] = str(n["_id"])

            if "student" in n: n["student"] = str(n["student"])
            if "admin" in n: n["admin"] = str(n["admin"])

            if isinstance(n.get("created_at"), datetime):
                n["created_at"] = n["created_at"].isoformat()

        return {
            "status": "success", 
            "count": len(notifications),
            "notifications": notifications
        }
    except HTTPException as hex:
        raise hex
    except Exception as ex:
        raise HTTPException(
            status_code=500,
            detail=f"Some exception occured in Notification/routes.py/get_notifications() /notification/get-notifications :: {ex}"
        )