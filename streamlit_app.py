"""
KL Weather Analyser — Streamlit version.

吉隆坡天气仪表盘:当前实况 + 多日预报 + 折线图。
数据来自 Weatherbit API。
"""

import os
from datetime import datetime

import pandas as pd
import requests
import streamlit as st

# ──────────────────────────────────────────────────────────────────────
# Page config
# ──────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="KL Weather Analyser",
    page_icon="🌤",
    layout="wide",
)

# ──────────────────────────────────────────────────────────────────────
# API key: secrets > env > sidebar input
# ──────────────────────────────────────────────────────────────────────
def _resolve_api_key() -> str | None:
    try:
        return st.secrets["WEATHERBIT_API_KEY"]
    except Exception:
        pass
    if os.environ.get("WEATHERBIT_API_KEY"):
        return os.environ["WEATHERBIT_API_KEY"]
    return None


API_KEY = _resolve_api_key()

# ──────────────────────────────────────────────────────────────────────
# Sidebar — config
# ──────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Settings")
    if not API_KEY:
        API_KEY = st.text_input(
            "Weatherbit API key",
            type="password",
            help="https://www.weatherbit.io/account/create 免费申请,免费层每天 50 次。",
        )
    else:
        st.success("Key 来自 Streamlit secrets,无需输入")

    st.markdown("---")
    st.caption("Location")
    lat = st.number_input("Latitude", value=3.139, step=0.001, format="%.4f")
    lon = st.number_input("Longitude", value=101.6869, step=0.001, format="%.4f")
    forecast_days = st.slider("预报天数", min_value=3, max_value=10, value=7)

    st.markdown("---")
    st.caption(
        "默认坐标是吉隆坡市中心。改 lat/lon 看别的城市。"
    )

# ──────────────────────────────────────────────────────────────────────
# Data fetch (cached for 10 minutes)
# ──────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=600, show_spinner=False)
def fetch_current(api_key: str, lat: float, lon: float):
    r = requests.get(
        "https://api.weatherbit.io/v2.0/current",
        params={"lat": lat, "lon": lon, "key": api_key},
        timeout=10,
    )
    r.raise_for_status()
    data = r.json()
    if not data.get("data"):
        return None
    return data["data"][0]


@st.cache_data(ttl=600, show_spinner=False)
def fetch_forecast(api_key: str, lat: float, lon: float, days: int):
    r = requests.get(
        "https://api.weatherbit.io/v2.0/forecast/daily",
        params={"lat": lat, "lon": lon, "key": api_key, "days": days},
        timeout=10,
    )
    r.raise_for_status()
    return r.json().get("data", [])

# ──────────────────────────────────────────────────────────────────────
# Page header
# ──────────────────────────────────────────────────────────────────────
st.title("🌤 Kuala Lumpur Weather Analyser")
st.caption("Real-time weather + multi-day forecast · powered by Weatherbit")

if not API_KEY:
    st.warning("👈 在左边 sidebar 填一个 Weatherbit API key,或在 Streamlit Secrets 里设 `WEATHERBIT_API_KEY`。")
    st.stop()

# ──────────────────────────────────────────────────────────────────────
# Current
# ──────────────────────────────────────────────────────────────────────
try:
    current = fetch_current(API_KEY, lat, lon)
except requests.HTTPError as e:
    st.error(f"API 返回错误: HTTP {e.response.status_code}。Key 是否有效?")
    st.stop()
except Exception as e:
    st.error(f"获取实况失败: {e}")
    st.stop()

if not current:
    st.warning("API 没返回数据,可能坐标没数据点。")
    st.stop()

city_name = current.get("city_name", "—")
station = current.get("station", "—")
st.subheader(f"📍 {city_name}  ·  station {station}")

cols = st.columns(5)
cols[0].metric("Temperature", f"{current.get('temp', '—')} °C", f"feels {current.get('app_temp', '—')} °C")
cols[1].metric("Humidity", f"{current.get('rh', '—')} %")
cols[2].metric("Wind", f"{current.get('wind_spd', '—')} m/s", current.get("wind_cdir", ""))
cols[3].metric("Pressure", f"{current.get('pres', '—')} mb")
cols[4].metric("UV index", f"{current.get('uv', '—')}")

st.caption(f"Observed at: {current.get('ob_time', '—')}  ·  Weather: {current.get('weather', {}).get('description', '—')}")

# ──────────────────────────────────────────────────────────────────────
# Forecast
# ──────────────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader(f"📅 Forecast — next {forecast_days} days")

try:
    forecast = fetch_forecast(API_KEY, lat, lon, forecast_days)
except Exception as e:
    st.error(f"获取预报失败: {e}")
    forecast = []

if not forecast:
    st.info("没有预报数据。")
else:
    df = pd.DataFrame([
        {
            "Date": d.get("datetime"),
            "High (°C)": d.get("max_temp"),
            "Low (°C)": d.get("min_temp"),
            "Mean (°C)": d.get("temp"),
            "Precipitation (mm)": d.get("precip"),
            "Humidity (%)": d.get("rh"),
            "Wind (m/s)": d.get("wind_spd"),
            "Condition": (d.get("weather") or {}).get("description", "—"),
        }
        for d in forecast
    ])

    tab_chart, tab_table = st.tabs(["Charts", "Raw table"])

    with tab_chart:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Temperature range**")
            st.line_chart(df.set_index("Date")[["High (°C)", "Mean (°C)", "Low (°C)"]])
        with c2:
            st.markdown("**Precipitation & humidity**")
            st.bar_chart(df.set_index("Date")[["Precipitation (mm)"]])
            st.line_chart(df.set_index("Date")[["Humidity (%)"]])

        st.markdown("**Wind speed**")
        st.area_chart(df.set_index("Date")[["Wind (m/s)"]])

    with tab_table:
        st.dataframe(df, use_container_width=True, hide_index=True)

st.markdown("---")
st.caption(
    f"Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}  ·  "
    "Data cached for 10 minutes to spare your free-tier quota."
)
