from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..services import DialogService
from ..schemas import Dialog, DialogCreate, DialogUpdate
from ..database import get_db

router = APIRouter(prefix="/dialogs", tags=["dialogs"])

@router.get("/{dialog_id}/{telegram_type}", response_model=Dialog)
def read_dialog(dialog_id: int, telegram_type: str, db: Session = Depends(get_db)):
    service = DialogService(db)
    db_obj = service.get(dialog_id, telegram_type)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Dialog not found")
    return db_obj

@router.post("/", response_model=Dialog)
def create_dialog(dialog_in: DialogCreate, db: Session = Depends(get_db)):
    service = DialogService(db)
    db_obj = service.get(dialog_in.dialog_id, dialog_in.telegram_type)
    if db_obj:
        raise HTTPException(status_code=400, detail="Dialog already exists")
    return service.create(dialog_in)

@router.put("/{id}", response_model=Dialog)
def update_dialog(id: int, dialog_in: DialogUpdate, db: Session = Depends(get_db)):
    service = DialogService(db)
    db_obj = service.repo.get_by_id(id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Dialog not found")
    return service.update(db_obj, dialog_in)

@router.delete("/{id}", status_code=204)
def delete_dialog(id: int, db: Session = Depends(get_db)):
    service = DialogService(db)
    db_obj = service.repo.get_by_id(id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Dialog not found")
    service.delete(id)
