# app/models/result_enum.py

from enum import Enum

class ResultEnum(str, Enum):
    win = 'win'
    loss = 'loss'
    push = 'push'
