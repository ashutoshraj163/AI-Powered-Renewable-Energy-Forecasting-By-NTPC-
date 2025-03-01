import yaml
import streamlit as st
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from streamlit_authenticator.utilities import (CredentialsError, ForgotError, Hasher, LoginError, RegisterError, ResetError, UpdateError)
from datetime import datetime
from app import (
    process_and_display_results, 
    simulate_weather_data, 
    WeatherService,
    SolarForecastModel,
    WindForecastModel
)
import folium
from streamlit_folium import st_folium

st.set_page_config(
    page_title="NTPC Renewable Energy Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)
# Loading config file
with open('./config.yaml', 'r', encoding='utf-8') as file:
    config = yaml.load(file, Loader=SafeLoader)

# Custom CSS for enhanced UI
st.markdown("""
<style>
    /* Main container styling */
    .main {
        padding: 2rem;
        background-color: #f8f9fa;
    }
    
    /* Card styling */
    .stMetric {
        background-color: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Header styling */
    .main .block-container h1 {
        color: #1f2937;
        font-family: 'Segoe UI', sans-serif;
        font-weight: 600;
        padding-bottom: 1rem;
    }
    
    /* Subheader styling */
    .main .block-container h2, .main .block-container h3 {
        color: #374151;
        font-family: 'Segoe UI', sans-serif;
        padding-top: 1rem;
    }
    
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background-color: #ffffff;
    }
    
    /* Button styling */
    .stButton button {
        background-color: #3b82f6;
        color: white;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        border: none;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        background-color: #2563eb;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Table styling */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* Chart container styling */
    .chart-container {
        background-color: white;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state for active tab and coordinates
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "Overview"
if 'weather_service' not in st.session_state:
    st.session_state.weather_service = WeatherService()
if 'latitude' not in st.session_state:
    st.session_state.latitude = 28.6139  # Default to New Delhi
if 'longitude' not in st.session_state:
    st.session_state.longitude = 77.2090

# Pre-hashing all plain text passwords once
# stauth.Hasher.hash_passwords(config['credentials'])

# Creating the authenticator object
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# Sidebar for navigation
page = None
if st.session_state.get('authentication_status'):
    st.image("logo.png", width=100)

    # st.sidebar.markdown(f"<h2 style='text-align: center; color: #4CAF50;'>Welcome {st.session_state['name']}</h2>", unsafe_allow_html=True)

    # Sidebar with enhanced styling
    with st.sidebar:

        st.markdown("# Navigation")

        tabs = ["Overview", "Analytics", "Reports", "Settings"]
        for tab in tabs:
            if st.button(
                tab,
                key=f"tab_{tab}",
                help=f"Navigate to {tab}",
                type="primary" if st.session_state.active_tab == tab else "secondary"
            ):
                st.session_state.active_tab = tab
             

        st.markdown("---")
        st.markdown("### Filters")
        date_range = st.date_input(
            "Select Date Range",
            value=(datetime.now(), datetime.now()),
            key="date_filter"
        )

        category_filter = st.multiselect(
            "Category",
            ["Solar", "Wind", "Hybrid"],
            default=["Solar", "Wind"]
        )

        use_live_data = st.checkbox("Use Live Weather Data", value=True)
        show_confidence_interval = st.checkbox("Show Prediction Confidence Interval", value=True)
        forecast_days = st.number_input("Forecast Days", min_value=1, max_value=30, value=7)

    authenticator.logout('Logout', 'sidebar')

    # Main screen content
    st.write(f'Welcome *{st.session_state["name"]}*')
    
    # ashutosh code for main area content of dashboard

    # Main content area
    st.title("Renewable Energy Dashboard")
    
    if st.session_state.active_tab == "Overview":
        # Create layout for map and location info
        map_col, info_col = st.columns([2, 1])
        
        with map_col:
            st.subheader("Select Location")
            if st.button("Reset to Default Location"):
                st.session_state.latitude = 28.6139
                st.session_state.longitude = 77.2090
                st.rerun()
            
            # Create the map
            m = folium.Map(
                location=[st.session_state.latitude, st.session_state.longitude],
                zoom_start=4,
                tiles="CartoDB positron"
            )
            
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
    
            # Display map and handle clicks
            map_data = st_folium(m, height=400, width=None, returned_objects=["last_clicked"])
            
            if (map_data and 'last_clicked' in map_data and map_data['last_clicked']):
                new_lat = map_data['last_clicked']['lat']
                new_lng = map_data['last_clicked']['lng']
                if (abs(new_lat - st.session_state.latitude) > 0.0001 or 
                    abs(new_lng - st.session_state.longitude) > 0.0001):
                    st.session_state.latitude = new_lat
                    st.session_state.longitude = new_lng
                    st.rerun()
    
        with info_col:
            st.subheader("Location Information")
            try:
                location_info = st.session_state.weather_service.get_location_info(
                    st.session_state.latitude, 
                    st.session_state.longitude
                )
                st.success(
                    f"📍 **Location**: {location_info['location_name']}\n\n"
                    f"🌍 **Coordinates**:\n"
                    f"- Latitude: {st.session_state.latitude:.4f}°\n"
                    f"- Longitude: {st.session_state.longitude:.4f}°"
                )
            except Exception as e:
                st.error("Unable to fetch location details. Please try again.")
    
        # Get weather data and display forecasts
        if use_live_data:
            weather_data = st.session_state.weather_service.get_weather_forecast(
                st.session_state.latitude,
                st.session_state.longitude,
                forecast_days
            )
        else:
            weather_data = simulate_weather_data(forecast_days)
    
        # Initialize models
        solar_model = SolarForecastModel()
        wind_model = WindForecastModel()
        solar_model.models = solar_model.create_ensemble()
        wind_model.models = wind_model.create_ensemble()
    
        # Process and display results using the shared functionality from app.py
        process_and_display_results(
            weather_data,
            solar_model,
            wind_model,
            location_info=location_info,
            show_confidence_interval=show_confidence_interval
        )
    
    elif st.session_state.active_tab == "Analytics":
        st.header("Advanced Analytics")
        # Add your analytics content here
        st.info("Analytics features coming soon!")
    
    elif st.session_state.active_tab == "Reports":
        st.header("Reports")
        # Add your reports content here
        st.info("Reporting features coming soon!")
    
    elif st.session_state.active_tab == "Settings":
        st.header("Settings")
        # Add your settings content here
        with st.expander("Application Settings"):
            st.checkbox("Enable Dark Mode", value=False)
            st.checkbox("Enable Notifications", value=True)
            st.selectbox("Update Frequency", ["Real-time", "Hourly", "Daily"])
    
        with st.expander("Data Sources"):
            st.text_input("Weather API Key")
            st.text_input("Database Connection String")
            st.button("Test Connections")
    
    


else:
    st.sidebar.markdown("<h1 style='text-align: center; color: #4CAF50;'>Navigation</h1>", unsafe_allow_html=True)

    page = st.sidebar.radio("", ["Login", "Register", "Forgot Password", "Forgot Username"], index=0, key="navigation")

# Login page
if page == "Login":
    try:
        authenticator.login()
    except LoginError as e:
        st.error(e)

    # Authenticating user
    if st.session_state['authentication_status']:
        # st.sidebar.markdown(f"<h2 style='text-align: center; color: #4CAF50;'>Welcome {st.session_state['name']}</h2>", unsafe_allow_html=True)
        authenticator.logout('Logout', 'sidebar')

        # center content of dashboard
        

        # Centered content on the main screen
        st.markdown("<div style='text-align: center;'><h1>Welcome to the NTPC Renewable Energy Dashboard</h1><p>Here is some centered content after logging in.</p></div>", unsafe_allow_html=True)

    elif st.session_state['authentication_status'] is False:
        st.error('Username/password is incorrect')
    elif st.session_state['authentication_status'] is None:
        st.warning('Please enter your username and password')

# Registration page
elif page == "Register":
    try:
        (email_of_registered_user,
            username_of_registered_user,
            name_of_registered_user) = authenticator.register_user(clear_on_submit=True, fields=['username', 'name', 'email', 'password'])
        if email_of_registered_user:
            st.success('User registered successfully')
    except RegisterError as e:
        st.error(e)

# Forgot Password page
elif page == "Forgot Password":
    try:
        (username_of_forgotten_password,
            email_of_forgotten_password,
            new_random_password) = authenticator.forgot_password()
        if username_of_forgotten_password:
            st.success('New password sent securely')
            # Random password to be transferred to the user securely
        elif not username_of_forgotten_password:
            st.error('Username not found')
    except ForgotError as e:
        st.error(e)

# Forgot Username page
elif page == "Forgot Username":
    try:
        (username_of_forgotten_username,
            email_of_forgotten_username) = authenticator.forgot_username()
        if username_of_forgotten_username:
            st.success('Username sent securely')
            # Username to be transferred to the user securely
        elif not username_of_forgotten_username:
            st.error('Email not found')
    except ForgotError as e:
        st.error(e)

# Saving config file
with open('./config.yaml', 'w', encoding='utf-8') as file:
    yaml.dump(config, file, default_flow_style=False)