import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from weather_service import WeatherService
import os
from dotenv import load_dotenv
import json
import folium
from streamlit_folium import st_folium

# Load environment variables
load_dotenv()

# Initialize weather service
weather_service = WeatherService()

# Set page config
st.set_page_config(page_title="Energy Generation Forecast", layout="wide")

# Title and description
st.title("AI-Powered Energy Generation Forecast")
st.markdown("""
This system predicts solar and wind energy generation using real-time weather data and machine learning.
It helps energy companies optimize planning and improve grid stability.
""")

# Initialize session state for coordinates if not exists
if 'latitude' not in st.session_state:
    st.session_state.latitude = 28.6139
if 'longitude' not in st.session_state:
    st.session_state.longitude = 77.2090
if 'map_clicked' not in st.session_state:
    st.session_state.map_clicked = False

# Create two columns for the map and info
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Select Location")
    
    # Add a button to reset map to default location
    if st.button("Reset to Default Location"):
        st.session_state.latitude = 28.6139
        st.session_state.longitude = 77.2090
        st.rerun()
    
    # Create a folium map centered at the current coordinates
    m = folium.Map(location=[st.session_state.latitude, st.session_state.longitude], 
                  zoom_start=4,
                  tiles="CartoDB positron")  # Using a cleaner map style
    
    # Add a red marker at the current location
    folium.Marker(
        [st.session_state.latitude, st.session_state.longitude],
        popup=f"Selected Location\nLat: {st.session_state.latitude:.4f}\nLon: {st.session_state.longitude:.4f}",
        icon=folium.Icon(color='red', icon='info-sign'),
        draggable=False
    ).add_to(m)
    
    # Display the map
    map_data = st_folium(
        m,
        height=400,
        width=None,
        returned_objects=["last_clicked"],
        key=f"map_{st.session_state.latitude}_{st.session_state.longitude}"
    )
    
    # Update coordinates if map is clicked
    if (map_data is not None and 
        'last_clicked' in map_data and 
        map_data['last_clicked'] is not None):
        
        new_lat = map_data['last_clicked']['lat']
        new_lng = map_data['last_clicked']['lng']
        
        # Only update if coordinates have changed
        if (abs(new_lat - st.session_state.latitude) > 0.0001 or 
            abs(new_lng - st.session_state.longitude) > 0.0001):
            
            st.session_state.latitude = new_lat
            st.session_state.longitude = new_lng
            st.rerun()
    
    st.info("👆 Click anywhere on the map to select a location, or use the sidebar controls to enter coordinates manually.")

with col2:
    st.subheader("Selected Location")
    try:
        location_info = weather_service.get_location_info(st.session_state.latitude, st.session_state.longitude)
        st.success(
            f"📍 **Location**: {location_info['location_name']}\n\n"
            f"🌍 **Coordinates**:\n"
            f"- Latitude: {st.session_state.latitude:.4f}°\n"
            f"- Longitude: {st.session_state.longitude:.4f}°\n\n"
            f"⏰ **Timezone**: {location_info['timezone']}"
        )
    except Exception as e:
        st.error("Unable to fetch location details. Please try again.")

# Sidebar for input parameters
with st.sidebar:
    st.header("Input Parameters")
    
    # Location parameters with geocoding
    st.subheader("Location Parameters")
    latitude = st.number_input("Latitude", value=st.session_state.latitude, format="%.4f", key="lat_input")
    longitude = st.number_input("Longitude", value=st.session_state.longitude, format="%.4f", key="lon_input")
    
    # Update session state if inputs change
    if latitude != st.session_state.latitude:
        st.session_state.latitude = latitude
    if longitude != st.session_state.longitude:
        st.session_state.longitude = longitude
    
    # Advanced options
    st.subheader("Advanced Options")
    use_live_data = st.checkbox("Use Live Weather Data", value=True)
    show_confidence_interval = st.checkbox("Show Prediction Confidence Interval", value=True)
    
    # Weather parameters for simulation mode
    if not use_live_data:
        st.subheader("Simulation Parameters")
        temperature = st.number_input("Base Temperature (°C)", value=25.0)
        wind_speed = st.number_input("Base Wind Speed (m/s)", value=5.0)
        solar_irradiance = st.number_input("Base Solar Irradiance (W/m²)", value=800.0)
    
    # Get and display location info
    location_info = weather_service.get_location_info(st.session_state.latitude, st.session_state.longitude)
    st.info(f"Selected Location: {location_info['location_name']}\nTimezone: {location_info['timezone']}")
    
    # Date range selection
    st.subheader("Forecast Range")
    forecast_days = st.number_input("Forecast Days", min_value=1, max_value=30, value=7)

