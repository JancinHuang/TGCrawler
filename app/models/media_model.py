from sqlalchemy import Column, BigInteger, String, Integer, DateTime, Enum, LargeBinary, ForeignKey, Index
from sqlalchemy.orm import declarative_base, relationship
from .base_model import Base
import enum


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


class Media(Base):
    __tablename__ = "medias"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    message_id = Column(BigInteger, ForeignKey("messages.message_id", ondelete="CASCADE"), nullable=False,
                        comment="关联消息的主键（messages.id）")
    dialog_id = Column(BigInteger, ForeignKey("dialogs.dialog_id", ondelete="CASCADE"), nullable=False,
                       comment="关联的对话ID（与 messages.dialog_id 一致）")
    media_type = Column(Enum(MediaTypeEnum), nullable=False, comment="媒体类型")
    mime_type = Column(String(128), nullable=True, comment="媒体 MIME 类型")
    file_name = Column(String(255), nullable=True, comment="文件名（如 document 类型）")
    file_reference = Column(LargeBinary, nullable=True, comment="Telethon 用于转发所需的引用")
    thumb_width = Column(Integer, nullable=True, comment="缩略图宽（可选）")
    thumb_height = Column(Integer, nullable=True, comment="缩略图高（可选）")
    duration = Column(Integer, nullable=True, comment="音视频时长（秒）")
    size = Column(BigInteger, nullable=True, comment="媒体文件大小")
    created_at = Column(DateTime, server_default="CURRENT_TIMESTAMP", comment="创建时间")

    dialog = relationship("Dialog", backref="medias")
    message = relationship("Message", backref="medias")

    __table_args__ = (

        Index('idx_message_id', 'message_id'),
    )
