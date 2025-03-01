# Energy Generation Forecast API

A FastAPI-based REST API that provides energy generation forecasts combining weather data, solar, and wind power generation predictions.

## Features

- Weather-based energy generation forecasting
- Solar power generation predictions
- Wind power generation predictions
- Confidence intervals for predictions
- Location-based forecasting with timezone support

## Prerequisites

- Python 3.12+
- Virtual environment (recommended)

## Installation

1. Clone the repository
2. Create and activate a virtual environment:
```bash
python -m venv myenv
myenv\Scripts\activate  # On Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the API

Start the API server with:
```bash
uvicorn api:app --reload --port 8000
```

The API will be available at `http://127.0.0.1:8000`

## API Endpoints

### GET /forecast/

Get energy generation forecast for a specific location.

**Parameters:**
- `latitude` (float, required): Location latitude (-90 to 90)
- `longitude` (float, required): Location longitude (-180 to 180)
- `days` (int, optional, default=7): Number of forecast days (1-30)

**Response:**
```json
{
    "location_name": "string",
    "timezone": "string",
    "forecast": {
        "timestamps": ["string"],
        "solar_generation": [number],
        "wind_generation": [number],
        "weather": {
            "temperature": [number],
            "wind_speed": [number],
            "solar_irradiance": [number]
        }
    },
    "total_generation": number,
    "average_solar": number,
    "average_wind": number,
    "confidence_intervals": {
        "solar": {
            "lower": [number],
            "upper": [number]
        },
        "wind": {
            "lower": [number],
            "upper": [number]
        }
    }
}
```

## Example Usage

```python
import requests

response = requests.get(
    "http://127.0.0.1:8000/forecast/",
    params={
        "latitude": 51.5074,
        "longitude": -0.1278,
        "days": 7
    }
)
forecast = response.json()
```


## API Documentation

Once the server is running, you can access:
- Interactive API documentation (Swagger UI): http://127.0.0.1:8000/docs
- Alternative API documentation (ReDoc): http://127.0.0.1:8000/redoc