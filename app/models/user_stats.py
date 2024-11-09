# app/models/user_stats.py

from pydantic import BaseModel

class UserStats(BaseModel):
    username: str
    wins: int
    losses: int