# Generate forecast when button is clicked
if st.button("Generate Forecast"):
    with st.spinner("Fetching weather data and generating forecast..."):
        if use_live_data:
            # Fetch real-time weather data
            weather_data = weather_service.get_weather_forecast(st.session_state.latitude, st.session_state.longitude, forecast_days)
            if weather_data is None:
                st.error("Failed to fetch weather data. Please check your API key or try again later.")
                st.stop()
        else:
            # Use simulated data (existing simulation code)
            dates = pd.date_range(start=datetime.now(), periods=forecast_days*24, freq='h')
            weather_data = pd.DataFrame(index=dates)
            # Simulate weather data with some randomness and daily patterns
            weather_data = pd.DataFrame(index=dates)
    
            # Add time-based features
            weather_data['hour'] = weather_data.index.hour
            weather_data['day_of_year'] = weather_data.index.dayofyear
            weather_data['month'] = weather_data.index.month
    
            # Temperature simulation with daily pattern
            weather_data['temperature'] = temperature + \
                5 * np.sin(2 * np.pi * (weather_data.index.hour) / 24) + \
                2 * np.sin(2 * np.pi * (weather_data.index.dayofyear) / 365) + \
                np.random.normal(0, 1.5, size=len(dates))
    
            # Wind speed simulation with more realistic patterns
            weather_data['wind_speed'] = wind_speed + \
                2 * np.sin(2 * np.pi * (weather_data.index.hour) / 24) + \
                np.random.normal(0, 1.5, size=len(dates))
            weather_data['wind_speed'] = weather_data['wind_speed'].clip(0, None)
    
            # Solar irradiance with improved day/night pattern
            daily_pattern = np.sin(2 * np.pi * (weather_data.index.hour - 6) / 24)
            seasonal_pattern = np.sin(2 * np.pi * (weather_data.index.dayofyear - 172) / 365)
            weather_data['solar_irradiance'] = solar_irradiance * \
                np.clip(daily_pattern, 0, None) * (0.7 + 0.3 * seasonal_pattern) + \
                np.random.normal(0, 30, size=len(dates))
            weather_data['solar_irradiance'] = weather_data['solar_irradiance'].clip(0, None)

        # Add time-based features
        weather_data['hour'] = weather_data.index.hour
        weather_data['day_of_year'] = weather_data.index.dayofyear
        weather_data['month'] = weather_data.index.month
        
        # Prepare features for ML model
        features = ['hour', 'day_of_year', 'month', 'temperature', 'wind_speed', 'solar_irradiance']
        X = weather_data[features].values
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Train ML models with improved historical data simulation
        solar_model = RandomForestRegressor(n_estimators=100, random_state=42)
        wind_model = RandomForestRegressor(n_estimators=100, random_state=42)
        
        # Generate more realistic synthetic training data
        n_samples = 1000
        solar_historical_X = np.random.normal(size=(n_samples, len(features)))
        wind_historical_X = np.random.normal(size=(n_samples, len(features)))
        
        # Improved solar generation model with temperature and latitude effects
        solar_historical_y = -np.clip(
            solar_historical_X[:, 5] * 0.2 * \
            (1 - 0.005 * (solar_historical_X[:, 3] - 25)) * \
            np.cos(np.radians(abs(st.session_state.latitude))), 
            0, None
        )
        solar_model.fit(solar_historical_X, solar_historical_y)
        
        # Improved wind generation model with terrain effects
        rated_power = 2.0  # MW per turbine
        num_turbines = 5
        wind_historical_y = wind_historical_X[:, 4].copy()
        terrain_factor = 0.8 + 0.4 * np.random.random()  # Simplified terrain effect
        wind_historical_y = -rated_power * num_turbines * terrain_factor * \
            np.clip((wind_historical_y - 3.0) / (12.0 - 3.0), 0, 1)
        wind_model.fit(wind_historical_X, wind_historical_y)
        
        # Generate predictions with confidence intervals
        weather_data['solar_generation'] = solar_model.predict(X_scaled)
        weather_data['wind_generation'] = wind_model.predict(X_scaled)
        
        # Calculate prediction intervals
        if show_confidence_interval:
            solar_predictions = np.array([tree.predict(X_scaled) 
                for tree in solar_model.estimators_])
            wind_predictions = np.array([tree.predict(X_scaled) 
                for tree in wind_model.estimators_])
            
            weather_data['solar_ci_lower'] = np.percentile(solar_predictions, 5, axis=0)
            weather_data['solar_ci_upper'] = np.percentile(solar_predictions, 95, axis=0)
            weather_data['wind_ci_lower'] = np.percentile(wind_predictions, 5, axis=0)
            weather_data['wind_ci_upper'] = np.percentile(wind_predictions, 95, axis=0)
        
        # Total generation
        weather_data['total_generation'] = weather_data['solar_generation'] + \
            weather_data['wind_generation']
        
        # Display results
        st.header("Forecast Results")
        
        # Create subplot with shared x-axis
        fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                            subplot_titles=("Weather Conditions", "Energy Generation", "Total Generation"))
        
        # Weather conditions plot with improved styling
        fig.add_trace(
            go.Scatter(x=weather_data.index, y=weather_data['temperature'],
                      name="Temperature (°C)", line=dict(width=2)), row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=weather_data.index, y=weather_data['wind_speed'],
                      name="Wind Speed (m/s)", line=dict(width=2)), row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=weather_data.index, y=weather_data['solar_irradiance']/100,
                      name="Solar Irradiance (100 W/m²)", line=dict(width=2)), row=1, col=1
        )
        
        # Generation plots with confidence intervals and improved styling
        if show_confidence_interval:
            fig.add_trace(
                go.Scatter(x=weather_data.index, y=weather_data['solar_ci_upper'],
                          fill=None, mode='lines', line_color='rgba(255,127,14,0.1)',
                          showlegend=False), row=2, col=1)
            fig.add_trace(
                go.Scatter(x=weather_data.index, y=weather_data['solar_ci_lower'],
                          fill='tonexty', mode='lines', line_color='rgba(255,127,14,0.1)',
                          showlegend=False), row=2, col=1)
            fig.add_trace(
                go.Scatter(x=weather_data.index, y=weather_data['wind_ci_upper'],
                          fill=None, mode='lines', line_color='rgba(44,160,44,0.1)',
                          showlegend=False), row=2, col=1)
            fig.add_trace(
                go.Scatter(x=weather_data.index, y=weather_data['wind_ci_lower'],
                          fill='tonexty', mode='lines', line_color='rgba(44,160,44,0.1)',
                          showlegend=False), row=2, col=1)
        
        fig.add_trace(
            go.Scatter(x=weather_data.index, y=weather_data['solar_generation'],
                      name="Solar Generation (MW)", line=dict(width=2, color='rgb(255,127,14)')), 
            row=2, col=1
        )
        fig.add_trace(
            go.Scatter(x=weather_data.index, y=weather_data['wind_generation'],
                      name="Wind Generation (MW)", line=dict(width=2, color='rgb(44,160,44)')), 
            row=2, col=1
        )
        
        # Total generation plot
        fig.add_trace(
            go.Scatter(x=weather_data.index, y=weather_data['total_generation'],
                      name="Total Generation (MW)", fill='tozeroy',
                      line=dict(width=2)), row=3, col=1
        )
        
        # Update layout with improved styling
        fig.update_layout(
            height=800,
            showlegend=True,
            plot_bgcolor='white',
            paper_bgcolor='white',
            hovermode='x unified',
            title=dict(
                text=f"Energy Generation Forecast for {location_info['location_name']}",
                x=0.5,
                xanchor='center'
            )
        )
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
        st.plotly_chart(fig, use_container_width=True)
        
        # Display enhanced statistics
        st.subheader("Forecast Summary")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Average Solar Generation",
                     f"{weather_data['solar_generation'].mean():.2f} MW",
                     delta=f"{weather_data['solar_generation'].std():.2f} MW σ")
        with col2:
            st.metric("Average Wind Generation",
                     f"{weather_data['wind_generation'].mean():.2f} MW",
                     delta=f"{weather_data['wind_generation'].std():.2f} MW σ")
        with col3:
            st.metric("Total Average Generation",
                     f"{weather_data['total_generation'].mean():.2f} MW",
                     delta=f"{weather_data['total_generation'].std():.2f} MW σ")
        
        # Additional statistics
        st.subheader("Generation Statistics")
        stats_cols = st.columns(2)
        
        with stats_cols[0]:
            st.write("Daily Generation Pattern")
            daily_pattern = weather_data.groupby(weather_data.index.hour)[
                ['solar_generation', 'wind_generation']].mean()
            st.line_chart(daily_pattern)
        
        with stats_cols[1]:
            st.write("Energy Mix")
            total_solar = abs(weather_data['solar_generation'].sum())
            total_wind = abs(weather_data['wind_generation'].sum())
            energy_mix = pd.DataFrame({
                'Source': ['Solar', 'Wind'],
                'Generation (MWh)': [total_solar, total_wind]
            })
            st.bar_chart(energy_mix.set_index('Source'))
        
        # API Integration Information
        st.subheader("API Integration")
        st.markdown("""
        To integrate this forecast into your systems, use our API endpoint:
        ```
        GET /forecast/?latitude={}&longitude={}&days={}
        ```
        """.format(st.session_state.latitude, st.session_state.longitude, forecast_days))
        
        # Download options
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="Download Forecast Data (CSV)",
                data=weather_data.to_csv(),
                file_name=f"energy_forecast_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        with col2:
            st.download_button(
                label="Download Forecast Data (JSON)",
                data=json.dumps(weather_data.to_dict(orient='records'), indent=2),
                file_name=f"energy_forecast_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )
