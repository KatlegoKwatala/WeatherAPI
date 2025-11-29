from fastapi import FastAPI, HTTPException
from datetime import datetime, timedelta
import requests
import os
from pydantic import BaseModel

app = FastAPI()

# Cache storage
weather_cache = {}

API_KEY = "your_openweather_api_key"  # get this from openweatherapp.org
BASE_URL = "http://api.openweathermap.org/data/2.5/weather"

class WeatherResponse(BaseModel):
    City: str
    Temperature: int
    Weather: str
    cached: bool = False

@app.get("/")
def index():
    return {"name": "Weather API", "version": "1.0"}

@app.get("/weather/{city}")
def get_weather(city: str):
    # Check cache first
    cache_key = city.lower()
    if cache_key in weather_cache:
        cache_data = weather_cache[cache_key]
        # Check if cache is still valid (10 minutes)
        if datetime.now() - cache_data['timestamp'] < timedelta(minutes=10):
            response = cache_data['data']
            response['cached'] = True
            return response
    
    # If not cached or expired, call external API
    try:
        params = {
            'q': city,
            'appid': API_KEY,
            'units': 'metric'
        }
        
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()

        data = response.json()

        # Format the response
        weather_data = WeatherResponse(
            City=data['name'],
            Temperature=int(data['main']['temp']),
            Weather=data['weather'][0]['description'],
        )
        
        # Store in cache
        weather_cache[cache_key] = {
            'data': weather_data.dict(),
            'timestamp': datetime.now()
        }
        
        return weather_data

    except requests.exceptions.HTTPError:
        raise HTTPException(status_code=404, detail="City not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Weather service unavailable")