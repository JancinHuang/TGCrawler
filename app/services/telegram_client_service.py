# app/services/telegram_client_service.py
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import HTTPException
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.sessions import StringSession
from pydantic_settings import BaseSettings
from dotenv import set_key, find_dotenv


class TelegramConfig(BaseSettings):
    # Telegram 基本配置
    telegram_api_id: int
    telegram_api_hash: str
    telegram_phone: Optional[str] = None
    telegram_session_string: str = "anon"

    # 代理配置
    telegram_proxy_type: Optional[str] = None
    telegram_proxy_host: Optional[str] = None
    telegram_proxy_port: Optional[int] = None

    class Config:
        env_prefix = "TELEGRAM_"  # 自动添加前缀
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    def save_session_to_env(self, session_str: str):
        """使用python-dotenv自动更新.env文件"""
        # 自动向上级目录查找.env文件
        env_path = find_dotenv(filename='.env', raise_error_if_not_found=True)

        # 更新或添加配置项
        set_key(
            env_path,
            "TELEGRAM_SESSION_STRING",
            session_str,
            quote_mode="never"  # 不添加引号
        )


class TelegramClientManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self._client: Optional[TelegramClient] = None
        self._last_activity: Optional[datetime] = None
        self.config = TelegramConfig()  # 初始化时加载配置
        self._last_error: Optional[str] = None
        self._lock = asyncio.Lock()  # 异步锁
        self._login_data = {}  # 临时存储验证码等信息

    def _get_proxy(self):
        """获取代理配置"""
        if not all([
            self.config.telegram_proxy_type,
            self.config.telegram_proxy_host,
            self.config.telegram_proxy_port
        ]):
            return None

        return (
            self.config.telegram_proxy_type,
            self.config.telegram_proxy_host,
            self.config.telegram_proxy_port
        )

    async def send_code(self, phone: str) -> bool:
        """发送验证码（返回验证码哈希）"""
        client = TelegramClient(
            StringSession(),
            self.config.telegram_api_id,
            self.config.telegram_api_hash,
            proxy=self._get_proxy()
        )
        await client.connect()

        sent = await client.send_code_request(phone)
        self._login_data = {
            "client": client,
            "phone": phone,
            "phone_code_hash": sent.phone_code_hash
        }
        return True

    async def login_with_code(self, code: str) -> bool:
        """用验证码登录（返回session_string）"""
        if not self._login_data.get("client"):
            raise ValueError("请先发送验证码")

        client: TelegramClient = self._login_data["client"]
        try:
            await client.sign_in(
                phone=self._login_data["phone"],
                code=code,
                phone_code_hash=self._login_data["phone_code_hash"]
            )
            session_str = client.session.save()
            self.config.save_session_to_env(session_str)
            return True
        except SessionPasswordNeededError:
            raise ValueError("需要两步验证密码，请关闭验证密码")
        finally:
            await client.disconnect()

    async def connect(self) -> Dict[str, Any]:
        """
        暴露给接口的连接方法
        返回标准化字典而非原生Client对象
        """
        try:

            await self._get_client()
            return {
                "status": "connected",
                "session_valid": True,
                "proxy_enabled": bool(self._get_proxy()),
                "connection_time": datetime.now().isoformat()
            }
        except Exception as e:
            self._last_error = str(e)
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "CONNECTION_FAILED",
                    "message": f"Telegram连接失败: {e}",
                    "solution": "请检查session_string或代理配置"
                }
            )

    async def _get_client(self) -> TelegramClient:
        """内部使用的连接方法（改造版）"""

        session_str = (self.config.telegram_session_string or "").strip()
        if not session_str or len(session_str) < 50:
            raise ValueError("Invalid session string")

        # 代理配置
        proxy = self._get_proxy()  # 保持你的原有方法

        # 客户端初始化（添加重试机制）
        max_retries = 5
        for attempt in range(max_retries):
            try:
                self._client = TelegramClient(
                    session=StringSession(session_str),
                    api_id=self.config.telegram_api_id,
                    api_hash=self.config.telegram_api_hash,
                    proxy=proxy,
                    connection_retries=5  # 内置重试
                )

                if not self._client.is_connected():
                    await self._client.start()
                return self._client

            except Exception as e:
                if attempt == max_retries - 1:
                    await self.disconnect()
                    raise
                await asyncio.sleep(1)

    async def get_status(self) -> Dict[str, Any]:
        """
        获取当前Telegram连接状态
        返回:
            Dict[str, Any]: 包含连接状态、代理信息和最后活动时间的字典
        """
        status = {
            "is_connected": False,
            "proxy_enabled": bool(self._get_proxy()),
            "last_activity": self._last_activity.isoformat() if self._last_activity else None,
            "last_error": self._last_error,
            "session_valid": bool(self.config.telegram_session_string),
            "details": {}
        }

        try:
            client =await self.get_client()
            status["is_connected"] = await self._is_connected()

            if status["is_connected"]:
                me = await client.get_me()
                status["details"].update({
                    "user_id": me.id,
                    "username": me.username,
                    "phone": me.phone,
                    "dc_id": me.photo.dc_id if me.photo else None
                })
        except Exception as e:
            status["last_error"] = str(e)
            status["is_connected"] = False

        if status["proxy_enabled"]:
            status["proxy_details"] = {
                "type": self.config.telegram_proxy_type,
                "host": self.config.telegram_proxy_host,
                "port": self.config.telegram_proxy_port
            }

        return status

    async def disconnect(self):
        """断开连接（接口使用）"""
        await self._safe_disconnect()
        return {"status": "disconnected", "time": datetime.now().isoformat()}

    async def _is_connected(self) -> bool:
        """安全检查连接状态"""
        try:
            return self._client and self._client.is_connected()
        except:
            return False

    async def _safe_disconnect(self):
        """安全断开连接"""
        if self._client:
            try:
                if self._client.is_connected():
                    await self._client.disconnect()
            finally:
                self._client = None


    async def get_client(self) -> TelegramClient:
        """
        安全获取客户端实例
        返回:
            TelegramClient: 已连接的客户端实例
        异常:
            RuntimeError: 客户端未初始化或连接失败
        """
        async with self._lock:  # 保证线程安全
            if self._client is None:
                raise RuntimeError("客户端未初始化，请先调用connect()")

            if not await self._is_connected():
                await self._reconnect()

            return self._client
