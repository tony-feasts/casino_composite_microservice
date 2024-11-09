# app/models/name_change.py

from pydantic import BaseModel

class NameChange(BaseModel):
    old_username: str
    new_username: str
    password: str
