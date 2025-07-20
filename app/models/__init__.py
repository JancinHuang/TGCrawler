# telegram_crawler/models/__init__.py
from .base_model import Base
from .dialog_model import Dialog, TelegramTypeEnum
from .message_model import Message, SenderTypeEnum, MediaTypeEnum as MessageMediaTypeEnum
from .media_model import Media, MediaTypeEnum as MediaMediaTypeEnum
