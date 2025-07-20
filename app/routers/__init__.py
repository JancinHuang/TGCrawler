from .dialog_router import router as dialog_router
from .message_router import router as message_router
from .media_router import router as media_router
from .telegram_client_router import router as telegram_client_router

__all__ = [
    "dialog_router",
    "message_router",
    "media_router",
    "telegram_client_router"
]
