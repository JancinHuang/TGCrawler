from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class TelegramTypeEnum(str, Enum):
    user = "user"
    chat = "chat"
    channel = "channel"

class DialogBase(BaseModel):
    dialog_id: int
    telegram_type: TelegramTypeEnum
    access_hash: Optional[int] = None
    title: Optional[str] = None
    username: Optional[str] = None
    verified: Optional[bool] = False
    bot: Optional[bool] = False
    participants_count: Optional[int] = None
    last_message_id: Optional[int] = None
    last_activity: Optional[datetime] = None
    unread_count: Optional[int] = 0

class DialogCreate(DialogBase):
    pass

class DialogUpdate(DialogBase):
    pass

class DialogInDBBase(DialogBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class Dialog(DialogInDBBase):
    pass
