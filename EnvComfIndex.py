import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
import pytz

# --- 1. CONFIGURATION ---
FIREBASE_URL = "https://staycomfee-9f647-default-rtdb.asia-southeast1.firebasedatabase.app/Live.json"
API_KEY = "d5e7bccdeb454246b5a4e72834de60c7" 
CITY = "Mumbai" 

st.set_page_config(page_title="StayCOMFIEE", layout="wide")

# --- 2. CSS STYLING ---
st.markdown("""
    <style>
    .glass-card { 
        background: rgba(128, 128, 128, 0.1); 
        border-radius: 15px; 
        padding: 20px; 
        border: 1px solid rgba(128, 128, 128, 0.2); 
        margin-bottom: 15px; 
    }
    
    /* --- NEW ALARM ANIMATIONS & STYLING --- */
    @keyframes pulse-border {
        0% { box-shadow: 0 0 0 0 rgba(255, 75, 75, 0.7); }
        70% { box-shadow: 0 0 0 15px rgba(255, 75, 75, 0); }
        100% { box-shadow: 0 0 0 0 rgba(255, 75, 75, 0); }
    }
    .alert-card {
        background: linear-gradient(135deg, #ff4b4b 0%, #a70000 100%);
        color: white;
        padding: 25px;
        border-radius: 15px;
        text-align: center;
        border: 2px solid #ff4b4b;
        margin-bottom: 25px;
        animation: pulse-border 2s infinite;
    }
    .alert-card h2 {
        color: white !important;
        margin-top: 0;
        margin-bottom: 10px;
        font-size: 32px;
        font-weight: 900;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    .alert-card .alert-reason {
        font-size: 22px;
        font-weight: 600;
        margin-bottom: 15px;
        background: rgba(0,0,0,0.2);
        padding: 8px 15px;
        border-radius: 8px;
        display: inline-block;
    }
    .alert-card .alert-stats {
        font-size: 20px;
        font-family: monospace;
        background: rgba(255,255,255,0.15);
        padding: 12px;
        border-radius: 8px;
        margin: 0;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. FUNCTIONS ---
@st.cache_data(ttl=600)
def get_weather(city, api_key):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        res = requests.get(url).json()
        return {
            "temp": res['main']['temp'], 
            "hum": res['main']['humidity'], 
            "desc": res['weather'][0]['description'].title()
        }
    except:
        return {"temp": "N/A", "hum": "N/A", "desc": "Offline"}

def circular_gauge(label, value, max_val, color="#58a6ff"):
    try:
        val_float = float(value)
    except:
        val_float = 0
    percent = min((val_float / max_val) * 100, 100)
    dash = f"{percent}, 100"
    return f"""
    <div style="text-align: center; display: flex; flex-direction: column; align-items: center;">
        <svg viewBox="0 0 36 36" style="width: 100px; height: 100px;">
            <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#888888" stroke-opacity="0.2" stroke-width="3" />
            <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="{color}" stroke-width="3" stroke-dasharray="{dash}" stroke-linecap="round" />
            <text x="18" y="21" text-anchor="middle" font-family="sans-serif" font-weight="bold" font-size="8" fill="white">{value}</text>
        </svg>
        <div style="color: gray; font-size: 10px; font-weight: bold; margin-top: -5px; text-transform: uppercase;">{label}</div>
    </div>
    """

# --- 4. UI INITIALIZATION ---
weather = get_weather(CITY, API_KEY)
st.title(f"🌍 StayCOMFIEE : {CITY}")

# Placeholder for the Alert Box
alert_box = st.empty() 

with st.sidebar:
    st.header("🔌 Cloud Connection")
    status_text = st.empty()
    if st.button("Force Cloud Refresh"):
        st.rerun()

col_left, col_right = st.columns([2, 1])

with col_left:
    st.markdown('<div class="glass-card"><b>🏠 INDOOR (LIVE CLOUD SENSOR)</b></div>', unsafe_allow_html=True)
    g1, g2, g3 = st.columns(3)
    gauge_air = g1.empty()
    gauge_temp = g2.empty()
    gauge_hum = g3.empty()

with col_right:
    st.markdown('<div class="glass-card"><b>☁️ OUTDOOR </b></div>', unsafe_allow_html=True)
    st.metric("Outdoor Temp", f"{weather['temp']}°C")
    st.metric("Outdoor Humidity", f"{weather['hum']}%")
    st.caption(f"Condition: {weather['desc']}")

st.subheader("📊 Live Cloud Streams")
c1, c2, c3 = st.columns(3)
chart_air = c1.empty()
chart_temp = c2.empty()
chart_hum = c3.empty()

if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=['Time', 'Air', 'Temp', 'Hum'])

# --- 5. CLOUD DATA LOOP ---
status_text.success("🟢 Connected to Firebase (Asia-Southeast1)")

while True:
    try:
        response = requests.get(FIREBASE_URL)
        
        if response.status_code == 200:
            data_cloud = response.json()
            
            if data_cloud:
                aq = int(data_cloud.get('Air', 0))
                t = float(data_cloud.get('Temp', 0.0))
                h = float(data_cloud.get('Hum', 0.0))
                
                ist_timezone = pytz.timezone('Asia/Kolkata')
                now = datetime.now(ist_timezone).strftime("%H:%M:%S")
                
                # --- VISUAL ALARM LOGIC ---
                if aq > 300 or t > 35 or h > 60:
                    alert_box.markdown(f"""
                        <div class="alert-card">
                            <h2>⚠️ CRITICAL ALERT ⚠️</h2>
                            <div class="alert-reason">Unsafe Environment Detected!</div>
                            <div class="alert-stats">Air: {aq} PPM &nbsp;&nbsp;|&nbsp;&nbsp; Temp: {t}°C &nbsp;&nbsp;|&nbsp;&nbsp; Hum: {h}%</div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    alert_box.empty()
                
                # Update Gauges
                aq_color = "#ff4b4b" if aq > 300 else "#58a6ff" 
                gauge_air.markdown(circular_gauge("PPM", aq, 1000, aq_color), unsafe_allow_html=True)
                gauge_temp.markdown(circular_gauge("°C", t, 50, "#ffa657"), unsafe_allow_html=True)
                gauge_hum.markdown(circular_gauge("%", h, 100, "#7ee787"), unsafe_allow_html=True)
                
                # Update History
                new_row = pd.DataFrame({'Time': [now], 'Air': [aq], 'Temp': [t], 'Hum': [h]})
                st.session_state.history = pd.concat([st.session_state.history, new_row]).tail(50)
                
                # Update Charts
                chart_air.area_chart(st.session_state.history.set_index('Time')[['Air']], color=aq_color)
                chart_temp.line_chart(st.session_state.history.set_index('Time')[['Temp']], color="#ffa657")
                chart_hum.line_chart(st.session_state.history.set_index('Time')[['Hum']], color="#7ee787")
                
        else:
            status_text.warning("Cloud Sync Delayed...")
            
    except Exception as e:
        status_text.error(f"⚠️ Network Error: {e}")
        
    time.sleep(5)
