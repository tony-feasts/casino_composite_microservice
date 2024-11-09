# app/main.py

from fastapi import FastAPI, HTTPException
from framework.middleware.logging_middleware import LoggingMiddleware
from os import getenv
from dotenv import load_dotenv
from models import NameChange, UserInfo, UserStats, CallbackNameChange
from requests import put
from httpx import AsyncClient
import asyncio
app = FastAPI()
app.add_middleware(LoggingMiddleware)

load_dotenv()
USER_URL = getenv('USER_MICROSERVICE_URL')
BLACKJACK_URL = getenv('BLACKJACK_MICROSERVICE_URL')
ROULETTE_URL = getenv('ROULETTE_MICROSERVICE_URL')

async def fetch_stats(base_url, username):
    async with AsyncClient() as client:
        response = await client.get(f'{base_url}/user_stats/{username}')
        return response.json()

async def initialize_stats(base_url, username):
    user_stats = UserStats(username=username, wins=0, losses=0)
    async with AsyncClient() as client:
        response = await client.post(f'{base_url}/user_stats/',
                                     json=user_stats.model_dump())
        return response.headers.get('Location')

def game_service_name_change(base_url, name_change):
    callback_name_change = CallbackNameChange(
        old_username=name_change.old_username,
        new_username=name_change.new_username,
        callback_url='_')
    return put(f'{base_url}/user_stats/',
                   json=callback_name_change.model_dump()).json()


@app.get('/login/{username}/{password}')
async def login(username: str, password: str):
    async with AsyncClient() as client:
        response = await client.get(
            f'{USER_URL}/user_info/{username}/{password}')
        if response.status_code == 401:
            raise HTTPException(status_code=401,
                                detail="Invalid username or password")

    blackjack_stats, roulette_stats = await asyncio.gather(
        fetch_stats(BLACKJACK_URL, username),
        fetch_stats(ROULETTE_URL, username))
    return {'username': username, 'blackjack_stats': blackjack_stats,
            'roulette_stats': roulette_stats}

@app.post("/signup/")
async def signup(user_info: UserInfo):
    async with AsyncClient() as client:
        response = await client.post(
            f'{USER_URL}/user_info/', json=user_info.model_dump())
        if response.status_code == 400:
            raise HTTPException(status_code=400,
                                detail="Invalid username or password")

        blackjack_stats_loc, roulette_stats_loc = await asyncio.gather(
            initialize_stats(BLACKJACK_URL, user_info.username),
            initialize_stats(ROULETTE_URL, user_info.username))
        return {'username': user_info.username,
                'blackjack_stats_loc': blackjack_stats_loc,
                'roulette_stats_loc': roulette_stats_loc}

@app.put("/change_name/")
def change_name(name_change: NameChange):
    response = put(f'{USER_URL}/user_info/', json=name_change.model_dump())
    if response.status_code == 401:
        raise HTTPException(status_code=401,
                            detail="Invalid username or password")

    return {'new_name': name_change.new_username,
            'blackjack_stats_msg': game_service_name_change(BLACKJACK_URL,
                                                            name_change),
            'roulette_stats_msg': game_service_name_change(ROULETTE_URL,
                                                           name_change)}

if __name__ == "__main__":
   import uvicorn
   uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
