import yaml
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from weather_service import WeatherService
from pykalman import KalmanFilter
from dotenv import load_dotenv
import folium
from streamlit_folium import st_folium

# Load environment variables
load_dotenv()

class EnergyForecastModel:
    def __init__(self, n_estimators=100, n_models=5):
        self.n_estimators = n_estimators
        self.n_models = n_models
        self.models = []
        self.scaler = StandardScaler()
    
    def create_ensemble(self):
        self.models = [RandomForestRegressor(n_estimators=self.n_estimators, random_state=42+i) 
                for i in range(self.n_models)]
        return self.models
    
    def generate_synthetic_data(self, n_samples, features, latitude=0):
        X = np.random.normal(size=(n_samples, len(features)))
        return X, self._generate_target(X, latitude)
    
    def _generate_target(self, X, latitude):
        raise NotImplementedError("Must be implemented by subclass")
    
    def train_and_predict(self, X_test, latitude=0):
        """Train on synthetic data and predict for test data"""
        if not self.models:
            self.create_ensemble()
        
        # Generate synthetic training data
        n_train = max(1000, len(X_test))  # Use at least 1000 training samples
        X_train, y_train = self.generate_synthetic_data(n_train, range(X_test.shape[1]), latitude)
        
        # Scale both training and test data
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train models and make predictions
        predictions = np.zeros((len(X_test_scaled), self.n_models))
        for i, model in enumerate(self.models):
            model.fit(X_train_scaled, y_train)
            predictions[:, i] = model.predict(X_test_scaled)
        
        return self._process_predictions(predictions)

    def _process_predictions(self, predictions):
        # Remove outliers and average predictions
        generation = np.zeros(len(predictions))
        for i in range(len(predictions)):
            preds = predictions[i, :]
            mean_pred = np.mean(preds)
            std_pred = np.std(preds)
            valid_mask = np.abs(preds - mean_pred) <= 2 * std_pred
            generation[i] = np.mean(preds[valid_mask])
        return generation

class SolarForecastModel(EnergyForecastModel):
    def _generate_target(self, X, latitude):
        y = -np.clip(
            X[:, 5] * 0.2 * \
            (1 - 0.005 * (X[:, 3] - 25)) * \
            np.cos(np.radians(abs(latitude))), 
            0, None
        )
        bias = 0.1 * np.mean(np.abs(y))
        return y + bias + np.random.normal(0, 0.05 * np.std(y), size=len(y))

