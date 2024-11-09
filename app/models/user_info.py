# app/models/user_info.py

from pydantic import BaseModel

class UserInfo(BaseModel):
    username: str
    password: str
