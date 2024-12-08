# these are services corresponding to the user

from httpx import AsyncClient
from fastapi import HTTPException
from app.models import UserInfo


class UserService:
    @staticmethod
    async def get_user_info(base_url: str, username: str, password: str):
        """
        Fetch user info for login verification.
        """
        async with AsyncClient() as client:
            response = await client.get(f"{base_url}/user_info/{username}/{password}")
            if response.status_code == 401:
                raise HTTPException(status_code=401, detail="Invalid username or password")
            return response.json()

    @staticmethod
    async def create_user(base_url: str, user_info: UserInfo):
        """
        Create a new user in the system.
        """
        async with AsyncClient() as client:
            response = await client.post(f"{base_url}/user_info/", json=user_info.model_dump())
            if response.status_code == 400:
                raise HTTPException(status_code=400, detail="Invalid username or password")
            return response
