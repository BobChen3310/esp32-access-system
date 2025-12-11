import asyncio
import getpass
from sqlmodel import select
from app.database import get_session
from app.models import Admin
from app.auth import get_password_hash

async def create_admin_interactive():
    print("=== 建立後台管理員帳號 (CLI 模式) ===")
    
    # 輸入帳號
    username = input("請輸入帳號 (Username): ").strip()
    if not username:
        print("錯誤: 帳號不能為空")
        return

    # 輸入密碼
    password = getpass.getpass("請輸入密碼 (Password): ").strip()
    if not password:
        print("錯誤: 密碼不能為空")
        return
        
    confirm_password = getpass.getpass("請再次輸入密碼 (Confirm): ").strip()
    if password != confirm_password:
        print("錯誤: 兩次輸入的密碼不符")
        return

    # 連線資料庫並寫入
    print(f"\n正在連線資料庫並建立使用者 [{username}] ...")
    
    # 手動取得 Session
    async for session in get_session():
        # 檢查帳號是否重複
        statement = select(Admin).where(Admin.username == username)
        result = await session.execute(statement)
        existing = result.scalars().first()

        if existing:
            print(f"錯誤: 帳號 '{username}' 已經存在！")
            return

        # 建立新管理員
        new_admin = Admin(
            username=username,
            hashed_password=get_password_hash(password)
        )
        session.add(new_admin)
        await session.commit()
        
        print(f"成功！管理員 '{username}' 已建立。")
        return

if __name__ == "__main__":
    try:
        asyncio.run(create_admin_interactive())
    except KeyboardInterrupt:
        print("\n已取消操作。")
    except Exception as e:
        print(f"\n發生未預期的錯誤: {e}")