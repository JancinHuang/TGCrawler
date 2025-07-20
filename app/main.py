from fastapi import FastAPI
from .routers import dialog_router, message_router, media_router
app = FastAPI(title="Telegram Crawler API")

app.include_router(dialog_router)
app.include_router(message_router)
app.include_router(media_router)


@app.get("/")
def root():
    return {"message": "Welcome to Telegram Crawler API"}
