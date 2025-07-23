from typing import Optional, List, Union

from sqlalchemy.orm import Session
import re

from telethon.tl.types import InputPeerChannel, InputPeerUser, PeerUser, PeerChannel

from .telegram_client_service import TelegramClientManager
from ..repositories import MessageRepository, MediaRepository
from ..schemas import MessageCreate, MessageUpdate, MediaCreate, Media
from ..models import Message
from ..schemas.message_schema import SenderTypeEnum, MediaTypeEnum

manager = TelegramClientManager()


class MessageService:
    def __init__(self, db: Session):
        self.message_repo = MessageRepository(db)
        self.media_repo = MediaRepository(db)
        self.client = None

    async def _get_client(self):
        self.client = await manager.get_client()
        return self.client

    def get(self, id: int) -> Message | None:
        return self.message_repo.get_by_id(id)

    def get_by_dialog_and_msg_id(self, dialog_id: int, message_id: int) -> Message | None:
        return self.message_repo.get_by_dialog_and_message_id(dialog_id, message_id)

    def create(self, obj_in: MessageCreate) -> Message:
        return self.message_repo.create(obj_in)

    def update(self, db_obj: Message, obj_in: MessageUpdate) -> Message:
        return self.message_repo.update(db_obj, obj_in)

    def delete(self, id: int) -> None:
        self.message_repo.delete(id)

    async def fetch_messages_by_keywords(
            self,
            channel_id: int,
            keywords: str,
            limit: Optional[int] = None,
            min_id: Optional[int] = 0
    ) -> bool:
        """
        获取并保存匹配关键词的消息
        :param channel_id: 频道ID或用户名
        :param keywords: 关键词字符串，用逗号分隔
        :param limit: 消息数量限制
        :param min_id: 最小消息ID
        :return: 保存到数据库的消息列表
        """
        if self.client is None:
            await self._get_client()

        if not self.client.is_connected():
            await self.client.connect()

            # 处理关键词
        keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]
        if not keyword_list:
            raise ValueError("至少需要提供一个有效关键词")

        # 构建关键词正则表达式
        pattern = re.compile('|'.join(map(re.escape, keywords)), re.IGNORECASE)
        await self.client.get_dialogs()
        async for message in self.client.iter_messages(
                entity=channel_id,
                limit=limit,
                min_id=min_id,
                wait_time=2,
                #reverse=True
        ):
            if not message.text:
                continue
            if pattern.search(message.text):
                # 构造 MessageCreate 对象
                message_create = MessageCreate(
                    message_id=message.id,
                    dialog_id=message.chat.id,
                    sender_id=self._get_sender_id(message),  # 使用新方法
                    sender_type=self._determine_sender_type(message),
                    date=message.date,
                    message=message.text,
                    views=getattr(message, 'views', None),
                    media_type=self._determine_media_type(message),
                    media_size=self._get_media_size(message),
                    reply_to_msg_id=getattr(message.reply_to, 'reply_to_msg_id', None),
                    forward_from_id=self._get_forward_from_id(message)
                )

                # 查找是否已有，决定 create or update
                existing = self.message_repo.get_by_dialog_and_message_id(
                    dialog_id=message.chat.id,
                    message_id=message.id
                )
                if existing:
                    self.message_repo.update(existing, message_create)
                else:
                    self.message_repo.create(message_create)

                # 如果有媒体附件，保存媒体信息
                if message.media:
                    media_create = self._create_media_from_message(message, message.id, message.chat.id)
                    # 检查媒体是否已存在
                    existing_media = self.media_repo.get_by_message_id(message.id)
                    if existing_media:
                        self.media_repo.update(existing_media, media_create)
                    else:
                        self.media_repo.create(media_create)

        return True

    def _create_media_from_message(self, message: Message, message_id: int, chat_id: int) -> MediaCreate:
        """从Telethon消息创建MediaCreate对象（包含duration获取）"""
        media_obj = message.media
        media_type = self._determine_media_type(message)

        # 初始化基础属性
        media_create = MediaCreate(
            message_id=message_id,
            dialog_id=chat_id,
            media_type=media_type,
            mime_type=None,
            file_name=None,
            file_reference=None,
            thumb_width=None,
            thumb_height=None,
            duration=None,  # 初始化为None，下面会根据类型处理
            size=None
        )

        # 处理不同媒体类型的属性
        if media_type == MediaTypeEnum.document:
            if hasattr(media_obj, 'document'):
                doc = media_obj.document
                media_create.mime_type = getattr(doc, 'mime_type', None)
                media_create.size = getattr(doc, 'size', None)
                media_create.file_reference = getattr(doc, 'file_reference', None)

                # 从document属性中获取文件名
                for attr in getattr(doc, 'attributes', []):
                    if hasattr(attr, 'file_name'):
                        media_create.file_name = attr.file_name
                    # 获取音频/视频时长
                    if hasattr(attr, 'duration'):
                        media_create.duration = round(attr.duration)

        elif media_type in [MediaTypeEnum.video, MediaTypeEnum.audio, MediaTypeEnum.voice]:
            # 视频/音频/语音消息的duration
            for attr in getattr(media_obj.document, 'attributes', []):
                if hasattr(attr, 'duration'):
                    media_create.duration = round(attr.duration)
                    break

        elif media_type == MediaTypeEnum.photo:
            # 照片没有duration，但可以获取缩略图尺寸
            if hasattr(media_obj, 'photo'):
                sizes = getattr(media_obj.photo, 'sizes', [])
                if sizes:
                    largest = max(sizes, key=lambda s: getattr(s, 'size', 0))
                    media_create.thumb_width = getattr(largest, 'w', None)
                    media_create.thumb_height = getattr(largest, 'h', None)

        return media_create

    def _determine_media_type(self, message):
        """更精确的媒体类型判断"""
        if not hasattr(message, 'media') or not message.media:
            return None

        if hasattr(message.media, 'photo'):
            return MediaTypeEnum.photo
        elif hasattr(message.media, 'document'):
            doc = message.media.document
            for attr in getattr(doc, 'attributes', []):
                if type(attr).__name__ == 'DocumentAttributeVideo':
                    return MediaTypeEnum.video
                elif type(attr).__name__ == 'DocumentAttributeAudio':
                    if hasattr(attr, 'voice') and attr.voice:
                        return MediaTypeEnum.voice
                    return MediaTypeEnum.audio
                elif type(attr).__name__ == 'DocumentAttributeSticker':
                    return MediaTypeEnum.sticker
                elif type(attr).__name__ == 'DocumentAttributeAnimated':
                    return MediaTypeEnum.gif
            return MediaTypeEnum.document
        elif hasattr(message.media, 'webPage'):
            return MediaTypeEnum.webpage
        elif hasattr(message.media, 'poll'):
            return MediaTypeEnum.poll
        return None

    def _get_media_size(self, message):
        media = (message.photo or message.video or message.document or
                 message.audio or message.voice)
        if media:
            return getattr(media, 'size', None)
        return None

    async def _resolve_entity(self, target: Union[int, str]):
        """增强版实体解析方法"""
        try:
            # 1. 先尝试直接解析（适用于已缓存的实体）
            try:
                return await self.client.get_entity(target)
            except ValueError:
                # 2. 尝试作为用户名解析（自动处理@前缀）
                if isinstance(target, str):
                    target = target.lstrip('@')
                    return await self.client.get_entity(target)

                # 3. 尝试作为原始Peer解析
                if isinstance(target, int):
                    # 如果是频道/超级群（负数ID）
                    if target < 0:
                        return InputPeerChannel(
                            channel_id=abs(target),
                            access_hash=0  # 需要真实access_hash
                        )
                    # 如果是普通用户
                    else:
                        return InputPeerUser(
                            user_id=target,
                            access_hash=0  # 需要真实access_hash
                        )

                raise ValueError("不支持的ID类型")
        except Exception as e:
            raise ValueError(f"无法解析实体 {target}: {str(e)}. 请确认："
                             f"1) 已加入该频道/群组 2) 使用正确ID/用户名 3) 有访问权限")

    def _get_sender_id(self, message):
        # 尝试多种方式获取 sender_id
        if hasattr(message, 'sender') and message.sender:
            return getattr(message.sender, 'id', None)
        if hasattr(message, 'from_id'):
            return message.from_id.user_id if isinstance(message.from_id, PeerUser) else None
        if hasattr(message, 'from_user'):
            return message.from_user.id
        return None

    def _determine_sender_type(self, message):
        # 优先检查是否频道消息
        if hasattr(message, 'sender') and message.sender:
            if hasattr(message.sender, 'channel_id'):
                return SenderTypeEnum.channel
            if hasattr(message.sender, 'bot'):
                return SenderTypeEnum.bot
            return SenderTypeEnum.user

        # 检查旧版属性
        if hasattr(message, 'from_id'):
            peer = message.from_id
            if isinstance(peer, PeerUser):
                return SenderTypeEnum.user
            elif isinstance(peer, PeerChannel):
                return SenderTypeEnum.channel

        # 默认匿名
        return SenderTypeEnum.anonymous

    def _get_forward_from_id(self, message):
        """安全获取转发来源的 ID"""
        if hasattr(message, 'forward') and message.forward:
            # Telethon 新版可能用 message.forward
            if hasattr(message.forward, 'from_id'):
                return message.forward.from_id.user_id if isinstance(message.forward.from_id, PeerUser) else None
            return getattr(message.forward, 'from_id', None)

        # 旧版 Telethon 可能用 forward_from 或 forward_from_chat
        if hasattr(message, 'forward_from'):
            return message.forward_from.id
        if hasattr(message, 'forward_from_chat'):
            return message.forward_from_chat.id
        return None

    """转发消息业务"""

    # async def forward_message(self, keyword, from_chat_id, to_chat_id='me'):
    #     if self.client is None:
    #         await self._get_client()
    #
    #     if not self.client.is_connected():
    #         await self.client.connect()
    #     await self.client.get_dialogs()
    #     message_ids = self.message_repo.get_message_ids_by_keyword_and_channel(keyword, from_chat_id)
    #     await self.client.get_dialogs()
    #     async for message in self.client.iter_messages(
    #             entity=to_chat_id,
    #             wait_time=2
    #     ):
    #         if not message.id == message_ids and message.chat.id == from_chat_id:
    #             for message_id in message_ids:
    #                 await self.client.forward_messages(
    #                     entity=to_chat_id,
    #                     messages=message_id,
    #                     from_peer=from_chat_id
    #                 )
    #         else:
    #             return False
    #     return True

    async def forward_message(
            self,
            keyword: str,
            from_chat_id: int,
            to_chat_id: str = 'me',
            min_duration: Optional[int] = None
    ) -> bool:
        """转发消息，可选按duration筛选"""
        if self.client is None:
            await self._get_client()

        if not self.client.is_connected():
            await self.client.connect()

        await self.client.get_dialogs()

        # 1. 获取基础消息ID列表
        message_ids = self.message_repo.get_message_ids_by_keyword_and_channel(keyword, from_chat_id)

        if not message_ids:
            return False

        # 2. 如果有duration要求，筛选符合条件的消息
        if min_duration is not None:
            filtered_ids = []
            for msg_id in message_ids:
                if self.get_message_duration(msg_id, from_chat_id, min_duration):
                    filtered_ids.append(msg_id)
            message_ids = filtered_ids

            if not message_ids:
                return False

        # 3. 检查目标频道是否已存在这些消息
        message_ids_set = set(message_ids)  # 转为集合提高查询效率
        async for message in self.client.iter_messages(
                entity=to_chat_id
        ):
            if message.chat.id == from_chat_id and message.id in message_ids_set:
                message_ids_set.remove(message.id)
                if not message_ids_set:  # 如果全部已存在则提前退出
                    return "转发的消息都已存在！"

        # 4. 执行转发
        if message_ids_set:
            await self.client.forward_messages(
                entity=to_chat_id,
                messages=list(message_ids_set),  # 转回列表
                from_peer=from_chat_id
            )
            return True

        return False

    def get_message_duration(
            self,
            message_id: int,
            chat_id: int,
            min_duration: int
    ) -> bool:
        """
        检查指定消息的媒体时长是否大于最小值

        :param message_id: 消息ID
        :param chat_id: 对话ID(dialog_id)
        :param min_duration: 最小duration要求(秒)
        :return: 如果满足条件返回True，否则返回False
        """
        return self.media_repo.exists_by_message_and_duration(
            message_id=message_id,
            dialog_id=chat_id,
            min_duration=min_duration
        )
