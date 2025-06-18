from fastapi import APIRouter, Query, Depends, HTTPException
from typing import List
import asyncpg
from sqlalchemy import select, func, tuple_
from sqlalchemy.orm import joinedload

from db.models import CityModel, StreetModel
from db.services.main_services import CityService, StreetService
from location_app.data import TOP_CITIES_FULL_EN, TOP_CITIES_FULL
from location_app.schemes import CityOut, StreetOut, StreetShort, StreetWithCity

router = APIRouter(prefix="/location", tags=["Location"])

@router.get("/cities-ukr", response_model=List[CityOut])
async def get_cities_ukr(q: str = Query("", max_length=50)):
    if not q.strip():
        names = [item["name"] for item in TOP_CITIES_FULL]
        oblasts = [item["oblast"] for item in TOP_CITIES_FULL]
        query = (
            select(CityModel)
            .where(
                tuple_(CityModel.name_ukr, CityModel.oblast)
                .in_(list(zip(names, oblasts)))
            )
            .order_by(CityModel.name_ukr)
        )
        result = await CityService.execute(query)
        return [{"id": row.id, "name": row.name_ukr, "oblast": row.oblast} for row in result]

    query = (
        select(CityModel)
        .where(CityModel.name_ukr.ilike(f"{q.lower()}%"))
        .order_by(CityModel.name_ukr)
        .limit(100)
    )
    result = await CityService.execute(query)
    return [{"id": row.id, "name": row.name_ukr, "oblast": row.oblast} for row in result]

@router.get("/cities-ukr/{city_id}/streets", response_model=List[StreetShort])
async def get_streets(
    city_id: int,
    q: str = Query("", max_length=50)
):
    city = await CityService.select_one(id=city_id)
    if not city:
        raise HTTPException(status_code=404, detail="City with specified oblast not found")

    if q.strip():
        cleaned_name = func.regexp_replace(StreetModel.name_ukr, r'^(вул\.|пров\.)\s*', '', 'i')
        rows = await StreetService.select(
            cleaned_name.ilike(f"{q.lower()}%"),
            city_id=city_id,
            order_by="name_ukr"
        )
    else:
        rows = await StreetService.select(city_id=city_id, order_by="name_ukr")

    return [StreetShort(id=row.id, name_ukr=row.name_ukr, city_name=city.name_ukr) for row in rows]

@router.get("/streets", response_model=List[StreetWithCity])
async def get_streets_ukr(q: str = Query("", max_length=50)):
    if q.strip():
        cleaned_name = func.regexp_replace(StreetModel.name_ukr, r'^(вул\.|пров\.)\s*', '', 'i')

        query = (
            select(StreetModel)
            .join(CityModel, CityModel.id == StreetModel.city_id)
            .options(joinedload(StreetModel.city))
            .where(cleaned_name.ilike(f"{q.lower()}%"))
            .order_by(CityModel.name_ukr, StreetModel.name_ukr)
            .limit(100)
        )

        rows = await StreetService.execute(query)

        return [
            {
                "id": street.id,
                "name_ukr": street.name_ukr,
                "city_name": street.city.name_ukr if street.city else None
            }
            for street in rows
        ]

    return []


@router.get("/street/{street_id}", response_model=StreetOut)
async def get_street_by_id(street_id: int):
    query = (
        select(StreetModel)
        .options(
            joinedload(StreetModel.city)
        )
        .where(StreetModel.id == street_id)
    )

    result = await StreetService.execute(query)
    street = result[0] if result else None

    if not street:
        raise HTTPException(status_code=404, detail="Street not found")

    return street

@router.get("/city/{city_id}", response_model=CityOut)
async def get_city_by_id(city_id: int):
    query = (
        select(CityModel)
        .where(CityModel.id == city_id)
    )

    result = await CityService.execute(query)
    city = result[0] if result else None

    if not city:
        raise HTTPException(status_code=404, detail="City not found")

    return {
            "id": city.id,
            "name": city.name_ukr,
            "oblast": city.oblast
        }