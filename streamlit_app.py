"""
KL Weather Analyser — Streamlit version.

吉隆坡天气仪表盘:当前实况 + 多日预报 + 折线图。
数据来自 Weatherbit API。

API key 优先级: Streamlit Secrets > 环境变量 > sidebar 输入。

UI 逻辑包在 main() 里,所以 `import streamlit_app` 测试时不会触发 Streamlit
页面渲染——只暴露纯函数(fetch_current / fetch_forecast / test_key / ...)。
"""

import os
from datetime import datetime

import pandas as pd
import requests
import streamlit as st


# ──────────────────────────────────────────────────────────────────────
# API key resolution
# ──────────────────────────────────────────────────────────────────────
def _resolve_api_key() -> tuple[str | None, str]:
    """Return (api_key, source). source ∈ {'secrets','env','none'}."""
    try:
        v = st.secrets["WEATHERBIT_API_KEY"]
        if v:
            return v, "secrets"
    except Exception:
        pass
    env = os.environ.get("WEATHERBIT_API_KEY")
    if env:
        return env, "env"
    return None, "none"


# ──────────────────────────────────────────────────────────────────────
# HTTP layer with typed errors
# ──────────────────────────────────────────────────────────────────────
class WeatherbitError(Exception):
    """Wrap all failure modes so UI renders the right message."""

    def __init__(self, kind: str, message: str):
        super().__init__(message)
        self.kind = kind   # auth / quota / network / no_data / other
        self.message = message


def _request(url: str, params: dict, timeout: int = 10) -> dict:
    try:
        r = requests.get(url, params=params, timeout=timeout)
    except requests.Timeout:
        raise WeatherbitError("network", "请求超时(10秒)。Weatherbit 暂时无响应。")
    except requests.ConnectionError:
        raise WeatherbitError("network", "网络连不上。检查一下你的网络。")

    if r.status_code in (401, 403):
        raise WeatherbitError(
            "auth",
            f"API key 无效或权限不足(HTTP {r.status_code})。请检查 Streamlit Secrets 里的 "
            "WEATHERBIT_API_KEY,或在 sidebar 重新填写。",
        )
    if r.status_code == 429:
        raise WeatherbitError("quota", "API 配额已用完(免费层每天 50 次)。明天再试或升级套餐。")
    if r.status_code >= 500:
        raise WeatherbitError("other", f"Weatherbit 服务器错误(HTTP {r.status_code})。可能是他们临时挂了。")
    if r.status_code != 200:
        raise WeatherbitError("other", f"未知错误: HTTP {r.status_code} — {r.text[:200]}")

    try:
        return r.json()
    except ValueError:
        raise WeatherbitError("other", "API 返回的不是合法 JSON。")


def fetch_current(api_key: str, lat: float, lon: float) -> dict:
    data = _request(
        "https://api.weatherbit.io/v2.0/current",
        params={"lat": lat, "lon": lon, "key": api_key},
    )
    items = data.get("data") or []
    if not items:
        raise WeatherbitError("no_data", "该坐标暂无观测站数据。")
    return items[0]


def fetch_forecast(api_key: str, lat: float, lon: float, days: int) -> list:
    data = _request(
        "https://api.weatherbit.io/v2.0/forecast/daily",
        params={"lat": lat, "lon": lon, "key": api_key, "days": days},
    )
    return data.get("data") or []


def test_key(api_key: str) -> tuple[bool, str]:
    if not api_key:
        return False, "Key 为空"
    try:
        fetch_current(api_key, 3.139, 101.6869)
        return True, "Key 有效"
    except WeatherbitError as e:
        return False, e.message
    except Exception as e:
        return False, f"未知错误: {e}"


# ──────────────────────────────────────────────────────────────────────
# UI
# ──────────────────────────────────────────────────────────────────────
def main() -> None:
    st.set_page_config(
        page_title="KL Weather Analyser",
        page_icon="🌤",
        layout="wide",
    )

    initial_key, key_source = _resolve_api_key()

    # ── Sidebar ──
    with st.sidebar:
        st.header("Settings")

        if initial_key:
            if key_source == "secrets":
                st.success("✓ Key 来自 Streamlit Secrets")
            elif key_source == "env":
                st.success("✓ Key 来自环境变量")
            api_key = initial_key
            override = st.text_input(
                "覆盖 key(可选)",
                type="password",
                help="想临时用别的 key,在这里粘。留空则使用 Secrets 里的。",
            )
            if override.strip():
                api_key = override.strip()
        else:
            st.info(
                "还没配 Key。部署到 Streamlit Cloud 后请在 app Settings → Secrets 里加 "
                "`WEATHERBIT_API_KEY`。本地开发也可以直接在下面填。"
            )
            api_key = st.text_input(
                "Weatherbit API key",
                type="password",
                help="https://www.weatherbit.io/account/create 免费申请,免费层每天 50 次。",
            ).strip()

        if api_key:
            if st.button("Test connection"):
                with st.spinner("Testing..."):
                    ok, msg = test_key(api_key)
                if ok:
                    st.success(f"✓ {msg}")
                else:
                    st.error(f"✗ {msg}")

        st.markdown("---")
        st.caption("Location")
        lat = st.number_input("Latitude", value=3.139, step=0.001, format="%.4f")
        lon = st.number_input("Longitude", value=101.6869, step=0.001, format="%.4f")
        forecast_days = st.slider("预报天数", min_value=3, max_value=16, value=7)

        st.markdown("---")
        st.caption("默认是吉隆坡市中心。改 lat/lon 看别的城市。免费层每天 50 次调用——多刷新会被风控。")

    # ── Header + early exit ──
    st.title("🌤 Kuala Lumpur Weather Analyser")
    st.caption("Real-time weather + multi-day forecast · powered by Weatherbit")

    if not api_key:
        st.warning(
            "👈 左边 sidebar 填 Weatherbit key,或在 Streamlit Cloud 的 Secrets 里加 "
            "`WEATHERBIT_API_KEY`。"
        )
        st.stop()

    # ── Current ──
    try:
        with st.spinner("Fetching current weather..."):
            current = fetch_current(api_key, lat, lon)
    except WeatherbitError as e:
        if e.kind == "auth":
            st.error(f"🔑 {e.message}")
            st.info("没有 key 的话去 https://www.weatherbit.io/account/create 申请,免费,30 秒。")
        elif e.kind == "quota":
            st.error(f"📊 {e.message}")
        else:
            st.error(e.message)
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

    weather_desc = (current.get("weather") or {}).get("description", "—")
    st.caption(f"Observed at: {current.get('ob_time', '—')}  ·  Weather: {weather_desc}")

    # ── Forecast ──
    st.markdown("---")
    st.subheader(f"📅 Forecast — next {forecast_days} days")

    try:
        with st.spinner("Fetching forecast..."):
            forecast = fetch_forecast(api_key, lat, lon, forecast_days)
    except WeatherbitError as e:
        st.error(f"预报获取失败: {e.message}")
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
    st.caption(f"Last refreshed: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")


if __name__ == "__main__":
    main()
