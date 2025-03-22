import datetime
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Query, joinedload
from starlette import status
from starlette.status import HTTP_404_NOT_FOUND

from db import UserModel
from db.services import UserService
from utils import datetime_now
from .deps import get_current_active_user
from .schemes import TokenResponse, SignupPayload, UserResponse, UserPayload
from .utils import create_user_session

router = APIRouter(
    prefix="/auth",
    tags=["Authorization"]
)


@router.post("/login")
async def login(
    payload: OAuth2PasswordRequestForm = Depends()
) -> TokenResponse:
    user = await UserService.select_one(
        UserModel.email == payload.username,
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
    user = await UserService.select_one(
        UserModel.email == payload.email
    )
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This email is already used"
        )
    else:
        try:
            user = UserModel(
                **payload.model_dump(),
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


@router.get("/me")
async def get_me(
        user: UserModel = Depends(get_current_active_user)
) -> UserResponse:
    return UserResponse(**user.__dict__)


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
    user: UserModel = await UserService.select_one(
        UserModel.id == user_id
    )
    if not user:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="No user with this id found")

    for key, value in payload.model_dump().items():
        setattr(user, key, value)

    updated_user = await UserService.save(user)

    return UserResponse(**updated_user.__dict__)


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