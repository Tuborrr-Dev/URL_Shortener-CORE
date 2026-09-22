# the below imports are the authentication part of our application
import random
import string
from fastapi.security import OAuth2PasswordRequestForm
from models.models import User
from services.auth import get_password_hash, verify_password, create_access_token
from sqlalchemy.orm import Session
from models.models import User


def register_authentication(email: str, db: Session):
    # first we Check if email exists
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
