import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError # Added ZoneInfoNotFoundError back
from google.adk.agents import Agent
import os
import requests
from dotenv import load_dotenv, find_dotenv
from geopy.geocoders import Nominatim # Added geopy import
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable, GeocoderServiceError # Added geopy exceptions
from timezonefinder import TimezoneFinder # Added timezonefinder import

load_dotenv(find_dotenv()) # Load .env file from root_agent directory or project root

# Initialize Geocoder and TimezoneFinder at module level
# IMPORTANT: Nominatim requires a unique user_agent.
# Using "RicoAgent/1.0" as a placeholder.
geolocator = Nominatim(user_agent="RicoAgent/1.0")
tf = TimezoneFinder()

def get_weather(city: str) -> dict:
    """Retrieves the current weather report for a specified city.
    Args:
        city (str): The name of the city for which to retrieve the weather report.
    Returns:
        dict: status and result or error msg.
    """
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return {
            "status": "error",
            "report": "OpenWeather API key not found. Please set OPENWEATHER_API_KEY environment variable."
        }

    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": api_key,
        "units": "metric"  # Or "imperial" for Fahrenheit
    }
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
        data = response.json() # Correctly placed after raise_for_status

        if data.get("cod") != 200 and data.get("cod") != "200": # API can return cod as int or string
            error_message = data.get("message", "Unknown error from OpenWeather API.")
            return {"status": "error", "report": f"API Error for {city}: {error_message}"}

        weather_description = data.get("weather", [{}])[0].get("description", "not available")
        temperature = data.get("main", {}).get("temp", "not available")
        
        report = f"The weather in {city} is {weather_description} with a temperature of {temperature}°C." # Assuming metric
        return {"status": "success", "report": report}

    except requests.exceptions.HTTPError as http_err:
        status_code = http_err.response.status_code if http_err.response is not None else "Unknown"
        if status_code == 401:
             return {"status": "error", "report": f"API Error for {city}: Invalid API key or unauthorized."}
        elif status_code == 404:
             return {"status": "error", "report": f"API Error for {city}: City not found by API endpoint or resource not found."}
        return {"status": "error", "report": f"HTTP error for {city} (Status: {status_code}): {http_err}"}
    except requests.exceptions.ConnectionError as conn_err:
        return {"status": "error", "report": f"Connection error for {city}: {conn_err}"}
    except requests.exceptions.Timeout as timeout_err:
        return {"status": "error", "report": f"Request timed out for {city}: {timeout_err}"}
    except requests.exceptions.RequestException as req_err: # Generic request exception
        return {"status": "error", "report": f"Error fetching weather for {city}: {req_err}"}
    except (KeyError, IndexError, TypeError) as json_err: # Catch errors from unexpected JSON structure
        return {"status": "error", "report": f"Error parsing weather data for {city}: {json_err}"}
    except Exception as e: # Catch-all for any other unexpected error
        return {"status": "error", "report": f"An unexpected error occurred while fetching weather for {city}."}

def get_current_time(city: str) -> dict:
    """
    Retrieves the current time for a specified city using geocoding (Nominatim)
    and timezone lookup (timezonefinder). No API key required.
    Args:
        city (str): The name of the city.
    Returns:
        dict: status and result or error message.
    """
    location = None
    lat, lon = None, None

    try:
        location = geolocator.geocode(city, timeout=10)
        if location:
            lat = location.latitude
            lon = location.longitude
        else:
            return {"status": "error", "report": f"City '{city}' not found or could not be geocoded."}
    except GeocoderTimedOut:
        return {"status": "error", "report": f"Geocoding service timed out for {city}."}
    except (GeocoderUnavailable, GeocoderServiceError) as geo_err:
        return {"status": "error", "report": f"Geocoding service unavailable/error for {city}: {geo_err}"}
    except Exception as e: # Catch-all for any other unexpected geocoding error
        return {"status": "error", "report": f"An unexpected error occurred during geocoding for {city}: {e}"}

    timezone_str = tf.timezone_at(lng=lon, lat=lat)
    if not timezone_str:
        return {
            "status": "error",
            "report": f"Could not determine timezone for {city} (lat: {lat}, lon: {lon})."
        }

    try:
        tz = ZoneInfo(timezone_str)
        now = datetime.datetime.now(tz)
        report = (
            f'The current time in {city} ({timezone_str}) is {now.strftime("%Y-%m-%d %H:%M:%S %Z%z")}'
        )
        return {"status": "success", "report": report}
    except ZoneInfoNotFoundError:
        return {
            "status": "error",
            "report": f"Invalid timezone identifier '{timezone_str}' found for {city}."
        }
    except Exception as e: # Catch-all for unexpected errors during time retrieval
        return {"status": "error", "report": f"An unexpected error occurred while getting time for {city}: {e}"}

# Create the root agent with the recommended configuration
root_agent = Agent(
    name="root_agent",
    model="gemini-2.5-flash-preview-05-20",
    description="Agent to answer questions about the weather or time in a city.",
    instruction=(
        "You are a helpful agent who can answer user questions about the weather or time in a city. "
        "Use the 'get_weather' tool when the user asks for weather information. "
        "Use the 'get_current_time' tool when the user asks for the current time in a specific city."
    ),
    tools=[get_weather, get_current_time],
)