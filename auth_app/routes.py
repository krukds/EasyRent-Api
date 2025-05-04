import datetime
import os
import shutil
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import ValidationError
from sqlalchemy import select, func
from sqlalchemy.orm import Query, joinedload
from starlette import status
from starlette.status import HTTP_404_NOT_FOUND

from db import UserModel
from db.models import ReviewModel
from db.services import UserService
from db.services.main_services import ReviewService
from utils import datetime_now
from .deps import get_current_active_user
from .schemes import TokenResponse, SignupPayload, UserResponse, UserPayload
from .utils import create_user_session, build_user_response

UPLOAD_DIR = Path("static/user_photos")
router = APIRouter(
    prefix="/auth",
    tags=["Authorization"]
)


@router.post("/login")
async def login(
    payload: OAuth2PasswordRequestForm = Depends()
) -> TokenResponse:
    if "@" in payload.username:
        filter_field = UserModel.email == payload.username
    else:
        filter_field = UserModel.phone == payload.username

    user = await UserService.select_one(
        filter_field,
        UserModel.password == payload.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )

    session = await create_user_session(user.id)

    return TokenResponse(
        access_token=session.access_token,
        refresh_token=None
    )

@router.post("/signup")
async def signup(
        payload: SignupPayload
) -> TokenResponse:
    # Перевірка email
    user = await UserService.select_one(
        UserModel.email == payload.email
    )
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This email is already used"
        )

    # ✅ Перевірка телефону
    existing_user_by_phone = await UserService.select_one(
        UserModel.phone == payload.phone
    )
    if existing_user_by_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This phone number is already used"
        )

    try:
        user = UserModel(
            **payload.model_dump(),
            photo_url=None,
            role=1,
            is_active=True
        )
        await UserService.save(user)

    except ValidationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect payload data"
        )

    session = await create_user_session(user.id)

    return TokenResponse(
        access_token=session.access_token,
        refresh_token=None
    )


@router.get("/me", response_model=UserResponse)
async def get_me(user: UserModel = Depends(get_current_active_user)) -> UserResponse:
    # 🎯 Отримуємо середній рейтинг як власника
    avg_rating_query = (
        select(func.avg(ReviewModel.rating))
        .where(ReviewModel.user_id  == user.id)
    )
    result = await ReviewService.execute(avg_rating_query)
    average_rating = result[0] if result else None
    
    return UserResponse(
        **user.__dict__,
        average_rating=round(average_rating, 2) if average_rating else None
    )

@router.get("/id")
async def get_user_by_id(
        user_id: int
) -> UserResponse:
    user: UserModel = await UserService.select_one(
        UserModel.id == user_id
    )
    if not user:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="No user with this id found")

    return UserResponse(**user.__dict__)


@router.get("/email")
async def get_user_by_email(
        email: str
) -> UserResponse:
    user: UserModel = await UserService.select_one(
        UserModel.email == email
    )
    if not user:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="No user with this email found")

    return UserResponse(**user.__dict__)


@router.delete("/id")
async def delete_user_by_id(
        user_id: int
):
    await UserService.delete(id=user_id)

    return {"status": "ok"}


@router.put("/id")
async def update_user_by_id(
        user_id: int,
        payload: UserPayload
) -> UserResponse:
    # Отримуємо користувача
    user: UserModel = await UserService.select_one(
        UserModel.id == user_id
    )
    if not user:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="No user with this id found")

    # Оновлюємо поля, якщо вони були передані
    for key, value in payload.model_dump().items():
        if value is not None:  # Перевіряємо, чи передано значення
            setattr(user, key, value)
        elif key == 'photo_url' and value is None:  # Якщо передано null для фото
            setattr(user, key, None)  # Явно обираємо null для фото

    await UserService.save(user)

    return await build_user_response(user)

@router.get("", response_model=List[UserResponse])
async def get_all_users(
        # location_id: int = None,
        # department_id: int = None
) -> List[UserResponse]:
    base_query = select(UserModel)

    # if location_id is not None:
    #     base_query = base_query.where(UserModel.location_id == location_id)
    #
    # if department_id is not None:
    #     base_query = base_query.where(UserModel.department_id == department_id)

    users = await UserService.execute(base_query)


    if not users:
        raise HTTPException(status_code=404, detail="No users found")

    return users
    # return [
    #     UserDetailResponse(
    #         id=user.id,
    #         email=user.email,
    #         password=user.password,
    #         first_name=user.first_name,
    #         last_name=user.last_name,
    #         phone=user.phone,
    #         location=user.location.name,
    #         department=user.department.name
    #     )
    #     for user in users
    # ]





@router.post("/upload-photo", response_model=UserResponse)
async def upload_user_photo(
    file: UploadFile = File(...),
    user: UserModel = Depends(get_current_active_user)
):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    # Збереження файлу
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Оновлення photo_url користувача
    user.photo_url = file.filename
    updated_user = await UserService.save(user)

    return UserResponse(**updated_user.__dict__)