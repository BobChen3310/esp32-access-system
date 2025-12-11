from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.database import get_session
from app.models import Admin
from app.auth import verify_password, create_access_token, get_password_hash, get_current_admin
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["Authentication"])

# 修改密碼請求格式
class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

# 登入
@router.post("/login")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_session)):
    statement = select(Admin).where(Admin.username == form_data.username)
    result = await session.execute(statement)
    admin = result.scalars().first()
    
    if not admin or not verify_password(form_data.password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": admin.username})
    return {"access_token": access_token, "token_type": "bearer"}

# 修改密碼
@router.post("/change-password")
async def change_password(
    req: ChangePasswordRequest, 
    current_admin: Admin = Depends(get_current_admin), 
    session: AsyncSession = Depends(get_session)
):
    if not verify_password(req.old_password, current_admin.hashed_password):
        raise HTTPException(status_code=400, detail="舊密碼輸入錯誤")
    
    current_admin.hashed_password = get_password_hash(req.new_password)
    session.add(current_admin)
    await session.commit()
    
    return {"msg": "Password updated successfully"}