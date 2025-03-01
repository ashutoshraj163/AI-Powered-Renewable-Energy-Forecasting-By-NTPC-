from fastapi import FastAPI, Query
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from weather_service import WeatherService
from typing import Optional
from pydantic import BaseModel

app = FastAPI(title="Energy Generation Forecast API")
weather_service = WeatherService()

class ForecastResponse(BaseModel):
    location_name: str
    timezone: str
    forecast: dict
    total_generation: float
    average_solar: float
    average_wind: float
    confidence_intervals: Optional[dict] = None

@app.get("/forecast/", response_model=ForecastResponse)
async def get_forecast(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    days: int = Query(7, ge=1, le=30)
):
    # Get location info
    location_info = weather_service.get_location_info(latitude, longitude)
    
    # Get weather forecast
    weather_data = weather_service.get_weather_forecast(latitude, longitude, days)
    
    if weather_data is None:
        return {"error": "Failed to fetch weather data"}
    
    # Prepare features for ML model
    features = ['hour', 'day_of_year', 'month', 'temperature', 'wind_speed', 'solar_irradiance']
    weather_data['hour'] = weather_data.index.hour
    weather_data['day_of_year'] = weather_data.index.dayofyear
    weather_data['month'] = weather_data.index.month
    
    X = weather_data[features].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Train and predict with models
    solar_model = RandomForestRegressor(n_estimators=100, random_state=42)
    wind_model = RandomForestRegressor(n_estimators=100, random_state=42)
    
    # Generate synthetic training data
    solar_historical_X = np.random.normal(size=(1000, len(features)))
    wind_historical_X = np.random.normal(size=(1000, len(features)))
    
    # Solar model training
    solar_historical_y = -np.clip(solar_historical_X[:, 5] * 0.2 * \
        (1 - 0.005 * (solar_historical_X[:, 3] - 25)), 0, None)
    solar_model.fit(solar_historical_X, solar_historical_y)
    
    # Wind model training
    rated_power = 2.0
    num_turbines = 5
    wind_historical_y = wind_historical_X[:, 4].copy()
    wind_historical_y = -rated_power * num_turbines * \
        np.clip((wind_historical_y - 3.0) / (12.0 - 3.0), 0, 1)
    wind_model.fit(wind_historical_X, wind_historical_y)
    
    # Generate predictions
    solar_pred = solar_model.predict(X_scaled)
    wind_pred = wind_model.predict(X_scaled)
    
    # Calculate confidence intervals
    solar_predictions = np.array([tree.predict(X_scaled) 
        for tree in solar_model.estimators_])
    wind_predictions = np.array([tree.predict(X_scaled) 
        for tree in wind_model.estimators_])
    
    confidence_intervals = {
        'solar': {
            'lower': np.percentile(solar_predictions, 5, axis=0).tolist(),
            'upper': np.percentile(solar_predictions, 95, axis=0).tolist()
        },
        'wind': {
            'lower': np.percentile(wind_predictions, 5, axis=0).tolist(),
            'upper': np.percentile(wind_predictions, 95, axis=0).tolist()
        }
    }
    
    # Prepare response
    forecast_data = {
        'timestamps': weather_data.index.strftime('%Y-%m-%d %H:%M:%S').tolist(),
        'solar_generation': solar_pred.tolist(),
        'wind_generation': wind_pred.tolist(),
        'weather': {
            'temperature': weather_data['temperature'].tolist(),
            'wind_speed': weather_data['wind_speed'].tolist(),
            'solar_irradiance': weather_data['solar_irradiance'].tolist()
        }
    }
    
    return ForecastResponse(
        location_name=location_info['location_name'],
        timezone=location_info['timezone'],
        forecast=forecast_data,
        total_generation=float(np.sum(solar_pred + wind_pred)),
        average_solar=float(np.mean(solar_pred)),
        average_wind=float(np.mean(wind_pred)),
        confidence_intervals=confidence_intervals
    )