from sqlalchemy.orm import Session
from ..repositories import MediaRepository
from ..schemas import MediaCreate, MediaUpdate
from ..models import Media

class MediaService:
    def __init__(self, db: Session):
        self.repo = MediaRepository(db)

    def get(self, id: int) -> Media | None:
        return self.repo.get_by_id(id)

    def create(self, obj_in: MediaCreate) -> Media:
        return self.repo.create(obj_in)

    def update(self, db_obj: Media, obj_in: MediaUpdate) -> Media:
        return self.repo.update(db_obj, obj_in)

    def delete(self, id: int) -> None:
        self.repo.delete(id)
