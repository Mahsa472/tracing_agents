import urllib.parse
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

from langchain.tools import tool

from schemas.tools_input import WeatherInput, TimeInput
from schemas.tools_output import WeatherResult, TimeResult


@tool(args_schema=WeatherInput)
def get_weather(city: str) -> str:
    """Get the weather in a given city using Open-Meteo API."""

    # Get coordinates for the city using geocoding API
    encoded_city = urllib.parse.quote(city)
    geocode_url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded_city}&count=1"

    geocode_response = requests.get(geocode_url, timeout=10)
    geocode_response.raise_for_status()
    geocode_data = geocode_response.json()

    if not geocode_data.get("results") or len(geocode_data["results"]) == 0:
        return f"Error: Could not find coordinates for city: {city}"


    # Get latitude and langitude
    location = geocode_data["results"][0]
    latitude = location["latitude"]
    longitude = location["longitude"]
    city_name = location.get("name", city)
    country = location.get("country", "")


    # Get current weather using coordinates (the api works with coordinates, not city names)
    weather_url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={latitude}&longitude={longitude}&"
        f"current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,precipitation&"
        f"timezone=auto"
    )

    weather_response = requests.get(weather_url, timeout=10)
    weather_response.raise_for_status()
    weather_data = weather_response.json()

    # Format the response
    current = weather_data.get("current", {})


    # Decode weather code
    weather_codes = {
        0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
        45: "Foggy", 48: "Depositing rime fog",
        51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
        56: "Light freezing drizzle", 57: "Dense freezing drizzle",
        61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
        66: "Light freezing rain", 67: "Heavy freezing rain",
        71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
        77: "Snow grains", 80: "Slight rain showers", 81: "Moderate rain showers",
        82: "Violent rain showers", 85: "Slight snow showers", 86: "Heavy snow showers",
        95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
    }

    weather_code = current.get("weather_code", 0)
    weather_description = weather_codes.get(weather_code, "Unknown")

    # Use output schema for validation and serialization
    result = WeatherResult(
        city=f"{city_name}, {country}" if country else city_name,
        temperature=current.get("temperature_2m") or 0.0,
        humidity=int(current.get("relative_humidity_2m") or 0),
        wind_speed=current.get("wind_speed_10m") or 0.0,
        condition=weather_description,
    )
    return result.model_dump_json()


@tool(args_schema=TimeInput)
def get_current_time(city: str) -> str:
    """Get the current time and date for a given city. Uses Open-Meteo so the time is correct for that location."""
    # Get coordinates for the city using Open-Meteo geocoding
    encoded_city = urllib.parse.quote(city)
    geocode_url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded_city}&count=1"

    try:
        geocode_response = requests.get(geocode_url, timeout=10)
        geocode_response.raise_for_status()
        geocode_data = geocode_response.json()
    except requests.RequestException as e:
        return f"Error: Could not find city: {e}"

    if not geocode_data.get("results"):
        return f"Error: Could not find coordinates for city: {city}"

    location = geocode_data["results"][0]
    latitude = location["latitude"]
    longitude = location["longitude"]
    city_name = location.get("name", city)
    country = location.get("country", "")

    # Get local time from Open-Meteo (timezone=auto → current.time is in city's local timezone)
    # API includes current.time when we request any current variable
    time_url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={latitude}&longitude={longitude}&"
        f"current=temperature_2m&timezone=auto"
    )
    try:
        time_response = requests.get(time_url, timeout=10)
        time_response.raise_for_status()
        time_data = time_response.json()
    except requests.RequestException as e:
        return f"Error: Could not get time for city: {e}"

    timezone_name = time_data.get("timezone") or "UTC"
    current_obj = time_data.get("current") or {}
    time_str_iso = current_obj.get("time")

    # Prefer Open-Meteo's current.time (already in local time for this location)
    if time_str_iso:
        try:
            if len(time_str_iso) >= 19:
                dt = datetime.strptime(time_str_iso[:19], "%Y-%m-%dT%H:%M:%S")
            else:
                dt = datetime.strptime(time_str_iso[:16], "%Y-%m-%dT%H:%M")
        except ValueError:
            dt = None
    else:
        dt = None

    # Fallback: use Python + IANA timezone if API didn't give time
    if dt is None:
        try:
            tz = ZoneInfo(timezone_name)
        except Exception:
            tz = ZoneInfo("UTC")
        dt = datetime.now(tz)

    date_str = dt.strftime("%A, %B %d, %Y")
    time_12h = dt.strftime("%I:%M:%S %p")
    time_24h = dt.strftime("%H:%M:%S")
    day_of_week = dt.strftime("%A")
    # Use Open-Meteo's utc_offset_seconds if present, else ZoneInfo
    offset_seconds = time_data.get("utc_offset_seconds")
    if offset_seconds is not None:
        sign = "+" if offset_seconds >= 0 else "-"
        h, r = divmod(abs(offset_seconds), 3600)
        m, _ = divmod(r, 60)
        utc_offset = f"{sign}{h:02d}:{m:02d}"
    else:
        try:
            tz = ZoneInfo(timezone_name) if timezone_name else ZoneInfo("UTC")
            utc_offset = datetime.now(tz).strftime("%z")
            if len(utc_offset) >= 5:
                utc_offset = utc_offset[:3] + ":" + utc_offset[3:5]
        except Exception:
            utc_offset = "N/A"

    result = TimeResult(
        city=f"{city_name}, {country}" if country else city_name,
        timezone=timezone_name,
        date=date_str,
        time_12h=time_12h,
        time_24h=time_24h,
        day_of_week=day_of_week,
        utc_offset=utc_offset or "N/A",
    )
    return result.model_dump_json()