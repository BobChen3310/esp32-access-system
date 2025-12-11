import asyncio
from sqlmodel import select
from app.database import get_session
from app.models import Admin
from app.auth import get_password_hash

async def reset_password(username, new_password):
    # 手動取得 Session
    async for session in get_session():
        print(f"正在搜尋使用者: {username} ...")
        statement = select(Admin).where(Admin.username == username)
        result = await session.execute(statement)
        admin = result.scalars().first()

        if not admin:
            print(f"找不到使用者: {username}")
            return

        print(f"找到使用者，正在重設密碼...")
        admin.hashed_password = get_password_hash(new_password)
        session.add(admin)
        await session.commit()
        print(f"🎉 密碼已成功重設為: {new_password}")
        return

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("用法: uv run reset_admin.py <帳號> <新密碼>")
        print("範例: uv run reset_admin.py admin 123456")
    else:
        user = sys.argv[1]
        pwd = sys.argv[2]
        asyncio.run(reset_password(user, pwd))