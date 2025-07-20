from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class SenderTypeEnum(str, Enum):
    user = "user"
    bot = "bot"
    channel = "channel"
    anonymous = "anonymous"

class MediaTypeEnum(str, Enum):
    photo = "photo"
    video = "video"
    document = "document"
    audio = "audio"
    voice = "voice"
    sticker = "sticker"
    gif = "gif"
    poll = "poll"
    webpage = "webpage"

class MessageBase(BaseModel):
    message_id: int
    dialog_id: int
    sender_id: Optional[int] = None
    sender_type: Optional[SenderTypeEnum] = None
    date: datetime
    message: Optional[str] = None
    views: Optional[int] = None
    media_type: Optional[MediaTypeEnum] = None
    media_size: Optional[int] = None
    reply_to_msg_id: Optional[int] = None
    forward_from_id: Optional[int] = None

class MessageCreate(MessageBase):
    pass

class MessageUpdate(MessageBase):
    pass

class MessageInDBBase(MessageBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class Message(MessageInDBBase):
    pass
