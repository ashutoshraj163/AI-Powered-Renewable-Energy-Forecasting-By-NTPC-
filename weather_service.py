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
        self.api_key = "YOUR_API_KEY"  # Replace with actual API key
        self.base_url = "https://api.openweathermap.org/data/2.5/forecast"
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
        
    def get_weather_forecast(self, latitude, longitude, forecast_days):
        # For demo purposes, generate synthetic data if no API key
        if self.api_key == "YOUR_API_KEY":
            return self._generate_synthetic_forecast(forecast_days)
        
        params = {
            'lat': latitude,
            'lon': longitude,
            'appid': self.api_key,
            'units': 'metric'
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Process API response
            weather_data = []
            for item in data['list']:
                weather_data.append({
                    'datetime': datetime.fromtimestamp(item['dt']),
                    'temperature': item['main']['temp'],
                    'wind_speed': item['wind']['speed'],
                    'solar_irradiance': self._estimate_solar_irradiance(
                        item['clouds']['all'],
                        datetime.fromtimestamp(item['dt']),
                        latitude
                    )
                })
            
            # Convert to DataFrame with datetime index
            df = pd.DataFrame(weather_data)
            df.set_index('datetime', inplace=True)
            
            # Resample to hourly data if needed
            if len(df) < forecast_days * 24:
                df = df.resample('H').interpolate(method='cubic')
            
            # Limit to requested forecast days
            df = df[:forecast_days * 24]
            
            return df
            
        except Exception as e:
            print(f"Error fetching weather data: {e}")
            return self._generate_synthetic_forecast(forecast_days)
    
    def _estimate_solar_irradiance(self, cloud_cover, dt, latitude):
        # Simplified solar irradiance estimation
        hour = dt.hour
        day_of_year = dt.timetuple().tm_yday
        
        # Calculate solar angle
        declination = 23.45 * np.sin(np.radians(360/365 * (day_of_year - 81)))
        hour_angle = 15 * (hour - 12)
        solar_angle = np.arcsin(
            np.sin(np.radians(latitude)) * np.sin(np.radians(declination)) +
            np.cos(np.radians(latitude)) * np.cos(np.radians(declination)) * np.cos(np.radians(hour_angle))
        )
        
        # Base irradiance (W/m²)
        base_irradiance = 1000 * np.sin(solar_angle) if solar_angle > 0 else 0
        
        # Cloud effect (simple linear reduction)
        cloud_factor = 1 - (cloud_cover / 100) * 0.75
        
        return base_irradiance * cloud_factor
    
    def _generate_synthetic_forecast(self, forecast_days):
        """Generate synthetic weather data for testing"""
        dates = pd.date_range(
            start=datetime.now().replace(minute=0, second=0, microsecond=0),
            periods=forecast_days * 24,
            freq='H'
        )
        
        df = pd.DataFrame(index=dates)
        
        # Temperature with daily pattern (°C)
        df['temperature'] = 25 + 5 * np.sin(2 * np.pi * (df.index.hour / 24)) + \
                          np.random.normal(0, 1, size=len(df))
        
        # Wind speed with some randomness (m/s)
        df['wind_speed'] = 5 + 2 * np.sin(2 * np.pi * (df.index.hour / 24)) + \
                         np.random.normal(0, 1, size=len(df))
        df['wind_speed'] = df['wind_speed'].clip(0, None)
        
        # Solar irradiance with day/night pattern (W/m²)
        df['solar_irradiance'] = 800 * np.sin(np.pi * (df.index.hour / 24)) + \
                               np.random.normal(0, 50, size=len(df))
        df['solar_irradiance'] = df['solar_irradiance'].clip(0, None)
        
        return df
    
    def get_location_info(self, latitude, longitude):
        """Get location name from coordinates"""
        try:
            location = self.geolocator.reverse((latitude, longitude))
            if location:
                address = location.raw.get('address', {})
                city = address.get('city', '')
                state = address.get('state', '')
                country = address.get('country', '')
                
                if city:
                    location_name = f"{city}, {country}"
                elif state:
                    location_name = f"{state}, {country}"
                else:
                    location_name = country
                
                return {
                    'location_name': location_name,
                    'latitude': latitude,
                    'longitude': longitude
                }
        except Exception as e:
            print(f"Error getting location info: {e}")
        
        return {
            'location_name': f"Location ({latitude:.2f}, {longitude:.2f})",
            'latitude': latitude,
            'longitude': longitude
        }