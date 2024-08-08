from typing import Optional

from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.orm import Session
from starlette import status

from app import schemas, models, utils, oauth2
from app.database import get_db

router = APIRouter(tags=["Authentication"])


@router.post("/login")
def login(user_credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    registered_user: Optional[models.User] = (
        db.query(models.User)
        .filter(models.User.email == user_credentials.email)
        .first()
    )

    if not registered_user or not utils.verify_password(
        user_credentials.password, registered_user.password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong Credentials"
        )

    access_token = oauth2.create_access_token(data={"user_id": registered_user.id})
    return {"access_token": access_token, "token_type": "bearer"}
