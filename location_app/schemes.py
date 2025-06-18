from pydantic import BaseModel

class CityOut(BaseModel):
    id: int
    name: str
    oblast: str

class StreetOut(BaseModel):
    id: int
    name_ukr: str
    name_eng: str
    city_id: int

class StreetShort(BaseModel):
    id: int
    name_ukr: str
    city_name: str

class StreetWithCity(BaseModel):
    id: int
    name_ukr: str
    city_name: str
