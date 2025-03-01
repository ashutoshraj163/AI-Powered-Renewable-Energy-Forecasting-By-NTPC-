import requests
import pandas as pd
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from timezonefinder import TimezoneFinder
from geopy.geocoders import Nominatim
import pytz
import numpy as np


load_dotenv()

class WeatherService:
    def __init__(self):
        self.tf = TimezoneFinder()
        self.geolocator = Nominatim(user_agent="energy_forecast_app")
        
    def get_location_info(self, lat: float, lon: float):
        """Get timezone and location name for coordinates"""
        timezone_str = self.tf.timezone_at(lat=lat, lng=lon)
        location = self.geolocator.reverse(f"{lat}, {lon}")
        return {
            'timezone': timezone_str or 'UTC',
            'location_name': location.address if location else f"Lat: {lat}, Lon: {lon}"
        }
        
    def get_weather_forecast(self, lat: float, lon: float, days: int = 7) -> pd.DataFrame:
        """Fetch weather forecast from OpenMeteo API"""
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&hourly=temperature_2m,windspeed_10m,cloudcover"
            f"&temperature_unit=celsius"
            f"&windspeed_unit=ms"
            f"&forecast_days={days}"
            f"&timezone=auto"
        )
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            # Process forecast data
            df = pd.DataFrame({
                'timestamp': pd.to_datetime(data['hourly']['time']),
                'temperature': data['hourly']['temperature_2m'],
                'wind_speed': data['hourly']['windspeed_10m'],
                'clouds': data['hourly']['cloudcover']
            })
            
            # Set timestamp as index
            df.set_index('timestamp', inplace=True)
            
            # Add solar irradiance estimation
            for idx in df.index:
                df.at[idx, 'solar_irradiance'] = self._estimate_solar_irradiance(
                    df.at[idx, 'clouds'],
                    lat, lon,
                    idx
                )
            
            return df
            
        except requests.RequestException as e:
            print(f"Error fetching weather data: {e}")
            return None
            
    def _estimate_solar_irradiance(self, cloud_cover: float, lat: float, lon: float, timestamp: datetime) -> float:
        """Estimate solar irradiance based on cloud cover and solar position"""
        try:
            # Calculate solar irradiance using time of day and cloud cover
            hour = timestamp.hour
            day_of_year = timestamp.timetuple().tm_yday
            
            # Basic solar position calculation
            declination = 23.45 * np.sin(2 * np.pi * (284 + day_of_year) / 365)
            hour_angle = 15 * (hour - 12)  # 15 degrees per hour from solar noon
            
            # Calculate solar elevation
            elevation = np.arcsin(
                np.sin(np.radians(lat)) * np.sin(np.radians(declination)) +
                np.cos(np.radians(lat)) * np.cos(np.radians(declination)) * np.cos(np.radians(hour_angle))
            )
            elevation_deg = np.degrees(elevation)
            
            # Calculate clear sky irradiance
            if elevation_deg > 0:
                clear_sky_irradiance = 1000 * np.sin(elevation)  # Approximate clear sky radiation
            else:
                clear_sky_irradiance = 0
            
            # Apply cloud cover reduction
            cloud_factor = 1 - (cloud_cover / 100) * 0.75
            return clear_sky_irradiance * cloud_factor
            
        except Exception:
            # Fallback to simplified calculation
            if 6 <= hour <= 18:  # Daytime hours
                return 1000 * (1 - cloud_cover / 100)
            return 0