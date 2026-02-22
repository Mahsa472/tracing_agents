from graphlib import TopologicalSorter
import requests

from langchain.tools import tool


@tool
def get_weather(city: str) -> str:
    """Get the weather in a given city using Open-Meteo API."""

    import urllib.parse

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


    # Get current weather using coordinates
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

    result = {
        "city": f"{city_name}, {country}" if country else city_name,
        "temperature": f"{current.get('temperature_2m', 'N/A')}°C",
        "humidity": f"{current.get('relative_humidity_2m', 'N/A')}%",
        "weather": weather_description,
        "wind_speed": f"{current.get('wind_speed_10m', 'N/A')} km/h",
        "precipitation": f"{current.get('precipitation', 0)} mm",
        "time": current.get("time", "N/A")
    }
    return str(result)


