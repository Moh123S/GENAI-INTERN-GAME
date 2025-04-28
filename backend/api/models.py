from pydantic import BaseModel
from typing import Literal

class GuessInput(BaseModel):
    guess: str
    persona: Literal["serious", "cheery"] = "serious"

class GuessResponse(BaseModel):
    status: str
    message: str
    score: int = None

class HistoryResponse(BaseModel):
    history: list[str]