class WindForecastModel(EnergyForecastModel):
    def __init__(self, rated_power=2.0, num_turbines=5, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rated_power = rated_power
        self.num_turbines = num_turbines
    
    def _generate_target(self, X, _):
        terrain_factor = 0.8 + 0.4 * np.random.random()
        y = -self.rated_power * self.num_turbines * terrain_factor * \
            np.clip((X[:, 4] - 3.0) / (12.0 - 3.0), 0, 1)
        bias = 0.1 * np.mean(np.abs(y))
        return y + bias + np.random.normal(0, 0.05 * np.std(y), size=len(y))

def smooth_timeseries(data, window_size=3):
    return pd.Series(data).rolling(window=window_size, center=True).mean().fillna(method='bfill').fillna(method='ffill').values

def kalman_filter(forecast_values, params):
    values = forecast_values.values if isinstance(forecast_values, pd.Series) else forecast_values
    initial_state_mean = values[0] if params.get('initial_state_mean') is None else params['initial_state_mean']
    
    kf = KalmanFilter(
        transition_matrices=np.array([[1]]),
        observation_matrices=np.array([[1]]),
        initial_state_mean=np.array([initial_state_mean]),
        initial_state_covariance=np.array([[1.0]]),
        transition_covariance=np.array([[params['Q']]]),
        observation_covariance=np.array([[params['R']]])
    )
    
    means, _ = kf.filter(values.reshape(-1, 1))
    return pd.Series(means.flatten(), index=forecast_values.index)

def create_visualization(weather_data, location_info, show_confidence_interval=True):
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                        subplot_titles=("Weather Conditions", "Energy Generation", "Total Generation"))
    
    # Weather conditions plot
    for param, name in [
        ('temperature', 'Temperature (°C)'),
        ('wind_speed', 'Wind Speed (m/s)'),
        ('solar_irradiance', 'Solar Irradiance (100 W/m²)')
    ]:
        y_data = weather_data[param]/100 if param == 'solar_irradiance' else weather_data[param]
        fig.add_trace(go.Scatter(x=weather_data.index, y=y_data, name=name, line=dict(width=2)), row=1, col=1)
    
    # Generation plots
    if show_confidence_interval:
        for source in ['solar', 'wind']:
            color = 'rgba(255,127,14,0.1)' if source == 'solar' else 'rgba(44,160,44,0.1)'
            fig.add_trace(go.Scatter(x=weather_data.index, y=weather_data[f'{source}_ci_upper'],
                                   fill=None, mode='lines', line_color=color, showlegend=False), row=2, col=1)
            fig.add_trace(go.Scatter(x=weather_data.index, y=weather_data[f'{source}_ci_lower'],
                                   fill='tonexty', mode='lines', line_color=color, showlegend=False), row=2, col=1)
    
    # Add generation traces
    fig.add_trace(go.Scatter(x=weather_data.index, y=weather_data['solar_generation'],
                           name="Solar Generation (MW)", line=dict(width=2, color='rgb(255,127,14)')), row=2, col=1)
    fig.add_trace(go.Scatter(x=weather_data.index, y=weather_data['wind_generation'],
                           name="Wind Generation (MW)", line=dict(width=2, color='rgb(44,160,44)')), row=2, col=1)
    
    # Total generation
    fig.add_trace(go.Scatter(x=weather_data.index, y=weather_data['total_generation'],
                           name="Total Generation (MW)", fill='tozeroy', line=dict(width=2)), row=3, col=1)
    
    # Layout updates
    fig.update_layout(
        height=800,
        showlegend=True,
        plot_bgcolor='white',
        paper_bgcolor='white',
        hovermode='x unified',
        title=dict(text=f"Energy Generation Forecast for {location_info['location_name']}", x=0.5, xanchor='center', font=dict(color='black')),
        font=dict(color='black'),
        legend=dict(font=dict(color='black')),
        annotations=[dict(font=dict(color='black')) for _ in fig['layout']['annotations']]  # Update subplot titles
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray', tickfont=dict(color='black'))
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray', tickfont=dict(color='black'))
    
    return fig

def simulate_weather_data(forecast_days, base_temp=25.0, base_wind=5.0, base_solar=800.0):
    dates = pd.date_range(start=datetime.now(), periods=forecast_days*24, freq='h')
    weather_data = pd.DataFrame(index=dates)
    
    # Add time-based features
    weather_data['hour'] = weather_data.index.hour
    weather_data['day_of_year'] = weather_data.index.dayofyear
    weather_data['month'] = weather_data.index.month

    # Temperature simulation with daily and seasonal patterns
    weather_data['temperature'] = base_temp + \
        5 * np.sin(2 * np.pi * weather_data['hour'] / 24) + \
        2 * np.sin(2 * np.pi * weather_data['day_of_year'] / 365) + \
        np.random.normal(0, 1.5, size=len(dates))

    # Wind speed simulation
    weather_data['wind_speed'] = base_wind + \
        2 * np.sin(2 * np.pi * weather_data['hour'] / 24) + \
        np.random.normal(0, 1.5, size=len(dates))
    weather_data['wind_speed'] = weather_data['wind_speed'].clip(0, None)

    # Solar irradiance with day/night and seasonal patterns
    daily_pattern = np.sin(2 * np.pi * (weather_data['hour'] - 6) / 24)
    seasonal_pattern = np.sin(2 * np.pi * (weather_data['day_of_year'] - 172) / 365)
    weather_data['solar_irradiance'] = base_solar * \
        np.clip(daily_pattern, 0, None) * (0.7 + 0.3 * seasonal_pattern) + \
        np.random.normal(0, 30, size=len(dates))
    weather_data['solar_irradiance'] = weather_data['solar_irradiance'].clip(0, None)
    
    return weather_data

def process_and_display_results(weather_data, solar_model, wind_model, location_info, show_confidence_interval=True):
    # Add time-based features
    weather_data['hour'] = weather_data.index.hour
    weather_data['day_of_year'] = weather_data.index.dayofyear
    weather_data['month'] = weather_data.index.month
    
    features = ['hour', 'day_of_year', 'month', 'temperature', 'wind_speed', 'solar_irradiance']
    X = weather_data[features].values
    
    # Generate predictions using synthetic training data
    solar_generation = solar_model.train_and_predict(X, latitude=location_info.get('latitude', 28.6139))
    wind_generation = wind_model.train_and_predict(X)
    
    # Apply smoothing
    weather_data['solar_generation'] = smooth_timeseries(solar_generation)
    weather_data['wind_generation'] = smooth_timeseries(wind_generation)
    
    # Apply Kalman filtering
    weather_data['solar_generation'] = kalman_filter(
        pd.Series(weather_data['solar_generation'], index=weather_data.index),
        {'Q': 0.1, 'R': 1.0}
    )
    weather_data['wind_generation'] = kalman_filter(
        pd.Series(weather_data['wind_generation'], index=weather_data.index),
        {'Q': 0.2, 'R': 1.5}
    )
    
    # Calculate confidence intervals
    if show_confidence_interval:
        std_solar = np.std(solar_generation) * 1.96  # 95% CI
        std_wind = np.std(wind_generation) * 1.96
        
        weather_data['solar_ci_lower'] = weather_data['solar_generation'] - std_solar
        weather_data['solar_ci_upper'] = weather_data['solar_generation'] + std_solar
        weather_data['wind_ci_lower'] = weather_data['wind_generation'] - std_wind
        weather_data['wind_ci_upper'] = weather_data['wind_generation'] + std_wind
        
        weather_data[['solar_ci_lower', 'wind_ci_lower']] = \
            weather_data[['solar_ci_lower', 'wind_ci_lower']].clip(lower=0)
    
    # Calculate total generation
    weather_data['total_generation'] = weather_data['solar_generation'] + weather_data['wind_generation']
    
    # Create and display visualization
    fig = create_visualization(weather_data, location_info, show_confidence_interval)
    st.plotly_chart(fig, use_container_width=True)
    
    # Display statistics
    display_statistics(weather_data)

def display_statistics(weather_data):
    st.subheader("Forecast Summary")
    col1, col2, col3 = st.columns(3)
    
    metrics = [
        ('Average Solar Generation', 'solar_generation'),
        ('Average Wind Generation', 'wind_generation'),
        ('Total Average Generation', 'total_generation')
    ]
    
    for (label, column), col in zip(metrics, [col1, col2, col3]):
        with col:
            mean_val = weather_data[column].mean()
            std_val = weather_data[column].std()
            st.metric(label, f"{mean_val:.2f} MW", delta=f"{std_val:.2f} MW σ")
    
    # Generation patterns
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
        total_generation = total_solar + total_wind
        
        energy_mix_data = pd.DataFrame({
            'Source': ['Solar', 'Wind'],
            'Generation (MWh)': [total_solar, total_wind],
            'Percentage (%)': [
                (total_solar / total_generation) * 100,
                (total_wind / total_generation) * 100
            ]
        })
        
        st.dataframe(
            energy_mix_data,
            column_config={
                'Source': st.column_config.TextColumn('Energy Source'),
                'Generation (MWh)': st.column_config.NumberColumn('Generation (MWh)', format='%.1f'),
                'Percentage (%)': st.column_config.NumberColumn('Share (%)', format='%.1f%%')
            },
            hide_index=True,
            use_container_width=True
        )
        
        # Create pie chart
        energy_mix_fig = go.Figure(data=[go.Pie(
            labels=['Solar', 'Wind'],
            values=[total_solar, total_wind],
            hole=0.4,
            textinfo='label+percent',
            marker_colors=['rgba(255,127,14,0.8)', 'rgba(44,160,44,0.8)'],
            textfont=dict(color='black')
        )])
        
        energy_mix_fig.update_layout(
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=300,
            margin=dict(l=20, r=20, t=20, b=20),
            font=dict(color='black'),
            annotations=[dict(
                text=f'Total<br>{total_generation:.1f} MWh',
                x=0.5, y=0.5,
                font_size=14,
                font_color='black',
                showarrow=False
            )]
        )
        st.plotly_chart(energy_mix_fig, use_container_width=True)

def main():
    # Initialize weather service
    weather_service = WeatherService()
    
    # Page config and title
    st.set_page_config(page_title="Energy Generation Forecast", layout="wide")
    st.title("AI-Powered Energy Generation Forecast")
    
    # Initialize session state
    if 'latitude' not in st.session_state:
        st.session_state.latitude = 28.6139
    if 'longitude' not in st.session_state:
        st.session_state.longitude = 77.2090
    
    # Create layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Map component
        st.subheader("Select Location")
        if st.button("Reset to Default Location"):
            st.session_state.latitude = 28.6139
            st.session_state.longitude = 77.2090
            st.rerun()
        
        m = folium.Map(location=[st.session_state.latitude, st.session_state.longitude], 
                      zoom_start=4, tiles="CartoDB positron")
        
        # Add markers and styling
        folium.CircleMarker(
            location=[st.session_state.latitude, st.session_state.longitude],
            radius=8,
            color='red',
            fill=True,
            popup=f"Selected Location\nLat: {st.session_state.latitude:.4f}\nLon: {st.session_state.longitude:.4f}",
        ).add_to(m)

        # Add a larger pulsing circle for visual effect
        folium.CircleMarker(
            location=[st.session_state.latitude, st.session_state.longitude],
            radius=20,
            color='red',
            fill=False,
            popup="Click anywhere to select a new location",
            weight=2,
            opacity=0.5,
            className='pulsing-circle'
        ).add_to(m)

        # Add custom CSS for pulsing effect
        css = """
        <style>
        @keyframes pulse {
            0% { transform: scale(0.5); opacity: 0; }
            50% { opacity: 1; }
            100% { transform: scale(1.2); opacity: 0; }
        }
        .pulsing-circle {
            animation: pulse 2s ease-out infinite;
        }
        </style>
        """
        m.get_root().html.add_child(folium.Element(css))

        # Add click instructions directly on the map
        folium.Rectangle(
            bounds=[
                [st.session_state.latitude - 0.1, st.session_state.longitude - 0.2],  # Southwest corner
                [st.session_state.latitude + 0.1, st.session_state.longitude + 0.2]   # Northeast corner
            ],
            color="transparent",
            fill=False,
            popup=folium.Popup("Click anywhere on the map to select a location", show=True)
        ).add_to(m)
        
        # Display map
        map_data = st_folium(m, height=400, width=None, returned_objects=["last_clicked"])
        
        if (map_data and 'last_clicked' in map_data and map_data['last_clicked']):
            new_lat = map_data['last_clicked']['lat']
            new_lng = map_data['last_clicked']['lng']
            if (abs(new_lat - st.session_state.latitude) > 0.0001 or 
                abs(new_lng - st.session_state.longitude) > 0.0001):
                st.session_state.latitude = new_lat
                st.session_state.longitude = new_lng
                st.rerun()
    
    # Sidebar configuration
    with st.sidebar:
        st.header("Input Parameters")
        use_live_data = st.checkbox("Use Live Weather Data", value=True)
        show_confidence_interval = st.checkbox("Show Prediction Confidence Interval", value=True)
        forecast_days = st.number_input("Forecast Days", min_value=1, max_value=30, value=7)
    
    # Generate forecast button
    if st.button("Generate Forecast"):
        with st.spinner("Generating forecast..."):
            # Get weather data
            weather_data = weather_service.get_weather_forecast(
                st.session_state.latitude, 
                st.session_state.longitude, 
                forecast_days
            ) if use_live_data else simulate_weather_data(forecast_days)
            
            # Generate forecasts
            solar_model = SolarForecastModel()
            wind_model = WindForecastModel()
            
            # Process and display results
            process_and_display_results(
                weather_data, 
                solar_model, 
                wind_model, 
                location_info=weather_service.get_location_info(
                    st.session_state.latitude, 
                    st.session_state.longitude
                ),
                show_confidence_interval=show_confidence_interval
            )

if __name__ == "__main__":
    main()

# Export these classes and functions for use in dashboard.py
__all__ = [
    'WeatherService',
    'SolarForecastModel',
    'WindForecastModel',
    'simulate_weather_data',
    'process_and_display_results',
    'create_visualization',
    'display_statistics'
]
