# app/routers/telegram_router.py
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Form, HTTPException
from pydantic import BaseModel
from telethon import TelegramClient
from telethon.sessions import StringSession
from ..services import TelegramClientManager
from telethon.errors import SessionPasswordNeededError

router = APIRouter(prefix="/telegram", tags=["Telegram"])

# 创建 TelegramClientManager 实例（单例）
tg_manager = TelegramClientManager()


class PhoneRequest(BaseModel):
    phone: str


class LoginRequest(BaseModel):
    code: str
    password: Optional[str] = None


@router.post("/get-code", summary="获取验证码")
async def get_code(data: PhoneRequest):
    try:
        send_code = await tg_manager.send_code(data.phone)
        if send_code:
            return {"message": "验证码已发送"}
    except Exception as e:
        raise HTTPException(400, detail=str(e))


@router.post("/login", summary="初次登录，保存session")
async def complete_login(data: LoginRequest):
    try:
        session_str = await tg_manager.login_with_code(data.code)
        if session_str:
            return {"初次登录成功！"}
    except ValueError as e:
        raise HTTPException(400, detail=str(e))


@router.post("/connect", summary="建立Telegram连接")
async def connect_telegram():
    """
    初始化Telegram客户端连接
    - 使用配置中的session_string
    - 自动处理代理配置
    - 失败返回详细错误信息
    """
    try:
        await tg_manager.connect()
        return {
            "status": "success",
            "message": "Telegram客户端已连接",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "CONNECTION_FAILED",
                "message": str(e),
                "solution": [
                    "检查TELEGRAM_SESSION_STRING是否有效",
                    "确认代理配置正确（如启用）"
                ]
            }
        )


@router.get("/status", summary="获取连接状态")
async def get_telegram_status():
    """
    获取当前Telegram连接状态
    - 返回连接是否活跃
    - 显示代理使用情况
    - 包含最后活动时间和代理详情（如果配置）
    """
    try:
        status = await tg_manager.get_status()

        result = {
            "connected": status["is_connected"],
            "proxy_enabled": status["proxy_enabled"],
            "last_activity": status["last_activity"],
            "session_valid": status["session_valid"]
        }

        # 如果有代理详情，就一并返回
        if status.get("proxy_details"):
            result["proxy_details"] = status["proxy_details"]

        # 如果你想调试详细信息（比如登录用户信息），也可以返回
        if status.get("details"):
            result["user"] = status["details"]

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "STATUS_CHECK_FAILED",
                "message": str(e)
            }
        )


@router.post("/disconnect", summary="断开Telegram连接")
async def disconnect_telegram():
    """
    主动断开Telegram连接
    - 安全释放资源
    - 返回断开时间
    """
    try:
        await tg_manager.disconnect()
        return {
            "status": "success",
            "message": "Telegram连接已断开",
            "disconnect_time": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "DISCONNECT_FAILED",
                "message": str(e),
                "solution": "请尝试强制重启服务"
            }
        )


@router.post("/logout", summary="退出登录")
async def logout():
    try:
        if await tg_manager.logout():
            return {"status": "退出登录成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Logout failed: {e}")
