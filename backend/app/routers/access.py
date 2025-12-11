from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.responses import StreamingResponse
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
from app.models import User, Card, AccessLog, Device, VerifyRequest, AccessLogRead, Admin
from app.routers.devices import verify_token
from app.auth import get_current_admin
import csv
import io

router = APIRouter(prefix="/access", tags=["Access"])

# 刷卡驗證
@router.post("/verify")
async def verify_access(
    req: VerifyRequest, 
    x_device_token: str = Header(..., alias="x-device-token"),
    session: AsyncSession = Depends(get_session)
):
    # 驗證設備
    result = await session.execute(select(Device).where(Device.device_name == req.device_id))
    device = result.scalars().first()
    
    if not device:
        raise HTTPException(status_code=401, detail="Invalid Device ID")

    if not verify_token(x_device_token, device.token):
        print(f"SECURITY WARNING: Invalid token used for device {req.device_id}")
        raise HTTPException(status_code=401, detail="Invalid Device Token")
    
    if not device.is_active:
        raise HTTPException(status_code=403, detail="Device is disabled")

    # 驗證使用者
    card_result = await session.execute(select(Card).where(Card.uid == req.card_uid))
    card = card_result.scalars().first()
    
    access_granted = False
    message = "Access Denied"
    user_id = None
    user = None
    log_status = "DENIED"

    if card and card.is_active:
        user_res = await session.execute(select(User).where(User.id == card.user_id))
        user = user_res.scalars().first()
        
        if user:
            user_id = user.id
            if user.is_active:
                await session.refresh(user, ["accessible_devices"])
                if device in user.accessible_devices:
                    access_granted = True
                    message = f"Welcome, {user.name}"
                    log_status = "SUCCESS"
                else:
                    message = "No Permission for this door"
                    log_status = "DENIED_DEVICE"
            else:
                message = "User Inactive"
                log_status = "DENIED_USER_INACTIVE"
        else:
            message = "Card has no owner"
            log_status = "UNKNOWN_OWNER"
    else:
        message = "Unknown Card"
        log_status = "UNKNOWN_CARD"

    log = AccessLog(
        user_id=user_id,
        card_uid=req.card_uid,
        method="RFID",
        status=log_status,
        details=f"Device: {req.device_id} | {message}"
    )
    session.add(log)
    await session.commit()

    return {
        "access": access_granted,
        "message": message,
        "user_name": user.name if user else "Unknown",
        "student_id": user.student_id if user else ""
    }

# 讀取 Log
@router.get("/logs", response_model=list[AccessLogRead])
async def read_logs(
    limit: int = 50, 
    session: AsyncSession = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin)
):
    statement = select(AccessLog).order_by(AccessLog.timestamp.desc()).limit(limit)
    result = await session.execute(statement)
    logs = result.scalars().all()
    
    response_data = []
    for log in logs:
        user_name = "Unknown"
        if log.user_id:
            u = await session.get(User, log.user_id)
            if u: user_name = u.name
        
        response_data.append(AccessLogRead(
            **log.model_dump(), user_name=user_name
        ))
    return response_data

# 匯出 CSV
@router.get("/export")
async def export_logs(
    session: AsyncSession = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin)
):
    statement = select(AccessLog).order_by(AccessLog.timestamp.desc())
    result = await session.execute(statement)
    logs = result.scalars().all()

    user_result = await session.execute(select(User))
    users = user_result.scalars().all()
    user_map = {u.id: u.name for u in users}

    output = io.StringIO()
    output.write('\ufeff') 
    
    writer = csv.writer(output)
    writer.writerow(['ID', '時間', '姓名', '卡號', '方式', '結果', '詳細內容'])

    for log in logs:
        user_name = user_map.get(log.user_id, "Unknown") if log.user_id else "Unknown"
        writer.writerow([
            log.id,
            log.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            user_name,
            log.card_uid,
            log.method,
            log.status,
            log.details
        ])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=access_logs.csv"}
    )
