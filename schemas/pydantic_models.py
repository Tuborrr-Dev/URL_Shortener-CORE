from pydantic import BaseModel, HttpUrl, EmailStr


# so we create the entire request in pydantic to avoid see finish
class UrlRequest(BaseModel):
    username: str
    long_url: HttpUrl  # <-- this is to avoid any url giving any issues


# we create a model for our users creating a profile
class UserCreate(BaseModel):
    email: EmailStr
    password: str
