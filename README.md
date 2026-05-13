# KL Weather Analyser

吉隆坡当前天气 + 未来几天预报。两个版本:

- **`streamlit_app.py`** — Streamlit 版,可一键部署到 Streamlit Cloud,带侧边栏调坐标/天数、10 分钟缓存、温度/降水/湿度/风速分图。**推荐用这个。**
- **`app.py`** — 原始 Flask 版,Chart.js 折线图,适合传统 web host。

需要一个 Weatherbit 免费 key(https://www.weatherbit.io/account/create 申请,免费层每天 50 次调用够练手)。

## Streamlit 版本(推荐)

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

打开 `http://localhost:8501`,在 sidebar 填 Weatherbit key 就能跑。

部署到 Streamlit Cloud:

1. push 到 GitHub
2. https://share.streamlit.io/ → New app → 选这个 repo
3. Main file path: `streamlit_app.py`
4. 部署后进 app Settings → Secrets,加一行 `WEATHERBIT_API_KEY = "你的key"`

## Flask 版本(原版)

```bash
export WEATHERBIT_API_KEY=你的key
python app.py
```

打开 `http://localhost:5000`。Procfile 已经在,部署到 Heroku / Railway / Render 都行,环境变量设 `WEATHERBIT_API_KEY`。

## 改地点

Streamlit 版本: sidebar 直接调 lat/lon。
Flask 版本: 坐标写死在 `app.py` 顶部(LAT/LON 两行)。

## 已知问题

- Streamlit 版加了 10 分钟缓存,Flask 版没缓存——每次刷新都打 API,免费层很快用完配额。
- Flask 版错误处理基础,key 失效页面是空白。Streamlit 版有明确的错误提示。

## 协议

MIT。
