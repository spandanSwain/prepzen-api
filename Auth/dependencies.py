from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from Auth.jwt_handler import decode_access_token
from configurations import db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/Auth/login")
users_collection = db["users"]


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        employee_id = decode_access_token(token)
        if employee_id is None:
            return HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

        user = users_collection.find_one({"employee_id": employee_id})
        if user is None:
            return HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        return user
    except Exception as ex:
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Some exception occured in depedencies.py/get_current_user() => {ex}"
        )

    