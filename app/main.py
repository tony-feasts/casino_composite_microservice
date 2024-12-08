from fastapi import FastAPI, HTTPException
from framework.middleware.logging_middleware import LoggingMiddleware
from os import getenv
from dotenv import load_dotenv
from models import NameChange, UserInfo, CallbackNameChange
from app.services.user_service import UserService
from app.services.game_service import GameService
import asyncio
from requests import put

app = FastAPI()
app.add_middleware(LoggingMiddleware)

load_dotenv()
USER_URL = getenv('USER_MICROSERVICE_URL')
BLACKJACK_URL = getenv('BLACKJACK_MICROSERVICE_URL')
ROULETTE_URL = getenv('ROULETTE_MICROSERVICE_URL')


@app.get('/login/{username}/{password}')
async def login(username: str, password: str):
    # Fetch user info
    await UserService.get_user_info(USER_URL, username, password)

    # Fetch game stats concurrently
    blackjack_stats, roulette_stats = await asyncio.gather(
        GameService.fetch_stats(BLACKJACK_URL, username),
        GameService.fetch_stats(ROULETTE_URL, username),
    )
    return {"username": username, "blackjack_stats": blackjack_stats, "roulette_stats": roulette_stats}


@app.post("/signup/")
async def signup(user_info: UserInfo):
    # Create a new user
    await UserService.create_user(USER_URL, user_info)

    # Initialize stats for games
    blackjack_stats_loc, roulette_stats_loc = await asyncio.gather(
        GameService.initialize_stats(BLACKJACK_URL, user_info.username),
        GameService.initialize_stats(ROULETTE_URL, user_info.username),
    )
    return {"username": user_info.username, "blackjack_stats_loc": blackjack_stats_loc, "roulette_stats_loc": roulette_stats_loc}


@app.put("/change_name/")
def change_name(name_change: NameChange):
    # Update user info in the user microservice
    response = put(f"{USER_URL}/user_info/", json=name_change.model_dump())
    if response.status_code == 401:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Update name in game services
    callback_name_change = CallbackNameChange(
        old_username=name_change.old_username,
        new_username=name_change.new_username,
        callback_url='_'
    )
    blackjack_stats_msg = GameService.update_name(BLACKJACK_URL, callback_name_change)
    roulette_stats_msg = GameService.update_name(ROULETTE_URL, callback_name_change)

    return {"new_name": name_change.new_username, "blackjack_stats_msg": blackjack_stats_msg, "roulette_stats_msg": roulette_stats_msg}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
