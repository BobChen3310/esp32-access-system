from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
from app.models import Device, DeviceReadPublic, DeviceReadWithToken, DeviceBase
import secrets
from pwdlib import PasswordHash

router = APIRouter(prefix="/devices", tags=["Devices"])

password_hash = PasswordHash.recommended()

def get_token_hash(token: str) -> str:
    return password_hash.hash(token)

def verify_token(plain_token: str, hashed_token: str) -> bool:
    return password_hash.verify(plain_token, hashed_token)

# 取得設備列表
@router.get("/", response_model=list[DeviceReadPublic])
async def read_devices(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Device))
    return result.scalars().all()

# 新增設備 (自動生成專屬 MQTT Topic)
@router.post("/", response_model=DeviceReadWithToken)
async def create_device(device_base: DeviceBase, session: AsyncSession = Depends(get_session)):
    # 檢查名稱重複
    existing = await session.execute(select(Device).where(Device.device_name == device_base.device_name))
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="Device name already exists")
    
    # 產生原始 Token
    raw_token = secrets.token_hex(16)
    # 產生雜湊 Token
    hashed_token = get_token_hash(raw_token)
    
    # 自動生成專屬 Topic: door/{設備名稱}
    unique_topic = f"door/{device_base.device_name}"
    
    # 建立 DB 物件
    db_device = Device(
        **device_base.model_dump(), 
        token=hashed_token,
        mqtt_topic=unique_topic
    )
    
    session.add(db_device)
    await session.commit()
    await session.refresh(db_device)
    
    # 回傳
    return DeviceReadWithToken(
        id=db_device.id,
        device_name=db_device.device_name,
        location=db_device.location,
        is_active=db_device.is_active,
        created_at=db_device.created_at,
        token=raw_token
    )

# 修改設備 (連動修改 Topic)
@router.put("/{device_id}", response_model=DeviceReadPublic)
async def update_device(device_id: int, device_data: DeviceBase, session: AsyncSession = Depends(get_session)):
    db_device = await session.get(Device, device_id)
    if not db_device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # 檢查名稱是否與其他設備重複
    if db_device.device_name != device_data.device_name:
        existing = await session.execute(select(Device).where(Device.device_name == device_data.device_name))
        if existing.scalars().first():
            raise HTTPException(status_code=400, detail="Device name already exists")

    # 更新欄位
    db_device.device_name = device_data.device_name
    db_device.location = device_data.location
    db_device.is_active = device_data.is_active
    
    db_device.mqtt_topic = f"door/{device_data.device_name}"
    
    session.add(db_device)
    await session.commit()
    await session.refresh(db_device)
    return db_device

# 刪除設備
@router.delete("/{device_id}")
async def delete_device(device_id: int, session: AsyncSession = Depends(get_session)):
    device = await session.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    await session.delete(device)
    await session.commit()
    return {"ok": True}

# 重設 Token
@router.post("/{device_id}/reset-token", response_model=DeviceReadWithToken)
async def reset_device_token(device_id: int, session: AsyncSession = Depends(get_session)):
    db_device = await session.get(Device, device_id)
    if not db_device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    raw_token = secrets.token_hex(16)
    db_device.token = get_token_hash(raw_token)
    
    session.add(db_device)
    await session.commit()
    await session.refresh(db_device)
    return DeviceReadWithToken(
        id=db_device.id,
        device_name=db_device.device_name,
        location=db_device.location,
        is_active=db_device.is_active,
        created_at=db_device.created_at,
        token=raw_token
    )