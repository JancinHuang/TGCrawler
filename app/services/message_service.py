from sqlalchemy.orm import Session
from ..repositories import MessageRepository
from ..schemas import MessageCreate, MessageUpdate
from ..models import Message

class MessageService:
    def __init__(self, db: Session):
        self.repo = MessageRepository(db)

    def get(self, id: int) -> Message | None:
        return self.repo.get_by_id(id)

    def get_by_dialog_and_msg_id(self, dialog_id: int, message_id: int) -> Message | None:
        return self.repo.get_by_dialog_and_message_id(dialog_id, message_id)

    def create(self, obj_in: MessageCreate) -> Message:
        return self.repo.create(obj_in)

    def update(self, db_obj: Message, obj_in: MessageUpdate) -> Message:
        return self.repo.update(db_obj, obj_in)

    def delete(self, id: int) -> None:
        self.repo.delete(id)
