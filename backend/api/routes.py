from fastapi import APIRouter, Depends, HTTPException
from .models import GuessInput, GuessResponse, HistoryResponse
from core.game_logic import GameLogic
from core.ai_client import AIClient
from core.moderation import Moderation
from core.rate_limiter import RateLimiter
from fastapi import Request

router = APIRouter()
game_logic = GameLogic()
ai_client = AIClient()
moderation = Moderation()

async def get_ip(request: Request):
    return request.client.host

@router.post("/guess", response_model=GuessResponse)
async def submit_guess(input: GuessInput, ip: str = Depends(get_ip)):
    if moderation.is_profane(input.guess):
        raise HTTPException(400, detail="Inappropriate guess")
    
    session_id = ip  # Using IP as session ID for simplicity
    rate_limiter = RateLimiter(game_logic.redis, max_requests=100, window=60)
    await rate_limiter.check(ip)
    
    if await game_logic.is_duplicate(session_id, input.guess):
        return GuessResponse(
            status="game_over",
            message=f"{input.guess} already guessed! Game Over!"
        )
    
    verdict, reasoning = await ai_client.validate_guess(input.guess, "Rock", input.persona)
    if verdict:
        await game_logic.add_guess(session_id, input.guess)
        count = await game_logic.increment_global_count(input.guess)
        score = await game_logic.get_score(session_id)
        return GuessResponse(
            status="success",
            message=f"Nice! {input.guess} beats Rock. {reasoning} Guessed {count} times before.",
            score=score
        )
    return GuessResponse(
        status="fail",
        message=f"{input.guess} doesn't beat Rock. {reasoning}"
    )

@router.get("/history", response_model=HistoryResponse)
async def get_history(ip: str = Depends(get_ip)):
    history = await game_logic.get_history(ip)
    return HistoryResponse(history=history)

@router.post("/reset")
async def reset_session(ip: str = Depends(get_ip)):
    await game_logic.clear_session(ip)
    return {"message": "Session reset successfully"}