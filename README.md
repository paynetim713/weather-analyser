# KL Weather Analyser

吉隆坡当前天气 + 未来几天预报。两个版本:

- **`streamlit_app.py`** — Streamlit 版,推荐部署到 Streamlit Cloud。带 Test connection 按钮、分类错误提示(key 无效 / 配额 / 网络 / 服务器错)、温度/降水/湿度/风速分图、坐标可调、3-16 天预报范围。**推荐用这个。**
- **`app.py`** — 原始 Flask 版,Chart.js 折线图,适合传统 web host。

需要一个 Weatherbit 免费 key——https://www.weatherbit.io/account/create 申请,免费层每天 50 次调用。

## Streamlit 版本(推荐)

### 本地跑

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

打开 `http://localhost:8501`,sidebar 填 key 或者:

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# 编辑 .streamlit/secrets.toml,填上你的 key
# 这个文件在 .gitignore 里,不会被提交
streamlit run streamlit_app.py
```

### 部署到 Streamlit Cloud

1. push 到 GitHub(如果还没的话)
2. 去 https://share.streamlit.io → Sign in with GitHub
3. **Create app** → **Deploy a public app from GitHub**
4. 选这个 repo,branch `main`
5. **Main file path**: `streamlit_app.py`
6. **App URL**: 随你起,比如 `weather-paynetim`(→ `weather-paynetim.streamlit.app`)
7. 点 **Deploy**,等 1-3 分钟构建
8. 部署完后,左下角 ⋮ → **Settings** → **Secrets** → 粘下面这一行 → **Save**

```toml
WEATHERBIT_API_KEY = "你的_weatherbit_key_字符串"
```

应用会自动 reload,sidebar 会显示"✓ Key 来自 Streamlit Secrets",访客**不用自己填 key**。

### 想确认 key 有效?

部署完打开 app,在 sidebar 点 **Test connection** 按钮——会做一次廉价的 current weather 调用,告诉你 key 是否有效、配额还有没有。

## Flask 版本(原版)

```bash
export WEATHERBIT_API_KEY=你的key
python app.py
```

打开 `http://localhost:5000`。Procfile 已经在,部署到 Heroku / Railway / Render 都行,环境变量设 `WEATHERBIT_API_KEY`。

## 改地点

Streamlit 版本: sidebar 直接调 lat/lon,预报天数滑块也在 sidebar。
Flask 版本: 坐标写死在 `app.py` 顶部(LAT/LON 两行)。

## 已知问题

- Streamlit 版每次刷新都重新打两次 API(current + forecast),没做缓存——免费层每天 50 次的话,刷个 25 下就到限了。要做缓存的话给 `fetch_current` / `fetch_forecast` 加 `@st.cache_data(ttl=600)` 装饰器即可。
- Flask 版错误处理基础,key 失效页面是空白。Streamlit 版有 4 种错误分类提示(key 无效 / 配额耗尽 / 网络问题 / 服务器错)。

## 协议

MIT。
