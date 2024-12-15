# app/main.py
from dotenv import load_dotenv

from app.models import GameHistory

load_dotenv()

from fastapi import FastAPI, HTTPException, Header, Request
from framework.middleware.logging_middleware import LoggingMiddleware
from framework.middleware.delete_auth_middleware import DeleteAuthMiddleware
from os import getenv
from models import NameChange, UserInfo, UserStats, CallbackNameChange
from requests import put, delete, post, get
from httpx import AsyncClient
import asyncio
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry.instrumentation.asgi import OpenTelemetryMiddleware
import boto3
import json

app = FastAPI()

from framework.middleware.correlation_id_middleware import CorrelationIDMiddleware
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
# from opentelemetry.sdk.trace.export import BatchSpanProcessor
# from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
#
# # Configure OpenTelemetry with Google Cloud Trace
resource = Resource.create({"service.name": "casino-info-service"})  # Replace with your service name
tracer_provider = TracerProvider(resource=resource)
#
# # Set up Google Cloud Trace Exporter
# cloud_trace_exporter = CloudTraceSpanExporter()
# span_processor = BatchSpanProcessor(cloud_trace_exporter)

# Use ConsoleSpanExporter to view spans locally
console_exporter = ConsoleSpanExporter()
span_processor = SimpleSpanProcessor(console_exporter)
tracer_provider.add_span_processor(span_processor)


# # Set the global tracer provider
trace.set_tracer_provider(tracer_provider)
#
# # Automatically instrument FastAPI

app.add_middleware(CorrelationIDMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(DeleteAuthMiddleware)
app.add_middleware(OpenTelemetryMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ideally, specify the exact domain(s) of your frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
async def login(username: str, password: str, request: Request):
    correlation_id = getattr(request.state, "correlation_id", None)
    print(correlation_id)
    async with AsyncClient() as client:
        response = await client.get(
            f'{USER_URL}/user_info/{username}/{password}',
                headers={"X-Correlation-ID": correlation_id})
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

@app.delete("/delete_game/{game_id}")
def delete_game(game_id: int, auth: str = Header(...)):
    headers = {'auth': auth}
    response = delete(
        f'{ROULETTE_URL}/game_history/{game_id}', headers=headers)
    if response.status_code == 403:
        raise HTTPException(status_code=403, detail="Permission denied")
    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="Game not found")
    return {"message": "Game history updated successfully"}

event = False
@app.post("/roulette_game")
def post_game_to_roulette(gameHistory: GameHistory):
    global event
    response = post(f"{ROULETTE_URL}/game_history/",
                             json=gameHistory.model_dump())
    if response.status_code != 201:
        return {"error": "Failed to create game in Roulette microservice"}

    while not event:
        pass
    temp = event
    event = False
    return {"message": "Game created successfully", "event_data": temp}



@app.post("/sns/events")
async def sns_event_handler(request: Request):
    global event
    """
    Endpoint to handle incoming SNS events.
    """
    try:
        body = await request.json()
        if body.get("Type") == "SubscriptionConfirmation":
            # Confirm the subscription by making a GET request to the provided SubscribeURL
            subscribe_url = body["SubscribeURL"]
            response = get(subscribe_url)
            print(f"Subscription confirmed: {response.status_code}")
            return
        event = body
    except Exception as e:
        print(f"Error processing SNS event: {e}")
        return {"error": str(e)}

step_functions_client = boto3.client('stepfunctions', region_name='us-east-1')
STEP_FUNCTION_ARN = "arn:aws:states:us-east-1:920373012265:stateMachine:MyStateMachine-1ri6etdzx"

@app.post("/blackjack_game")
def post_game_to_blackjack(game_history: GameHistory):
    """
    Endpoint to trigger the Step Functions workflow for posting a blackjack game.
    """
    try:
        # Prepare the input for Step Functions
        payload = {
            "username": game_history.username,
            "game_history": {
                "username": game_history.username,
                "result": game_history.result
            }
        }

        # Start Step Functions workflow
        response = step_functions_client.start_execution(
            stateMachineArn=STEP_FUNCTION_ARN,
            input=json.dumps(payload)
        )

        # Return the Step Functions execution details
        return {
            "message": "Workflow triggered successfully",
            "executionArn": response["executionArn"],
            "startDate": response["startDate"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
   import uvicorn
   uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
