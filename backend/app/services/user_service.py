from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from typing import Optional, List
from app.models.models import User, UserRole
from app.utils.security import get_password_hash, verify_password


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_login(self, login: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.login == login))
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create_user(self, login: str, password: str, role: UserRole = UserRole.ENGINEER) -> User:
        hashed_password = get_password_hash(password)
        user = User(
            login=login,
            password_hash=hashed_password,
            role=role
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def authenticate_user(self, login: str, password: str) -> Optional[User]:
        user = await self.get_user_by_login(login)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        if user.is_blocked:
            return None
        if not user.is_active:
            return None
        return user

    async def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        stmt = update(User).where(User.id == user_id).values(**kwargs)
        await self.db.execute(stmt)
        await self.db.commit()
        return await self.get_user_by_id(user_id)

    async def delete_user(self, user_id: int) -> bool:
        stmt = delete(User).where(User.id == user_id)
        await self.db.execute(stmt)
        await self.db.commit()
        return True

    async def get_all_users(self) -> List[User]:
        result = await self.db.execute(select(User))
        return result.scalars().all()

    async def block_user(self, user_id: int) -> Optional[User]:
        return await self.update_user(user_id, is_blocked=True)

    async def unblock_user(self, user_id: int) -> Optional[User]:
        return await self.update_user(user_id, is_blocked=False)

    async def change_password(self, user_id: int, new_password: str) -> Optional[User]:
        hashed_password = get_password_hash(new_password)
        return await self.update_user(user_id, password_hash=hashed_password)
