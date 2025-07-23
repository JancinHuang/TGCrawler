from datetime import datetime

from sqlalchemy.orm import Session
from ..repositories import DialogRepository
from ..schemas import DialogCreate, DialogUpdate
from ..models import Dialog
from ..schemas.dialog_schema import TelegramTypeEnum
from .telegram_client_service import TelegramClientManager

manager = TelegramClientManager()


class DialogService:
    def __init__(self, db: Session):
        self.repo = DialogRepository(db)
        self.client = None

    async def _get_client(self):
        self.client = await manager.get_client()
        return self.client

    async def get_all_dialogs(self):
        if self.client is None:
            await self._get_client()

        dialogs = await self.client.get_dialogs()

        for dialog in dialogs:
            entity = dialog.entity
            if not hasattr(entity, "id") or not hasattr(entity, "__class__"):
                continue

            # 识别对话类型
            if entity.__class__.__name__ == "User":
                telegram_type = TelegramTypeEnum.user
            elif entity.__class__.__name__ == "Chat":
                telegram_type = TelegramTypeEnum.chat
            elif entity.__class__.__name__ == "Channel":
                telegram_type = TelegramTypeEnum.channel
            else:
                continue  # 跳过未知类型

            # 构造 DialogCreate
            dialog_create = DialogCreate(
                dialog_id=entity.id,
                telegram_type=telegram_type,
                access_hash=getattr(entity, "access_hash", None),
                title=getattr(entity, "title", None) or getattr(entity, "first_name", None),
                username=getattr(entity, "username", None),
                verified=getattr(entity, "verified", False),
                bot=getattr(entity, "bot", False),
                participants_count=getattr(entity, "participants_count", None),
                last_message_id=dialog.message.id if dialog.message else None,
                last_activity=datetime.fromtimestamp(dialog.message.date.timestamp()) if dialog.message else None,
                unread_count=dialog.unread_count or 0,
            )

            # 查找是否已有，决定 create or update
            existing = self.repo.get_by_dialog_id_and_type(entity.id, telegram_type)
            if existing:
                self.repo.update(existing, dialog_create)
            else:
                self.repo.create(dialog_create)

        return self.repo.get_all()

    def get(self, dialog_id: int, telegram_type: str) -> Dialog | None:
        return self.repo.get_by_dialog_id_and_type(dialog_id, telegram_type)

    def create(self, obj_in: DialogCreate) -> Dialog:
        return self.repo.create(obj_in)

    def update(self, db_obj: Dialog, obj_in: DialogUpdate) -> Dialog:
        return self.repo.update(db_obj, obj_in)

    def delete(self, id: int) -> None:
        self.repo.delete(id)
