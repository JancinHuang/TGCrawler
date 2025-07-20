from sqlalchemy import Column, BigInteger, String, Integer, DateTime, Boolean, Enum, UniqueConstraint, Index
from sqlalchemy.orm import declarative_base
from .base_model import Base
import enum


class TelegramTypeEnum(str, enum.Enum):
    user = "user"
    chat = "chat"
    channel = "channel"


class Dialog(Base):
    __tablename__ = "dialogs"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="自增主键")
    dialog_id = Column(BigInteger, nullable=False, comment="对话ID，取自 entity.id")
    telegram_type = Column(Enum(TelegramTypeEnum), nullable=False, comment="对话类型")
    access_hash = Column(BigInteger, nullable=True, comment="访问哈希，仅某些类型可用")
    title = Column(String(255), nullable=True, comment="标题/名称")
    username = Column(String(32), nullable=True, comment="用户名或频道链接（@xxx）")
    verified = Column(Boolean, default=False, comment="是否认证账号，仅限User/Channel")
    bot = Column(Boolean, default=False, comment="是否为机器人，仅User有效")
    participants_count = Column(Integer, nullable=True, comment="成员数量（仅Chat/Channel）")
    last_message_id = Column(BigInteger, nullable=True, comment="最后一条消息ID")
    last_activity = Column(DateTime, nullable=True, comment="最后活动时间（取最后消息时间）")
    unread_count = Column(Integer, default=0, comment="未读消息数")
    created_at = Column(DateTime, server_default="CURRENT_TIMESTAMP", comment="记录创建时间")
    updated_at = Column(DateTime, server_default="CURRENT_TIMESTAMP", server_onupdate="CURRENT_TIMESTAMP",
                        comment="记录更新时间")

    __table_args__ = (
        UniqueConstraint('dialog_id', 'telegram_type', name='uk_dialog'),
        Index('idx_username', 'username'),
        Index('idx_activity', 'last_activity'),
        Index('dialog_id', 'dialog_id'),
    )
