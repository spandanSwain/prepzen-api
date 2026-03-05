from fastapi import APIRouter, HTTPException
from configurations import db

domain_router = APIRouter()
domain_collection = db["domain"]

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