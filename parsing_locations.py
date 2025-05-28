import xml.etree.ElementTree as ET
import psycopg2
from transliterate import translit
import re

# Відображення типів вулиць
street_type_map = {
    'вул.': 'Street', 'вул': 'Street',
    'пров.': 'Lane', 'пров': 'Lane',
    'просп.': 'Avenue', 'просп': 'Avenue',
    'бул.': 'Boulevard', 'бул': 'Boulevard',
    'пл.': 'Square', 'пл': 'Square',
    'туп.': 'Dead End', 'туп': 'Dead End',
    'наб.': 'Quay',
    'шосе': 'Highway',
    'дор.': 'Road', 'дор': 'Road',
}

# Порядкові числівники → 1-й → 1st
def ordinal_suffix(n: int) -> str:
    if 10 <= n % 100 <= 20:
        return f"{n}th"
    else:
        return f"{n}{['th', 'st', 'nd', 'rd', 'th', 'th', 'th', 'th', 'th', 'th'][n % 10]}"

def convert_ordinals(text: str) -> str:
    text = re.sub(r'\b(\d+)\s*[-–]?\s*y\b', lambda m: ordinal_suffix(int(m.group(1))), text)
    text = re.sub(r'\b(\d+)\s*[-–]?\s*[аaя]\b', lambda m: ordinal_suffix(int(m.group(1))), text)
    return text

def translate_street_name(ukr_name: str) -> str:
    for ukr_prefix, eng in street_type_map.items():
        pattern = rf"^{re.escape(ukr_prefix)}\s*"
        if re.match(pattern, ukr_name, flags=re.IGNORECASE):
            name_core = re.sub(pattern, '', ukr_name, flags=re.IGNORECASE).strip()
            transliterated = translit(name_core, 'uk', reversed=True).replace("'", "").replace("j", "y")
            return convert_ordinals(f"{transliterated} {eng}")
    transliterated = translit(ukr_name, 'uk', reversed=True).replace("'", "").replace("j", "y")
    return convert_ordinals(transliterated)

def translate_city_name(ukr_name: str) -> str:
    ukr_name = ukr_name.strip()
    ukr_name = re.sub(
        r'^(м\.|с\.|смт\.|сщ\.|с-ще\.|сщ/рада\.?|рада\.?|сільрада\.?|місто|село|селище|пгт)\s*',
        '', ukr_name, flags=re.IGNORECASE
    )
    transliterated = translit(ukr_name, 'uk', reversed=True)
    transliterated = transliterated.replace("'", "").replace("j", "y")
    return transliterated

def translate_oblast_name(ukr_name: str) -> str:
    ukr_name = ukr_name.strip()
    ukr_name = re.sub(r'^м\.', '', ukr_name, flags=re.IGNORECASE)  # прибрати "м." перед Київ, Севастополь
    transliterated = translit(ukr_name, 'uk', reversed=True).replace("'", "").replace("j", "y")
    return transliterated

# --- DB connection ---
conn = psycopg2.connect(
    dbname="EasyRent", user="postgres", password="postgres", host="localhost"
)
cur = conn.cursor()

# --- Parse XML ---
tree = ET.parse('addressData.xml')
root = tree.getroot()

city_cache = {}
batched_streets = []
batch_size = 1000

for record in root.findall('.//RECORD'):
    city_name_ukr = (record.find('CITY_NAME').text or '').strip()
    region_name = (record.find('REGION_NAME').text or '').strip()
    oblast_name = (record.find('OBL_NAME').text or '').strip()
    street_name_ukr = (record.find('STREET_NAME').text or '').strip()

    # Якщо CITY_NAME порожній, а oblast — місто, використовуємо oblast як назву міста
    if not city_name_ukr and oblast_name.lower().startswith("м."):
        city_name_ukr = oblast_name
    elif not city_name_ukr:
        continue

    # Пропустити адміністративні одиниці
    if re.match(r'^(с[\-/\\]?рада\.?|сільрада\.?|рада\.?)', city_name_ukr, re.IGNORECASE):
        print(f"⚠️ Skipped administrative unit: {city_name_ukr}")
        continue

    city_name_eng = translate_city_name(city_name_ukr)

    # Ключ унікальності — name_eng + oblast (без region)
    cache_key = (city_name_eng.lower(), oblast_name.lower())

    if cache_key not in city_cache:
        # Перевірка на існування
        cur.execute("""
            SELECT id FROM cities 
            WHERE LOWER(name_eng) = %s AND LOWER(oblast) = %s
            LIMIT 1
        """, (city_name_eng.lower(), oblast_name.lower()))
        existing_city = cur.fetchone()

        if existing_city:
            city_id = existing_city[0]
            print(f"🔁 Skipped duplicate city: {city_name_ukr} -> {city_name_eng}")
        else:
            cur.execute("""
                INSERT INTO cities (name_ukr, name_eng, region, oblast) 
                VALUES (%s, %s, %s, %s) RETURNING id
            """, (city_name_ukr, city_name_eng, region_name, oblast_name))
            city_id = cur.fetchone()[0]
            print(f"✅ Inserted city: {city_name_ukr} -> {city_name_eng}")
        city_cache[cache_key] = city_id
    else:
        city_id = city_cache[cache_key]

    # Додати вулиці
    if street_name_ukr:
        street_name_eng = translate_street_name(street_name_ukr)
        batched_streets.append((street_name_ukr, street_name_eng, city_id))

        if len(batched_streets) >= batch_size:
            cur.executemany(
                "INSERT INTO streets (name_ukr, name_eng, city_id) VALUES (%s, %s, %s)",
                batched_streets
            )
            print(f"📦 Inserted batch of {len(batched_streets)} streets")
            batched_streets.clear()

# Вставити залишок
if batched_streets:
    cur.executemany(
        "INSERT INTO streets (name_ukr, name_eng, city_id) VALUES (%s, %s, %s)",
        batched_streets
    )
    print(f"📦 Inserted final batch of {len(batched_streets)} streets")

conn.commit()
cur.close()
conn.close()
print("✅ Done")
