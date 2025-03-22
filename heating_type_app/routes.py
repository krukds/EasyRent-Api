from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from db.models import HeatingTypeModel
from db.services.main_services import HeatingTypeService
from .schemes import HeatingTypeResponse
from typing import List

router = APIRouter(
    prefix="/heating-types",
    tags=["Heating Types"]
)

@router.get("", response_model=List[HeatingTypeResponse])
async def get_all_heating_types():
    query = select(HeatingTypeModel)
    heating_types = await HeatingTypeService.execute(query)

    return [
        HeatingTypeResponse(id=ht.id, name=ht.name)
        for ht in heating_types
    ]
