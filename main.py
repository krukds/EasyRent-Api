from contextlib import asynccontextmanager

from fastapi import FastAPI, APIRouter, Depends
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

import admin_app
import auth_app
import favorites_app
import heating_type_app
import listing_app
import listing_status_app
import listing_tag_app
import listing_tag_category_app
import listing_type_app
import location_app
import review_app
import review_tag_app
from services.worker_checking_listing_relevance import worker_checking_listing_relevance
from services.worker_moderate_listings import worker_moderate_listings


@asynccontextmanager
async def lifespan(_: FastAPI):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(worker_checking_listing_relevance, CronTrigger(hour=12, minute=0))
    scheduler.add_job(worker_moderate_listings, IntervalTrigger(seconds=2))
    scheduler.start()
    await worker_checking_listing_relevance()
    yield


app = FastAPI(
    title="EasyRent Api",
    lifespan=lifespan
)


origins = [
    "http://localhost:4200",
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

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
api_router.include_router(favorites_app.router)
api_router.include_router(admin_app.router)
api_router.include_router(location_app.router)
api_router.include_router(listing_status_app.router)
app.include_router(api_router)
app.include_router(secured_router)
