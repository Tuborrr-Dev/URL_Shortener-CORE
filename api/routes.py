from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import get_db
from schemas.pydantic_models import UrlRequest, UserCreate
from crud.url_processing import shorten, elongate
from crud.authentication import register_authentication, authenticate
from crud.url_stats import count_em_up, count_em_hr, daily_counts
import hashlib
from services.auth import get_current_user, create_access_token
from models.models import User

router = APIRouter()


@router.post("/register")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    username = register_authentication(user.email, user.password, db)
    if username == None:  # <-- the email already exists
        raise HTTPException(status_code=400, detail="Email already registered")
    else:
        return {"message": "User created successfully", "username": username}


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    # Pass form_data.username (which holds the email) to authenticate
    user = authenticate(form_data.username, form_data.password, db)
    if user == None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate an actual signed JWT token containing user.id
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


# table to store endpoint and it's click counts in background updated every hour


@router.post("/shorten_url")  # <-- this is the post method to our API to save the URL
def shorten_url(
    payload: UrlRequest,
    current_user: User = Depends(get_current_user),  # <-- Secure JWT dependency
    db: Session = Depends(get_db),
):  # <-- tells FastAPI: Before running any CRUD, go execute get_db(), grab whatever it yields, and plug it into the db variable."
    short_cd = shorten(user_id=current_user.id, long_url=str(payload.long_url), db=db)
    if short_cd:
        return {"short_url": short_cd}
    else:
        raise HTTPException(status_code=400, detail="Link canont be saved")


@router.get("/{short_code}")
def generate_url(short_code: str, request: Request, db: Session = Depends(get_db)):
    # gets where the user came from (e.g., "https://twitter.com/")
    referrer_url = request.headers.get("referer")

    # the raw IP (or fallback if behind a proxy
    raw_ip_header = request.headers.get("x-forwarded-for")
    if raw_ip_header:
        raw_ip = raw_ip_header.split(",")[
            0
        ].strip()  # Get the true client IP because a list of IP's is returned
    else:
        raw_ip = request.client.host if request.client else "unknown"
    # we then hash with SHA-256
    ip_hash = hashlib.sha256(raw_ip.encode("utf-8")).hexdigest()
    # <-- first off before cache lets try to get our code from our CRUD
    long_cd = elongate(short_code, referrer_url, ip_hash, db)
    # now long_cd contains the full url
    if not long_cd:
        raise HTTPException(status_code=404, detail="Link not found")
    """Browsers cache 301 redirects aggressively in local storage. 
    Once a user clicks the shortened link for the first time, 
    their browser saves the destination URL locally. 
    On every future click, the browser bypasses the API server completely and goes straight to the target URL. 
    Result: inaccurate click stats"""
    return RedirectResponse(
        url=long_cd, status_code=307
    )  # <-- ensures our click function is active and still redirects the browser insteda of json


# GET /links/{code}/stats <-- return click count of all time and clicks per day (default 24hrs)
@router.get("/links/{short_code}/stats")
def generate_url_stats(
    short_code: str, limit_hrs: int = 24, db: Session = Depends(get_db)
):
    # in the function below if we get none we know the link is non-existent
    result = count_em_up(short_code, db)  # <-- this is the total count of clicks
    if result == None:
        raise HTTPException(status_code=404, detail="Link not found")
    # we dont need to bother about the below returning none since if it would we would already have it above
    result_hr = count_em_hr(
        short_code, limit_hrs, db
    )  # if no parameter query this returns from the past 24hrs
    daily_stats = daily_counts(short_code, db)  # dict of every click stats daily

    return {
        "hour clicks": result_hr,
        "daily stats": daily_stats,
        "All time clicks": result,
    }
