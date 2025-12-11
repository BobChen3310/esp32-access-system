from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
from app.models import User, Card, Device
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/users", tags=["Users"])

class UserReadWithDetails(BaseModel):
    id: int
    student_id: str
    name: str
    email: Optional[str] = None
    is_active: bool
    card_uid: Optional[str] = None
    accessible_device_ids: List[int] = [] # 回傳給前端，用於顯示已選設備
    accessible_device_names: List[str] = [] # 用於列表顯示設備名稱

class UserCreateUpdate(BaseModel):
    student_id: str
    name: str
    email: Optional[str] = None # Email
    is_active: bool
    card_uid: Optional[str] = None
    accessible_device_ids: List[int] = [] # 接收前端傳來的設備 ID 列表

# 取得所有學生 (含詳細資料)
@router.get("/", response_model=List[UserReadWithDetails])
async def read_users(session: AsyncSession = Depends(get_session)):
    # 預先載入 cards 和 accessible_devices
    statement = select(User).options(selectinload(User.cards), selectinload(User.accessible_devices))
    result = await session.execute(statement)
    users = result.scalars().all()
    
    response_data = []
    for user in users:
        current_card_uid = user.cards[0].uid if user.cards else None
        
        # 整理設備 ID 與 名稱
        device_ids = [d.id for d in user.accessible_devices]
        device_names = [d.device_name for d in user.accessible_devices]

        response_data.append(UserReadWithDetails(
            id=user.id,
            student_id=user.student_id,
            name=user.name,
            email=user.email,
            is_active=user.is_active,
            card_uid=current_card_uid,
            accessible_device_ids=device_ids,
            accessible_device_names=device_names
        ))
    return response_data

# 新增學生
@router.post("/", response_model=UserReadWithDetails)
async def create_user(user_in: UserCreateUpdate, session: AsyncSession = Depends(get_session)):
    # 檢查學號重複
    existing_user = await session.execute(select(User).where(User.student_id == user_in.student_id))
    if existing_user.scalars().first():
        raise HTTPException(status_code=400, detail="Student ID already exists")
    
    # 檢查卡號重複
    if user_in.card_uid:
        existing_card = await session.execute(select(Card).where(Card.uid == user_in.card_uid))
        if existing_card.scalars().first():
            raise HTTPException(status_code=400, detail="Card UID already exists")

    # 建立 User 物件
    db_user = User(
        student_id=user_in.student_id,
        name=user_in.name,
        email=user_in.email,
        is_active=user_in.is_active
    )
    
    # 處理設備關聯
    if user_in.accessible_device_ids:
        # 查詢所有對應的 Device 物件
        for dev_id in user_in.accessible_device_ids:
            device = await session.get(Device, dev_id)
            if device:
                db_user.accessible_devices.append(device)

    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)

    # 建立 Card
    if user_in.card_uid:
        new_card = Card(uid=user_in.card_uid, user_id=db_user.id, is_active=True)
        session.add(new_card)
        await session.commit()
        
    # 重新載入以獲取完整關聯資料
    await session.refresh(db_user, ["cards", "accessible_devices"])

    return UserReadWithDetails(
        id=db_user.id,
        student_id=db_user.student_id,
        name=db_user.name,
        email=db_user.email,
        is_active=db_user.is_active,
        card_uid=user_in.card_uid,
        accessible_device_ids=[d.id for d in db_user.accessible_devices],
        accessible_device_names=[d.device_name for d in db_user.accessible_devices]
    )

# 更新學生
@router.put("/{user_id}", response_model=UserReadWithDetails)
async def update_user(user_id: int, user_in: UserCreateUpdate, session: AsyncSession = Depends(get_session)):
    # 載入 User 及其關聯
    result = await session.execute(
        select(User)
        .options(selectinload(User.cards), selectinload(User.accessible_devices))
        .where(User.id == user_id)
    )
    db_user = result.scalars().first()
    
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 更新基本資料
    db_user.student_id = user_in.student_id
    db_user.name = user_in.name
    db_user.email = user_in.email
    db_user.is_active = user_in.is_active
    
    # 更新設備權限 (先清空再重加)
    db_user.accessible_devices.clear()
    if user_in.accessible_device_ids:
        for dev_id in user_in.accessible_device_ids:
            device = await session.get(Device, dev_id)
            if device:
                db_user.accessible_devices.append(device)
    
    # 更新卡片 (保持一人一卡邏輯)
    current_card = db_user.cards[0] if db_user.cards else None
    
    if user_in.card_uid:
        if current_card:
            if current_card.uid != user_in.card_uid:
                existing = await session.execute(select(Card).where(Card.uid == user_in.card_uid))
                if existing.scalars().first():
                    raise HTTPException(status_code=400, detail="Card UID already exists")
                current_card.uid = user_in.card_uid
        else:
            existing = await session.execute(select(Card).where(Card.uid == user_in.card_uid))
            if existing.scalars().first():
                raise HTTPException(status_code=400, detail="Card UID already exists")
            new_card = Card(uid=user_in.card_uid, user_id=db_user.id, is_active=True)
            session.add(new_card)
    else:
        if current_card:
            await session.delete(current_card)

    try:
        await session.commit()
        await session.refresh(db_user)
    except Exception:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Update failed")
    
    return UserReadWithDetails(
        id=db_user.id,
        student_id=db_user.student_id,
        name=db_user.name,
        email=db_user.email,
        is_active=db_user.is_active,
        card_uid=user_in.card_uid,
        accessible_device_ids=[d.id for d in db_user.accessible_devices],
        accessible_device_names=[d.device_name for d in db_user.accessible_devices]
    )

# 刪除學生
@router.delete("/{user_id}")
async def delete_user(user_id: int, session: AsyncSession = Depends(get_session)):
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    cards_result = await session.execute(select(Card).where(Card.user_id == user_id))
    for card in cards_result.scalars().all():
        await session.delete(card)

    await session.delete(user)
    await session.commit()
    return {"ok": True}