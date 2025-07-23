from typing import Optional, Tuple, List

from sqlalchemy.orm import Session
from ..models import Media
from ..schemas import MediaCreate, MediaUpdate


class MediaRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, id: int) -> Media | None:
        return self.db.query(Media).filter(Media.id == id).first()

    def create(self, obj_in: MediaCreate) -> Media:
        obj = Media(**obj_in.dict())
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(self, db_obj: Media, obj_in: MediaUpdate) -> Media:
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

    def get_by_message_id(self, message_id: int) -> Optional[Media]:
        return self.db.query(Media).filter(Media.message_id == message_id).first()

    # 在 MediaRepository 类中添加
    def exists_by_message_and_duration(
            self,
            message_id: int,
            dialog_id: int,
            min_duration: int
    ) -> bool:
        """
        检查指定消息是否存在且duration大于阈值

        :param message_id: 消息ID
        :param dialog_id: 对话ID
        :param min_duration: 最小duration要求(秒)
        :return: 是否存在符合条件的记录
        """
        return self.db.query(
            self.db.query(Media)
            .filter(
                Media.message_id == message_id,
                Media.dialog_id == dialog_id,
                Media.duration > min_duration)
            .exists()
        ).scalar()
