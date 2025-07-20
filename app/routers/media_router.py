from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..services import MediaService
from ..schemas import Media, MediaCreate, MediaUpdate
from ..database import get_db

router = APIRouter(prefix="/medias", tags=["medias"])

@router.get("/{id}", response_model=Media)
def read_media(id: int, db: Session = Depends(get_db)):
    service = MediaService(db)
    db_obj = service.get(id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Media not found")
    return db_obj

@router.post("/", response_model=Media)
def create_media(media_in: MediaCreate, db: Session = Depends(get_db)):
    service = MediaService(db)
    return service.create(media_in)

@router.put("/{id}", response_model=Media)
def update_media(id: int, media_in: MediaUpdate, db: Session = Depends(get_db)):
    service = MediaService(db)
    db_obj = service.get(id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Media not found")
    return service.update(db_obj, media_in)

@router.delete("/{id}", status_code=204)
def delete_media(id: int, db: Session = Depends(get_db)):
    service = MediaService(db)
    db_obj = service.get(id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Media not found")
    service.delete(id)
