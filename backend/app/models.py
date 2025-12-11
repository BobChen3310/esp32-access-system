from typing import Optional, List
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship

# 多對多關聯表
class UserDeviceLink(SQLModel, table=True):
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", primary_key=True)
    device_id: Optional[int] = Field(default=None, foreign_key="device.id", primary_key=True)

# Admin
class Admin(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str

# Device
class DeviceBase(SQLModel):
    device_name: str = Field(index=True, unique=True)
    location: Optional[str] = None
    is_active: bool = Field(default=True)

class Device(DeviceBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    token: str = Field(index=True, unique=True)
    mqtt_topic: str = Field(default="door/control") # MQTT 主題
    created_at: datetime = Field(default_factory=datetime.now)
    
    allowed_users: List["User"] = Relationship(back_populates="accessible_devices", link_model=UserDeviceLink)

class DeviceReadPublic(DeviceBase):
    id: int
    created_at: datetime

class DeviceReadWithToken(DeviceBase):
    id: int
    token: str
    created_at: datetime

# User
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: str = Field(index=True, unique=True)
    name: str
    email: Optional[str] = Field(default=None, index=True)
    telegram_id: Optional[str] = Field(default=None)
    
    # 驗證碼欄位
    verification_code: Optional[str] = Field(default=None)
    code_expires_at: Optional[datetime] = Field(default=None)
    
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)
    
    cards: List["Card"] = Relationship(back_populates="owner")
    accessible_devices: List[Device] = Relationship(back_populates="allowed_users", link_model=UserDeviceLink)

# Card
class Card(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    uid: str = Field(index=True, unique=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    is_active: bool = Field(default=True)
    owner: Optional[User] = Relationship(back_populates="cards")

# AccessLog
class AccessLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.now)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    card_uid: Optional[str] = None
    method: str
    status: str
    details: Optional[str] = None

# API Models
class VerifyRequest(SQLModel):
    card_uid: str
    device_id: str

class AccessLogRead(SQLModel):
    id: int
    timestamp: datetime
    card_uid: Optional[str]
    method: str
    status: str
    details: Optional[str]
    user_name: Optional[str] = "Unknown"