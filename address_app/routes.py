from fastapi import APIRouter, Query
from typing import List

from address_app.deps import extract_cities, extract_streets, normalize_street_name

router = APIRouter(prefix="/location", tags=["Location"])

@router.get("/cities", response_model=List[str])
async def get_cities(q: str = Query("")):
    if not q.strip():
        # Повертаємо популярні міста, якщо фільтр не заданий
        return ["Київ", "Харків", "Львів", "Дніпро", "Одеса", "Запоріжжя", "Івано-Франківськ", "Тернопіль"]

    all_cities = extract_cities("addressData.xml")
    return [city for city in all_cities if city.lower().startswith(q.lower())]



@router.get("/streets", response_model=List[str])
async def get_streets(city: str, q: str = Query("")):
    street_objs = extract_streets("addressData.xml", city)

    if q.strip():
        q_norm = q.lower()
        filtered = [
            s for s in street_objs
            if s["normalized"].startswith(q_norm)
        ]
    else:
        filtered = street_objs

    # Сортуємо по normalized назві
    sorted_result = sorted(filtered, key=lambda s: s["normalized"])
    return [s["original"] for s in sorted_result[:30]]
