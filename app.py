from flask import Flask, jsonify, render_template_string
import requests
import os

app = Flask(__name__)

API_KEY = os.environ.get("WEATHERBIT_API_KEY", "")  # 部署时通过环境变量注入
LAT = 3.139
LON = 101.6869
TIMEOUT = 10

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>KL Weather Analyser</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Segoe UI', sans-serif; background: #f0f4f8; color: #1a202c; min-height: 100vh; }
  header { background: #1F4E79; color: white; padding: 24px 40px; }
  header h1 { font-size: 22px; font-weight: 600; }
  header p { font-size: 13px; opacity: 0.75; margin-top: 4px; }
  main { max-width: 960px; margin: 0 auto; padding: 40px 24px; }
  .current-card {
    background: white; border-radius: 16px; padding: 28px 32px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08); margin-bottom: 32px;
    display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 20px;
  }
  .stat { text-align: center; }
  .stat .val { font-size: 32px; font-weight: 700; color: #1F4E79; }
  .stat .label { font-size: 12px; color: #718096; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.05em; }
  .chart-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
  .chart-card { background: white; border-radius: 16px; padding: 24px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); }
  .chart-card h2 { font-size: 15px; font-weight: 600; color: #2d3748; margin-bottom: 16px; }
  .loading { text-align: center; padding: 60px; color: #718096; font-size: 16px; }
  .error { background: #fff5f5; border: 1px solid #fed7d7; color: #c53030; border-radius: 12px; padding: 20px; }
  @media (max-width: 640px) { .chart-grid { grid-template-columns: 1fr; } }
</style>
</head>
<body>
<header>
  <h1>🌤 Kuala Lumpur Weather Analyser</h1>
  <p>Real-time weather data powered by Weatherbit API</p>
</header>
<main>
  <div id="content"><div class="loading">Loading weather data...</div></div>
</main>
<script>
async function load() {
  try {
    const res = await fetch('/api/weather');
    const data = await res.json();
    if (!data.success) throw new Error(data.error);

    const c = data.current;
    const f = data.forecast;
    const dates = f.map(d => d.date);
    const temps = f.map(d => d.temp);

    document.getElementById('content').innerHTML = `
      <div class="current-card">
        <div class="stat"><div class="val">${c.temperature}°C</div><div class="label">Temperature</div></div>
        <div class="stat"><div class="val">${c.feels_like}°C</div><div class="label">Feels Like</div></div>
        <div class="stat"><div class="val">${c.humidity}%</div><div class="label">Humidity</div></div>
        <div class="stat"><div class="val">${c.wind_speed} m/s</div><div class="label">Wind Speed</div></div>
        <div class="stat"><div class="val" style="font-size:16px;padding-top:8px">${c.description}</div><div class="label">Condition</div></div>
      </div>
      <div class="chart-grid">
        <div class="chart-card"><h2>📈 7-Day Temperature Trend</h2><canvas id="lineChart"></canvas></div>
        <div class="chart-card"><h2>📊 Daily Temperature Comparison</h2><canvas id="barChart"></canvas></div>
      </div>
    `;

    const colors = temps.map(t => t > 30 ? '#E53E3E' : t > 25 ? '#DD6B20' : '#3182CE');

    new Chart(document.getElementById('lineChart'), {
      type: 'line',
      data: { labels: dates, datasets: [{ label: 'Temp (°C)', data: temps, borderColor: '#1F4E79', backgroundColor: 'rgba(31,78,121,0.1)', tension: 0.4, pointBackgroundColor: '#1F4E79', pointRadius: 5 }] },
      options: { responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: false } } }
    });

    new Chart(document.getElementById('barChart'), {
      type: 'bar',
      data: { labels: dates, datasets: [{ label: 'Temp (°C)', data: temps, backgroundColor: colors }] },
      options: { responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: false } } }
    });

  } catch(e) {
    document.getElementById('content').innerHTML = `<div class="error">⚠️ ${e.message}</div>`;
  }
}
load();
</script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/api/weather')
def weather():
    try:
        cur_url = f'https://api.weatherbit.io/v2.0/current?lat={LAT}&lon={LON}&key={API_KEY}&units=M'
        fc_url  = f'https://api.weatherbit.io/v2.0/forecast/daily?lat={LAT}&lon={LON}&key={API_KEY}&units=M&days=7'

        cur_res = requests.get(cur_url, timeout=TIMEOUT)
        fc_res  = requests.get(fc_url, timeout=TIMEOUT)
        cur_res.raise_for_status()
        fc_res.raise_for_status()

        w = cur_res.json()['data'][0]
        current = {
            'temperature': round(w['temp'], 1),
            'feels_like':  round(w['app_temp'], 1),
            'humidity':    w['rh'],
            'description': w['weather']['description'],
            'wind_speed':  round(w['wind_spd'], 1),
        }

        forecast = [
            {'date': d['datetime'][5:], 'temp': round(d['temp'], 1), 'desc': d['weather']['description']}
            for d in fc_res.json()['data']
        ]

        return jsonify({'success': True, 'current': current, 'forecast': forecast})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=False)
