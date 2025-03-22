from contextlib import asynccontextmanager

from fastapi import FastAPI, APIRouter, Depends
from starlette.middleware.cors import CORSMiddleware

import auth_app, listing_app, review_app, review_tag_app, heating_type_app, \
    listing_type_app, listing_tag_category_app, listing_tag_app, subscription_app, \
    favorites_app, admin_app

@asynccontextmanager
async def lifespan(_: FastAPI):
    yield


app = FastAPI(
    title="EasyRent Api",
    lifespan=lifespan
)

# Дозволені origins
origins = [
    "http://localhost:4200",  # Дозволити Angular додаток
]

# Додавання CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Дозволені origins
    allow_credentials=True,
    allow_methods=["*"],  # Дозволити всі методи (GET, POST, PUT, DELETE, і т.д.)
    allow_headers=["*"],  # Дозволити всі заголовки
)

secured_router = APIRouter(
    prefix="/api",
    dependencies=[Depends(auth_app.get_current_active_user)]
)

api_router = APIRouter(
    prefix="/api",
    # dependencies=[Depends(auth_app.auth_secure)]

)
api_router.include_router(auth_app.router)
api_router.include_router(listing_app.router)
api_router.include_router(review_app.router)
api_router.include_router(review_tag_app.router)
api_router.include_router(heating_type_app.router)
api_router.include_router(listing_type_app.router)
api_router.include_router(listing_tag_category_app.router)
api_router.include_router(listing_tag_app.router)
api_router.include_router(subscription_app.router)
api_router.include_router(favorites_app.router)
api_router.include_router(admin_app.router)
app.include_router(api_router)
app.include_router(secured_router)
