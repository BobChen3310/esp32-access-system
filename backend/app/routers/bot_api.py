import os
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Header, BackgroundTasks
from sqlmodel import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
from app.models import User, Device, AccessLog
from app.email_utils import send_verification_code
from pydantic import BaseModel
import secrets
from datetime import datetime, timedelta
import aiomqtt
import ssl

load_dotenv()

router = APIRouter(prefix="/bot", tags=["Bot Integration"])

BOT_SECRET = os.getenv("BOT_API_SECRET")
MQTT_BROKER = os.getenv("MQTT_BROKER")
MQTT_PORT = int(os.getenv("MQTT_PORT"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")

class BotLoginRequest(BaseModel):
    email: str
    telegram_id: str

class BotVerifyRequest(BaseModel):
    code: str
    telegram_id: str

class BotUnlockRequest(BaseModel):
    telegram_id: str

class BotLogoutRequest(BaseModel):
    telegram_id: str

class BotCheckStatusRequest(BaseModel):
    telegram_id: str

# 驗證 Bot Token
async def verify_bot_token(x_bot_token: str = Header(..., alias="x-bot-token")):
    if x_bot_token != BOT_SECRET:
        raise HTTPException(status_code=403, detail="Invalid Bot Token")

# MQTT 開門函式
async def trigger_mqtt_open(device_topic: str):
    try:
        # 建立 SSL Context
        tls_context = ssl.create_default_context()
        
        async with aiomqtt.Client(
            hostname=MQTT_BROKER, 
            port=MQTT_PORT,
            username=MQTT_USERNAME,
            password=MQTT_PASSWORD,
            tls_context=tls_context # 啟用 TLS
        ) as client:
            await client.publish(device_topic, payload="OPEN")
            print(f"[Backend] MQTT Sent OPEN to {device_topic}")
            return True
    except Exception as e:
        print(f"[Backend] MQTT Error: {e}")
        return False

@router.post("/check-status", dependencies=[Depends(verify_bot_token)])
async def bot_check_status(req: BotCheckStatusRequest, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.telegram_id == req.telegram_id))
    user = result.scalars().first()
    if user:
        return {"is_logged_in": True, "message": f"⚠️ 您已登入為：{user.name}\n若要切換帳號，請先執行 /logout。"}
    return {"is_logged_in": False, "message": "尚未登入"}

@router.post("/request-code", dependencies=[Depends(verify_bot_token)])
async def bot_request_code(req: BotLoginRequest, background_tasks: BackgroundTasks, session: AsyncSession = Depends(get_session)):
    check_login = await session.execute(select(User).where(User.telegram_id == req.telegram_id))
    if check_login.scalars().first():
        return {"success": False, "message": "⚠️ 您已登入囉！"}

    result = await session.execute(select(User).where(User.email == req.email))
    user = result.scalars().first()
    
    if not user:
        return {"success": False, "message": "❌ 找不到此 Email。"}
    
    if user.telegram_id and user.telegram_id != req.telegram_id:
        return {"success": False, "message": "⚠️ 此 Email 已被其他帳號綁定。"}

    code = secrets.token_hex(3).upper()
    user.verification_code = code
    user.code_expires_at = datetime.now() + timedelta(minutes=3)
    session.add(user)
    await session.commit()
    
    background_tasks.add_task(send_verification_code, req.email, code)
    return {"success": True, "message": f"✅ 驗證碼已發送至 {req.email}。\n請在 3 分鐘內輸入: /code 進行驗證。"}

@router.post("/verify-code", dependencies=[Depends(verify_bot_token)])
async def bot_verify_code(req: BotVerifyRequest, session: AsyncSession = Depends(get_session)):
    check_login = await session.execute(select(User).where(User.telegram_id == req.telegram_id))
    if check_login.scalars().first():
        return {"success": False, "message": "⚠️ 您已登入囉！"}

    result = await session.execute(select(User).where(User.verification_code == req.code))
    user = result.scalars().first()
    
    if not user:
        return {"success": False, "message": "❌ 驗證碼錯誤。"}
    if not user.code_expires_at or datetime.now() > user.code_expires_at:
        return {"success": False, "message": "⚠️ 驗證碼已過期，請使用 /login 重新取得驗證碼。"}
    
    user.telegram_id = req.telegram_id
    user.verification_code = None
    user.code_expires_at = None
    session.add(user)
    await session.commit()
    return {"success": True, "message": f"🎉 綁定成功！你好 {user.name}。\n現在你可以使用 /unlock 進行遠端開門。"}

@router.post("/unlock", dependencies=[Depends(verify_bot_token)])
async def bot_unlock(req: BotUnlockRequest, session: AsyncSession = Depends(get_session)):
    statement = select(User).where(User.telegram_id == req.telegram_id).options(selectinload(User.accessible_devices))
    result = await session.execute(statement)
    user = result.scalars().first()
    
    if not user: return {"success": False, "message": "❌ 尚未綁定，請先 /login。"}
    if not user.is_active: return {"success": False, "message": "⛔ 帳號已被停用。"}
    if not user.accessible_devices: return {"success": False, "message": "⚠️ 無任何門禁權限。"}

    target_device = user.accessible_devices[0]
    mqtt_topic = f"door/{target_device.device_name}"
    
    is_sent = await trigger_mqtt_open(mqtt_topic)
    
    if is_sent:
        log = AccessLog(user_id=user.id, method="TELEGRAM", status="SUCCESS", details=f"Remote unlock: {target_device.device_name}")
        session.add(log)
        await session.commit()
        return {"success": True, "message": f"🟢 已發送開門指令至 [{target_device.device_name}]！"}
    else:
        return {"success": False, "message": "❌ MQTT 連線失敗。"}

@router.post("/logout", dependencies=[Depends(verify_bot_token)])
async def bot_logout(req: BotLogoutRequest, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.telegram_id == req.telegram_id))
    user = result.scalars().first()
    if user:
        user.telegram_id = None
        session.add(user)
        await session.commit()
        return {"success": True, "message": "👋 已解除綁定。"}
    return {"success": False, "message": "ℹ️ 尚未登入。"}