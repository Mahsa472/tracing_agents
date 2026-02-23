from pydantic import BaseModel

class WeatherResult(BaseModel):
    city: str
    temperature: float
    humidity: int
    wind_speed: float
    condition: str

class TimeResult(BaseModel):
    city: str
    timezone: str
    date: str
    time_12h: str
    time_24h: str
    day_of_week: str
    utc_offset: str