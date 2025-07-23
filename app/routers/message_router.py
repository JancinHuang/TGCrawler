from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional

from ..services import MessageService
from ..schemas import Message, MessageCreate, MessageUpdate
from ..database import get_db

router = APIRouter(prefix="/messages", tags=["messages"])


class MessageRequest(BaseModel):
    channel_id: int
    keywords: str = "编程"
    limit: Optional[int] = None
    min_id: Optional[int] = 0


class ForwardRequest(BaseModel):
    keyword: str
    from_chat_id: int
    to_chat_id: int = 2629932339
    min_duration: int


@router.post("/get_message")
async def get_messages(
        param: MessageRequest,
        db: Session = Depends(get_db)
):
    """
    根据频道ID和关键词获取消息

    参数:
    - channel_id: 要查询的Telegram频道ID(整数)
    - keywords: 要匹配的关键词列表，默认为["编程"]
    - limit: 返回消息数量的限制(可选)
    - min_id: 只获取大于此ID的消息(可选)
    """
    try:
        service = MessageService(db)
        messages = await service.fetch_messages_by_keywords(
            channel_id=param.channel_id,
            keywords=param.keywords,
            limit=param.limit,
            min_id=param.min_id
        )

        if not messages:
            raise HTTPException(
                status_code=404,
                detail="未找到匹配关键词的消息"
            )
        if messages:
            return "消息获取完毕！"

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取消息时出错: {str(e)}"
        )


@router.post("/forward_message")
async def forward_message(
        param: ForwardRequest,
        db: Session = Depends(get_db)
):
    try:
        service = MessageService(db)
        messages = await service.forward_message(keyword=param.keyword,
                                                 from_chat_id=param.from_chat_id,
                                                 to_chat_id=param.to_chat_id,
                                                 min_duration=param.min_duration, )
        if messages:
            return "转发成功！"
        else:
            return "转发的消息都已存在！"
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


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
