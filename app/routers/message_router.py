from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..services import MessageService
from ..schemas import Message, MessageCreate, MessageUpdate
from ..database import get_db

router = APIRouter(prefix="/messages", tags=["messages"])


@router.get("/{id}", response_model=Message)
def read_message(id: int, db: Session = Depends(get_db)):
    service = MessageService(db)
    db_obj = service.get(id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Message not found")
    return db_obj


@router.get("/dialog/{dialog_id}/message/{message_id}", response_model=Message)
def read_message_by_dialog_and_msg(dialog_id: int, message_id: int, db: Session = Depends(get_db)):
    service = MessageService(db)
    db_obj = service.get_by_dialog_and_msg_id(dialog_id, message_id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Message not found")
    return db_obj


@router.post("/", response_model=Message)
def create_message(message_in: MessageCreate, db: Session = Depends(get_db)):
    service = MessageService(db)
    # 可加业务逻辑判断
    return service.create(message_in)


@router.put("/{id}", response_model=Message)
def update_message(id: int, message_in: MessageUpdate, db: Session = Depends(get_db)):
    service = MessageService(db)
    db_obj = service.get(id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Message not found")
    return service.update(db_obj, message_in)


@router.delete("/{id}", status_code=204)
def delete_message(id: int, db: Session = Depends(get_db)):
    service = MessageService(db)
    db_obj = service.get(id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Message not found")
    service.delete(id)
