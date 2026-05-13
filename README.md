# KL Weather Analyser

Flask 小项目，把 Weatherbit 的天气 API 拿来包一层好看的前端：吉隆坡当前天气 + 未来几天预报，用 Chart.js 画折线图。

学校作业里需要一个调外部 API 的网页 demo，挑了这个题目顺手做了一下。

## 跑起来

需要一个 Weatherbit 免费 key（https://www.weatherbit.io/account/create 申请，免费层每天 50 次调用够练手）。

```bash
pip install -r requirements.txt
export WEATHERBIT_API_KEY=你的key
python app.py
```

或者一行：

```bash
WEATHERBIT_API_KEY=xxx python app.py
```

打开 `http://localhost:5000`。

## 部署

Heroku 风格的 Procfile 已经在仓库里了：

```
web: gunicorn app:app
```

部署到 Heroku / Railway / Render 时把 `WEATHERBIT_API_KEY` 填到环境变量里。

## 改地点

坐标写死在 `app.py` 顶部：

```python
LAT = 3.139      # 吉隆坡
LON = 101.6869
```

想看别的城市，改这两个数。或者顺手把它做成 URL 参数也行——我没做是因为这个 demo 范围就到这。

## 已知问题

- 没有任何缓存，每次刷新都打一次 API。免费层会很快用完配额。
- 错误处理很基础，API key 失效的话页面就是空白。

## 协议

MIT。
