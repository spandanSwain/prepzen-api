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
    except HTTPException as hex:
        raise hex
    except Exception as ex:
        raise HTTPException(
            status_code=500,
            detail=f"Some exception occured in Admin/routes.py/get_admin_dashboard() /admin/dashboard :: {ex}"
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
    except HTTPException as hex:
        raise hex
    except Exception as ex:
        raise HTTPException(
            status_code=500,
            detail=f"Some exception occured in Admin/routes.py/get_users_by_domain() /admin/domain-users :: {ex}"
        )
    
def serialize_mongo(data):
    if isinstance(data, list): return [serialize_mongo(item) for item in data]
    if isinstance(data, dict):
        return {k: (str(v) if isinstance(v, ObjectId) else serialize_mongo(v)) for k, v in data.items()}
    return data


@admin_router.get("/all-students")
def get_all_students():
    try:
        students = list(users_collection.find({"role": "student"}))
        
        student_registry = []

        for student in students:
            student_id = student["_id"]
            
            path = path_collection.find_one({"user_id": student_id})
            domain = domain_collection.find_one({"_id": student["domain"]})
            
            progress = 0
            if path and "assignments_status" in path:
                assignments = path["assignments_status"]
                total = len(assignments)
                completed = sum(1 for a in assignments if a.get("status") == "completed")
                
                if total > 0:
                    progress = int((completed / total) * 100)

            student_registry.append({
                "_id": str(student_id),
                "domain": domain["domain_name"],
                "username": student.get("username", "Unknown"),
                "employee_id": student.get("employee_id", "N/A"),
                "role": student.get("role"),
                "path_progress": progress,
                "createdAt": student.get("createdAt").isoformat() if isinstance(student.get("createdAt"), datetime) else student.get("createdAt")
            })

        return student_registry

    except HTTPException as hex:
        raise hex
    except Exception as ex:
        raise HTTPException(
            status_code=500,
            detail=f"Some exception occured in Admin/routes.py/get_all_students() /admin/all-students :: {ex}"
        )
    

@admin_router.get("/student-details/{employee_id}")
def get_student_detailed_report(employee_id: str):
    try:
        user = users_collection.find_one({"employee_id": employee_id})
        if not user: 
            raise HTTPException(status_code=404, detail="Student not found")
        
        user_id = user["_id"]
        username = user.get("username", "Candidate")
        domain_id = user.get("domain")

        domain_doc = domain_collection.find_one({"_id": domain_id})
        domain_name = domain_doc["domain_name"] if domain_doc else "Unknown Domain"

        path = path_collection.find_one({"user_id": user_id})
        assignments = path.get("assignments_status", []) if path else []
        
        total_topics = len(assignments)
        mastered_topics = sum(1 for a in assignments if a.get("status") == "completed")
        completion_pct = int((mastered_topics / total_topics) * 100) if total_topics > 0 else 0

        interviews = list(interview_collection.find({"user_id": user_id}).sort("completedAt", -1))
        
        performance_log = []
        for i in interviews:
            m = i.get("metrics", {})
            rubrics = ["communication_skills", "technical_knowledge", "problem_solving", "cultural_role_fit", "confidence_clarity"]
            total_score = sum(m.get(k, 0) for k in rubrics)
            calc_percentage = (total_score / 500) * 100
            
            performance_log.append({
                "topic": i.get("topic", "General Interview"),
                "date": i.get("completedAt").strftime("%b %d, %Y") if i.get("completedAt") else "N/A",
                "score": f"{int(calc_percentage)}%",
                "status": "QUALIFIED" if calc_percentage >= 75 else "RETAKE"
            })

        all_paths_in_domain = list(path_collection.find({"domain_id": domain_id}).sort("total_xp", -1))
        rank_value = next((f"#{idx + 1}" for idx, p in enumerate(all_paths_in_domain) if p.get("user_id") == user_id), "N/A")

        weakness_map = {}
        for interview in interviews:
            for w in interview.get("weaknesses", []):
                weakness_map[w] = weakness_map.get(w, 0) + 1
        
        sorted_weaknesses = sorted(weakness_map.items(), key=lambda x: x[1], reverse=True)
        top_weaknesses_list = [w[0] for w in sorted_weaknesses[:4]]

        if not sorted_weaknesses:
            ai_summary = f"{username} has a clean record with no significant weaknesses identified in recent sessions."
        else:
            primary_issue = sorted_weaknesses[0][0]
            occurrence_count = sorted_weaknesses[0][1]
            ai_summary = (
                f"{username} shows recurring difficulty with {primary_issue}, appearing in {occurrence_count} evaluation(s). "
                f"They currently struggle with {', '.join(top_weaknesses_list[1:3]) if len(top_weaknesses_list) > 1 else 'foundational concepts'}. "
                f"Recommendation: Prioritize {primary_issue} modules to improve their domain standing."
            )

        proficiency = {
            "Logic & Problem Solving": 0,
            "Technical Knowledge": 0,
            "Communication": 0,
            "Confidence": 0
        }
        
        if interviews:
            count = len(interviews)
            for i in interviews:
                m = i.get("metrics", {})
                proficiency["Logic & Problem Solving"] += m.get("problem_solving", 0)
                proficiency["Technical Knowledge"] += m.get("technical_knowledge", 0)
                proficiency["Communication"] += m.get("communication_skills", 0)
                proficiency["Confidence"] += m.get("confidence_clarity", 0)
            
            for key in proficiency:
                proficiency[key] = int(proficiency[key] / count)

        return serialize_mongo({
            "header": {
                "username": username,
                "employee_id": employee_id,
                "domain": domain_name,
                "total_interviews": len(interviews),
                "rank": rank_value
            },
            "curriculum": {
                "total_completion": completion_pct,
                "topics_mastered": f"{mastered_topics} / {total_topics}",
                "avg_interview_score": f"{int(sum(float(x['score'].strip('%')) for x in performance_log)/len(performance_log)) if performance_log else 0}%"
            },
            "ai_evaluation": {
                "weaknesses": top_weaknesses_list,
                "summary": ai_summary
            },
            "performance_log": performance_log,
            "skill_proficiency": proficiency
        })

    except HTTPException as hex:
        raise hex
    except Exception as ex:
        raise HTTPException(
            status_code=500,
            detail=f"Error in Admin/routes.py/get_student_detailed_report: {ex}"
        )