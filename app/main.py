import uvicorn
from fastapi import FastAPI
from .routers import dialog_router, message_router, media_router, telegram_client_router
from .services import TelegramClientManager
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Telegram Crawler API", debug=True)

app.include_router(dialog_router)
app.include_router(message_router)
app.include_router(media_router)

app.include_router(telegram_client_router)

# 配置允许跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 你可以指定前端地址比如 "http://localhost:5173"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
def root():
    return {"message": "Welcome to Telegram Crawler API"}