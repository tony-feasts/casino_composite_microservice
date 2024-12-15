# app/models/game_history.py

from pydantic import BaseModel
from typing import Optional, List
from app.models.result_enum import ResultEnum

class GameHistory(BaseModel):
    username: str
    result: ResultEnum
