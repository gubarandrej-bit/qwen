from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database.database import get_db
from app.services.user_service import UserService
from app.schemas.schemas import UserResponse, UserUpdate, UserRole
from app.routers.auth import require_admin, get_current_user
from app.models.models import User

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=List[UserResponse])
async def get_all_users(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
):
    user_service = UserService(db)
    users = await user_service.get_all_users()
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_service = UserService(db)
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Users can view their own info, admins can view all
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
):
    user_service = UserService(db)
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = {}
    if user_data.password is not None:
        update_data["password_hash"] = user_service.db  # Will be hashed in service
    if user_data.role is not None:
        update_data["role"] = user_data.role
    if user_data.is_active is not None:
        update_data["is_active"] = user_data.is_active
    if user_data.is_blocked is not None:
        update_data["is_blocked"] = user_data.is_blocked
    
    updated_user = await user_service.update_user(user_id, **update_data)
    return updated_user


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
):
    user_service = UserService(db)
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Prevent deleting yourself
    if admin.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    await user_service.delete_user(user_id)
    return {"message": "User deleted successfully"}


@router.post("/{user_id}/block")
async def block_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
):
    user_service = UserService(db)
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if admin.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot block yourself")
    await user_service.block_user(user_id)
    return {"message": "User blocked successfully"}


@router.post("/{user_id}/unblock")
async def unblock_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
):
    user_service = UserService(db)
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await user_service.unblock_user(user_id)
    return {"message": "User unblocked successfully"}


@router.post("/{user_id}/change-password")
async def change_password(
    user_id: int,
    new_password: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_service = UserService(db)
    # Users can change their own password, admins can change any
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    await user_service.change_password(user_id, new_password)
    return {"message": "Password changed successfully"}
