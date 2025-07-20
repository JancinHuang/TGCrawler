from sqlalchemy.orm import Session
from ..repositories import DialogRepository
from ..schemas import DialogCreate, DialogUpdate
from ..models import Dialog

class DialogService:
    def __init__(self, db: Session):
        self.repo = DialogRepository(db)

    def get(self, dialog_id: int, telegram_type: str) -> Dialog | None:
        return self.repo.get_by_dialog_id_and_type(dialog_id, telegram_type)

    def create(self, obj_in: DialogCreate) -> Dialog:
        return self.repo.create(obj_in)

    def update(self, db_obj: Dialog, obj_in: DialogUpdate) -> Dialog:
        return self.repo.update(db_obj, obj_in)

    def delete(self, id: int) -> None:
        self.repo.delete(id)
