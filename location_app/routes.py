from fastapi import APIRouter, Query, Depends, HTTPException
from typing import List
import asyncpg

router = APIRouter(prefix="/location", tags=["Location"])

# 🔧 Підключення до БД
async def get_db():
    return await asyncpg.connect(user='postgres', password='postgres', database='ukraine_locations', host='localhost')

@router.get("/cities", response_model=List[str])
async def get_cities(q: str = Query("", max_length=50), db=Depends(get_db)):
    if not q.strip():
        # Повертаємо хардкодовані топ-міста з областю
        return [
            "Cherkasy (Cherkaska oblast)", "Chernihiv (Chernihivska oblast)", "Chernivtsi (Chernivetska oblast)",
            "Dnipro (Dnipropetrovska oblast)", "Ivano-Frankivsk (Ivano-Frankivska oblast)", "Kharkiv (Kharkivska oblast)",
            "Khmelnytskyy (Khmelnytska oblast)", "Kryvyi Rih (Dnipropetrovska oblast)", "Kyiv (Kyivska oblast)",
            "Lviv (Lvivska oblast)", "Mariupol (Donetska oblast)", "Mykolaiv (Mykolaivska oblast)",
            "Odesa (Odeska oblast)", "Poltava (Poltavska oblast)", "Rivne (Rivnenska oblast)",
            "Sumy (Sumska oblast)", "Ternopil (Ternopilska oblast)", "Vinnytsia (Vinnytska oblast)",
            "Zaporizhzhia (Zaporizka oblast)", "Zhytomyr (Zhytomyrska oblast)"
        ]

    # Пошук по базі
    query = """
        SELECT name_eng, oblast_eng FROM cities
        WHERE LOWER(name_eng) LIKE $1
        ORDER BY name_eng
    """
    rows = await db.fetch(query, f"{q.lower()}%")
    await db.close()
    return [f"{row['name_eng']} ({row['oblast_eng']})" for row in rows]


@router.get("/cities-ukr", response_model=List[str])
async def get_cities_ukr(q: str = Query("", max_length=50), db=Depends(get_db)):
    if not q.strip():
        # Повертаємо хардкодовані топ-міста з областю (українською, впорядковано за алфавітом)
        return [
            "Вінниця (Вінницька обл.)", "Дніпро (Дніпропетровська обл.)", "Житомир (Житомирська обл.)",
            "Запоріжжя (Запорізька обл.)", "Івано-Франківськ (Івано-Франківська обл.)", "Київ (Київська обл.)",
            "Кривий Ріг (Дніпропетровська обл.)", "Львів (Львівська обл.)", "Маріуполь (Донецька обл.)",
            "Миколаїв (Миколаївська обл.)", "Одеса (Одеська обл.)", "Полтава (Полтавська обл.)",
            "Рівне (Рівненська обл.)", "Суми (Сумська обл.)", "Тернопіль (Тернопільська обл.)",
            "Харків (Харківська обл.)", "Хмельницький (Хмельницька обл.)", "Черкаси (Черкаська обл.)",
            "Чернівці (Чернівецька обл.)", "Чернігів (Чернігівська обл.)"
        ]

    query = """
        WITH cleaned_cities AS (
            SELECT 
                REGEXP_REPLACE(name_ukr, '^(м\\.|с\\.|смт\\.|сщ\\.)\\s*', '', 'gi') AS clean_name,
                oblast
            FROM cities
        )
        SELECT clean_name, oblast
        FROM cleaned_cities
        {where_clause}
        ORDER BY clean_name
        LIMIT 100
    """

    if not q.strip():
        sql = query.format(where_clause="")
        rows = await db.fetch(sql)
    else:
        sql = query.format(where_clause="WHERE LOWER(clean_name) LIKE $1")
        rows = await db.fetch(sql, f"{q.lower()}%")

    await db.close()
    return [f"{row['clean_name']} ({row['oblast']})" for row in rows]

@router.get("/streets", response_model=List[str])
async def get_streets(
    city: str = Query(...),
    oblast: str = Query(...),  # додано
    q: str = Query("", max_length=50),
    db=Depends(get_db)
):
    # Шукаємо місто по name_eng + oblast_eng
    city_query = """
        SELECT id FROM cities
        WHERE LOWER(name_eng) = $1 AND LOWER(oblast_eng) = $2
        LIMIT 1
    """
    city_row = await db.fetchrow(city_query, city.lower(), oblast.lower())
    if not city_row:
        raise HTTPException(status_code=404, detail="City with specified oblast not found")

    city_id = city_row["id"]

    # Вулиці для міста
    if q.strip():
        street_query = """
            SELECT name_eng FROM streets
            WHERE city_id = $1 AND LOWER(name_eng) LIKE $2
            ORDER BY name_eng
        """
        rows = await db.fetch(street_query, city_id, f"{q.lower()}%")
    else:
        street_query = """
            SELECT name_eng FROM streets
            WHERE city_id = $1
            ORDER BY name_eng
        """
        rows = await db.fetch(street_query, city_id)

    await db.close()
    return [row["name_eng"] for row in rows]

