from sqlalchemy.orm import Session
from ..models import Message
from ..schemas import MessageCreate, MessageUpdate

class MessageRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, id: int) -> Message | None:
        return self.db.query(Message).filter(Message.id == id).first()

    def get_by_dialog_and_message_id(self, dialog_id: int, message_id: int) -> Message | None:
        return (
            self.db.query(Message)
            .filter(Message.dialog_id == dialog_id, Message.message_id == message_id)
            .first()
        )

    def create(self, obj_in: MessageCreate) -> Message:
        obj = Message(**obj_in.dict())
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(self, db_obj: Message, obj_in: MessageUpdate) -> Message:
        obj_data = obj_in.dict(exclude_unset=True)
        for field, value in obj_data.items():
            setattr(db_obj, field, value)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, id: int) -> None:
        obj = self.get_by_id(id)
        if obj:
            self.db.delete(obj)
            self.db.commit()

    def get_message_ids_by_keyword_and_channel(self, keyword: str, channel_id: int) -> list[int]:
        """
        根据关键词和频道ID(dialog_id)获取匹配的消息ID列表

        Args:
            keyword: 要搜索的关键词
            channel_id: 频道/对话的ID(dialog_id)

        Returns:
            匹配的消息ID列表
        """
        results = (
            self.db.query(Message.message_id)
            .filter(
                Message.dialog_id == channel_id,
                Message.message.contains(keyword)
            )
            .all()
        )
        return [result[0] for result in results]
