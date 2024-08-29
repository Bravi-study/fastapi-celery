from broadcaster import Broadcast
from fastapi import APIRouter

from project.config import settings

broadcast = Broadcast(settings.WS_MESSAGE_QUEUE)

ws_router = APIRouter()
