# the below imports are the authentication part of our application
import random
import string
from fastapi.security import OAuth2PasswordRequestForm
from models.models import User
from services.auth import get_password_hash, verify_password, create_access_token
from sqlalchemy.orm import Session
from sqlalchemy import or_
from models.models import User


def register_authentication(email: str, password: str, db: Session):
    # first we Check if email exists
    if db.query(User).filter(User.email == email).first():
        return None
    # now we know it is unique we go ahead to generate username
    base_name = email.split("@")[0]
    random_suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
    username = f"{base_name}_{random_suffix}"
    new_user = User(
        email=email, username=username, hashed_password=get_password_hash(password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return username


# in the case where the user is not verified we give zero access
def authenticate(username: str, password, db: Session):
    user = (
        db.query(User)
        .filter(or_(User.email == username, User.username == username))
        .first()
    )
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user
