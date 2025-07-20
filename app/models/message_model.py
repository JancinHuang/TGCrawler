from sqlalchemy import Column, BigInteger, String, Integer, DateTime, Enum, Text, UniqueConstraint, Index, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from .base_model import Base
import enum


class SenderTypeEnum(str, enum.Enum):
    user = "user"
    bot = "bot"
    channel = "channel"
    anonymous = "anonymous"


class MediaTypeEnum(str, enum.Enum):
    photo = "photo"
    video = "video"
    document = "document"
    audio = "audio"
    voice = "voice"
    sticker = "sticker"
    gif = "gif"
    poll = "poll"
    webpage = "webpage"


class Message(Base):
    __tablename__ = "messages"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="自增主键")
    message_id = Column(BigInteger, nullable=False, comment="消息ID")
    dialog_id = Column(BigInteger, ForeignKey("dialogs.dialog_id", ondelete="CASCADE"), nullable=False,
                       comment="关联的 dialog_id")
    sender_id = Column(BigInteger, nullable=True, comment="发送者ID")
    sender_type = Column(Enum(SenderTypeEnum), nullable=True, comment="发送者类型")
    date = Column(DateTime, nullable=False, comment="发送时间")
    message = Column(Text, nullable=True, comment="消息文本内容")
    views = Column(Integer, nullable=True, comment="查看次数（仅频道消息）")
    media_type = Column(Enum(MediaTypeEnum), nullable=True, comment="媒体类型")
    media_size = Column(BigInteger, nullable=True, comment="媒体文件大小（可选）")
    reply_to_msg_id = Column(BigInteger, nullable=True, comment="回复的消息ID")
    forward_from_id = Column(BigInteger, nullable=True, comment="转发来源的对话ID")
    created_at = Column(DateTime, server_default="CURRENT_TIMESTAMP", comment="记录创建时间")
    updated_at = Column(DateTime, server_default="CURRENT_TIMESTAMP", server_onupdate="CURRENT_TIMESTAMP",
                        comment="记录更新时间")

    dialog = relationship("Dialog", backref="messages")

    __table_args__ = (
        UniqueConstraint('dialog_id', 'message_id', name='uk_message'),
        Index('idx_sender', 'sender_id'),
        Index('idx_date', 'date'),
    )
