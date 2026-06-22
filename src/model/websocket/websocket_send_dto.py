import json
from typing import Any

from pydantic import BaseModel

from src.model.websocket.websocket_message_type import WebSocketMessageType


class WebSocketSendDTO(BaseModel):
    type: WebSocketMessageType
    content: Any
