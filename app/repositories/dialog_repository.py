from typing import Optional

from sqlalchemy.orm import Session
from ..models import Dialog
from ..schemas import DialogCreate, DialogUpdate
from ..schemas.dialog_schema import TelegramTypeEnum


class DialogRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> list[Dialog]:
        return self.db.query(Dialog).all()

    def get_by_dialog_id_and_type(self, dialog_id: int, telegram_type: TelegramTypeEnum) -> Optional[Dialog]:
        return self.db.query(Dialog).filter_by(dialog_id=dialog_id, telegram_type=telegram_type).first()

    def get_by_id(self, id: int) -> Dialog | None:
        return self.db.query(Dialog).filter(Dialog.id == id).first()

    def get_by_dialog_id_and_type(self, dialog_id: int, telegram_type: str) -> Dialog | None:
        return (
            self.db.query(Dialog)
            .filter(Dialog.dialog_id == dialog_id, Dialog.telegram_type == telegram_type)
            .first()
        )

    def create(self, obj_in: DialogCreate) -> Dialog:
        obj = Dialog(**obj_in.dict())
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj


    def update(self, db_obj: Dialog, obj_in: DialogUpdate) -> Dialog:
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
