from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from dotenv import load_dotenv
import os

load_dotenv()

conf = ConnectionConfig(
    MAIL_USERNAME = os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD"),
    MAIL_FROM = os.getenv("MAIL_FROM"),
    MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME"),
    MAIL_PORT = int(os.getenv("MAIL_PORT")),
    MAIL_SERVER = os.getenv("MAIL_SERVER"),
    
    MAIL_STARTTLS = False,
    MAIL_SSL_TLS = True,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)

async def send_verification_code(email_to: EmailStr, code: str):
    html = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
        <h2 style="color: #2c3e50;">🚪 IoT 門禁系統驗證</h2>
        <p>您好，</p>
        <p>這是您的 Telegram 綁定驗證碼：</p>
        <h1 style="color: #3498db; letter-spacing: 5px; background: #f0f8ff; padding: 10px; text-align: center; border-radius: 5px;">{code}</h1>
        <p style="color: #e74c3c;"><strong>此驗證碼將在 3 分鐘後失效。</strong></p>
    </div>
    """

    message = MessageSchema(
        subject="[IoT門禁] Telegram 綁定驗證碼",
        recipients=[email_to],
        body=html,
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    await fm.send_message(message)