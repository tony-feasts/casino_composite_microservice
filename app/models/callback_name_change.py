# app/models/callback_name_change.py

from pydantic import BaseModel

class CallbackNameChange(BaseModel):
    old_username: str
    new_username: str
    callback_url: str
