import xml.etree.ElementTree as ET
import re

def normalize_name(name):
    # Прибирає префікси типу "м.", "с.", "смт." тощо
    return re.sub(r"^(м\.|с\.|смт\.|пгт\.)\s*", "", name.strip(), flags=re.IGNORECASE)

def normalize_street_name(name: str) -> str:
    # Видаляємо тип вулиці (вул., пр., пров., пл. тощо)
    return re.sub(r"^(вул\.|просп\.|пр\.|пров\.|пл\.)\s*", "", name.strip(), flags=re.IGNORECASE)


def clean_street_name(name: str) -> str:
    name = re.sub(r"\s*,?\s*\d[\d/]*.*", "", name).strip()

    if name.lower() in {"вул.", "пр.", "пров.", "пл.", "просп."}:
        return ""

    if len(name) < 5 or not re.search(r"[а-яА-Яіїєґ]", name):
        return ""

    return name

def extract_cities(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    cities = set()

    for record in root.findall("RECORD"):
        city_elem = record.find("CITY_NAME")
        obl_elem = record.find("OBL_NAME")

        city = city_elem.text.strip() if city_elem is not None and city_elem.text else ""
        obl = obl_elem.text.strip() if obl_elem is not None and obl_elem.text else ""

        if city:
            cities.add(normalize_name(city))
        elif obl.startswith("м."):
            cities.add(normalize_name(obl))

    return sorted(cities)


def extract_streets(xml_file, city_name):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    seen = set()
    streets = []

    for record in root.findall("RECORD"):
        city_elem = record.find("CITY_NAME")
        obl_elem = record.find("OBL_NAME")
        street_elem = record.find("STREET_NAME")

        city = city_elem.text.strip() if city_elem is not None and city_elem.text else ""
        obl = obl_elem.text.strip() if obl_elem is not None and obl_elem.text else ""
        street = street_elem.text.strip() if street_elem is not None and street_elem.text else ""

        normalized_city = normalize_name(city) if city else normalize_name(obl) if obl.startswith("м.") else ""

        if normalized_city == city_name and street:
            clean_name = clean_street_name(street)
            if clean_name:
                normalized = normalize_street_name(clean_name).lower()
                # унікальність по повній назві (враховує і провулок, і вулицю)
                if clean_name not in seen:
                    streets.append({
                        "original": clean_name,
                        "normalized": normalized
                    })
                    seen.add(clean_name)

    return streets
