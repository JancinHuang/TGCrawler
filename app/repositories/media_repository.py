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
