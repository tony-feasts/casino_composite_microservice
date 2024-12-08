from httpx import AsyncClient
from app.models import UserStats, CallbackNameChange
from requests import put
from fastapi import HTTPException


class GameService:
    @staticmethod
    async def fetch_stats(base_url: str, username: str):
        """
        Fetch game stats for a user.
        """
        async with AsyncClient() as client:
            response = await client.get(f"{base_url}/user_stats/{username}")
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Unable to fetch stats")
            return response.json()

    @staticmethod
    async def initialize_stats(base_url: str, username: str):
        """
        Initialize game stats for a new user.
        """
        user_stats = UserStats(username=username, wins=0, losses=0)
        async with AsyncClient() as client:
            response = await client.post(f"{base_url}/user_stats/", json=user_stats.model_dump())
            if response.status_code != 201:
                raise HTTPException(status_code=response.status_code, detail="Unable to initialize stats")
            return response.headers.get("Location")

    @staticmethod
    def update_name(base_url: str, name_change: CallbackNameChange):
        """
        Update a user's name in game services.
        """
        response = put(f"{base_url}/user_stats/", json=name_change.model_dump())
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Unable to update username")
        return response.json()
