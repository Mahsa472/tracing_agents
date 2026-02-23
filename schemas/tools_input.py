from pydantic import BaseModel

class WeatherInput(BaseModel):
    city: str

class TimeInput(BaseModel):
    city: str