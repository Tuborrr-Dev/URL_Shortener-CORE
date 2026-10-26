from pydantic import BaseModel, HttpUrl, EmailStr, ConfigDict


# so we create the entire request in pydantic to avoid see finish
class UrlRequest(BaseModel):
    long_url: HttpUrl  # <-- this is to avoid any url giving any issues
    model_config = ConfigDict(extra="ignore")


# we create a model for our users creating a profile
class UserCreate(BaseModel):
    email: EmailStr
    password: str
