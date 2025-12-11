import os
import logging
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# 載入環境變數
load_dotenv()
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BACKEND_URL = os.getenv("BACKEND_API_URL")
BOT_SECRET = os.getenv("BOT_API_SECRET")

# Logging 設定
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Conversation 狀態常數
ASK_EMAIL, ASK_CODE = range(2)
waiting_for_code = set()

# 後端 API 呼叫
def call_backend(endpoint: str, data: dict):
    url = f"{BACKEND_URL}/{endpoint}"
    headers = {"Content-Type": "application/json", "x-bot-token": BOT_SECRET}
    try:
        resp = requests.post(url, json=data, headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        return {"success": False, "message": f"Server Error: {resp.status_code}"}
    except Exception as e:
        return {"success": False, "message": f"連線失敗: {e}"}

# /start /help
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚪 <b>IoT 門禁機器人</b>\n\n"
        "指令列表：\n"
        "/login - 開始綁定帳號\n"
        "/code - 輸入驗證碼\n"
        "/unlock - 遠端開門\n"
        "/logout - 解除綁定\n"
        "/help - 顯示指令列表",
        parse_mode=ParseMode.HTML,
    )

# /login → ASK_EMAIL
async def login_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.message.chat_id)
    status = call_backend("check-status", {"telegram_id": telegram_id})
    if status.get("is_logged_in"):
        await update.message.reply_text(status.get("message"))
        return ConversationHandler.END
    await update.message.reply_text("請輸入您的 Email：")
    return ASK_EMAIL

# 接收 Email
async def login_receive_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text.strip()
    if email.startswith("/"):
        await update.message.reply_text("操作已取消")
        return ConversationHandler.END
    telegram_id = str(update.message.chat_id)
    res = call_backend("request-code", {"email": email, "telegram_id": telegram_id})
    if res.get("success"):
        waiting_for_code.add(telegram_id)
    await update.message.reply_text(res.get("message"))
    return ConversationHandler.END

# /code → ASK_CODE
async def code_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.message.chat_id)
    status = call_backend("check-status", {"telegram_id": telegram_id})
    if status.get("is_logged_in"):
        await update.message.reply_text(status.get("message"))
        return ConversationHandler.END
    if telegram_id not in waiting_for_code:
        await update.message.reply_text("您尚未申請驗證碼，請先執行 /login")
        return ConversationHandler.END
    await update.message.reply_text("請輸入 6 位數驗證碼：")
    return ASK_CODE

# 接收驗證碼
async def verify_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    telegram_id = str(update.message.chat_id)
    if code.startswith("/"):
        await update.message.reply_text("操作已取消")
        return ConversationHandler.END
    res = call_backend("verify-code", {"code": code, "telegram_id": telegram_id})
    if res.get("success") and telegram_id in waiting_for_code:
        waiting_for_code.remove(telegram_id)
    await update.message.reply_text(res.get("message"))
    return ConversationHandler.END

# /unlock
async def unlock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.message.chat_id)
    res = call_backend("unlock", {"telegram_id": telegram_id})
    await update.message.reply_text(res.get("message"))

# /logout
async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.message.chat_id)
    res = call_backend("logout", {"telegram_id": telegram_id})
    if telegram_id in waiting_for_code:
        waiting_for_code.remove(telegram_id)
    await update.message.reply_text(res.get("message"))

# 未知指令
async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("未知指令，請輸入 /help 查看可用指令。")

# 主程式入口
def main():
    if not TG_TOKEN:
        raise RuntimeError("未讀取到 TELEGRAM_BOT_TOKEN")
    application = ApplicationBuilder().token(TG_TOKEN).build()
    login_conv = ConversationHandler(
        entry_points=[CommandHandler("login", login_command)],
        states={
            ASK_EMAIL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, login_receive_email)
            ],
        },
        fallbacks=[],
    )
    code_conv = ConversationHandler(
        entry_points=[CommandHandler("code", code_command)],
        states={
            ASK_CODE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, verify_code)
            ],
        },
        fallbacks=[],
    )
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", start))
    application.add_handler(login_conv)
    application.add_handler(code_conv)
    application.add_handler(CommandHandler("unlock", unlock))
    application.add_handler(CommandHandler("logout", logout))
    application.add_handler(MessageHandler(filters.ALL, unknown))
    print("Bot Client Running...")
    application.run_polling()

if __name__ == "__main__":
    main()