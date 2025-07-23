from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


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


class MediaBase(BaseModel):
    message_id: int
    dialog_id: int
    media_type: MediaTypeEnum
    mime_type: Optional[str] = None
    file_name: Optional[str] = None
    file_reference: Optional[bytes] = None
    thumb_width: Optional[int] = None
    thumb_height: Optional[int] = None
    duration: Optional[int] = None
    size: Optional[int] = None


class MediaCreate(MediaBase):
    pass


class MediaUpdate(MediaBase):
    pass


class MediaInDBBase(MediaBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class Media(MediaInDBBase):
    pass
