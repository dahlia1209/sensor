#!/usr/bin/env python3
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
import subprocess
import os

app = FastAPI()

IRRP = os.path.expanduser("~/src/sensor/irrp.py")
CODES = os.path.expanduser("~/src/sensor/codes")
GPIO = "18"

ALLOWED_KEYS = [
    "aircon:cool", "aircon:heat", "aircon:dry", "aircon:off",
    "aircon:temp_up", "aircon:temp_down", "aircon:wind_volume",
    "aircon:wind_direction", "aircon:timer_on", "aircon:sleep_off",
    "aircon:clean", "light:on", "light:off", "tv:on", "tv:off"
]

def send_ir(key: str) -> bool:
    result = subprocess.run(
        ["python3", IRRP, "-p", f"-g{GPIO}", "-f", CODES, key],
        capture_output=True, text=True
    )
    return result.returncode == 0


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTML_CONTENT


@app.get("/send/{key}")
async def send(key: str):
    if key not in ALLOWED_KEYS:
        return JSONResponse({"success": False, "error": "不正なキー"}, status_code=400)
    success = send_ir(key)
    return {"success": success, "key": key}


HTML_CONTENT = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>スマートリモコン</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@700;800&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg: #0f0f0f;
    --surface: #1a1a1a;
    --border: #2a2a2a;
    --text: #e8e8e8;
    --muted: #555;
    --accent-red: #ff3b3b;
    --accent-blue: #3b8eff;
    --accent-green: #2dca73;
    --accent-yellow: #f5c518;
    --accent-purple: #a78bfa;
    --accent-orange: #ff7c3b;
  }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'DM Mono', monospace;
    min-height: 100vh;
    padding: 24px 16px 48px;
  }

  header {
    text-align: center;
    margin-bottom: 32px;
    padding-bottom: 24px;
    border-bottom: 1px solid var(--border);
  }

  header h1 {
    font-family: 'Syne', sans-serif;
    font-size: 28px;
    font-weight: 800;
    letter-spacing: -0.5px;
    color: var(--text);
  }

  header p {
    font-size: 11px;
    color: var(--muted);
    margin-top: 4px;
    letter-spacing: 2px;
    text-transform: uppercase;
  }

  .container {
    max-width: 480px;
    margin: 0 auto;
  }

  .section {
    margin-bottom: 28px;
  }

  .section-title {
    font-size: 10px;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 12px;
    padding-left: 2px;
  }

  .grid {
    display: grid;
    gap: 8px;
  }

  .grid-2 { grid-template-columns: 1fr 1fr; }
  .grid-3 { grid-template-columns: 1fr 1fr 1fr; }

  button {
    background: var(--surface);
    border: 1px solid var(--border);
    color: var(--text);
    font-family: 'DM Mono', monospace;
    font-size: 12px;
    padding: 14px 10px;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.15s ease;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    line-height: 1.3;
    text-align: center;
  }

  button .icon { font-size: 18px; }
  button .label { font-size: 11px; color: var(--muted); }

  button:active { transform: scale(0.96); }

  button:hover { border-color: #444; background: #222; }

  button.red    { border-color: var(--accent-red);    color: var(--accent-red); }
  button.blue   { border-color: var(--accent-blue);   color: var(--accent-blue); }
  button.green  { border-color: var(--accent-green);  color: var(--accent-green); }
  button.yellow { border-color: var(--accent-yellow); color: var(--accent-yellow); }
  button.purple { border-color: var(--accent-purple); color: var(--accent-purple); }
  button.orange { border-color: var(--accent-orange); color: var(--accent-orange); }

  button.red:hover    { background: rgba(255,59,59,0.1); }
  button.blue:hover   { background: rgba(59,142,255,0.1); }
  button.green:hover  { background: rgba(45,202,115,0.1); }
  button.yellow:hover { background: rgba(245,197,24,0.1); }
  button.purple:hover { background: rgba(167,139,250,0.1); }
  button.orange:hover { background: rgba(255,124,59,0.1); }

  #toast {
    position: fixed;
    bottom: 24px;
    left: 50%;
    transform: translateX(-50%) translateY(80px);
    background: var(--surface);
    border: 1px solid var(--border);
    color: var(--text);
    font-family: 'DM Mono', monospace;
    font-size: 12px;
    padding: 10px 20px;
    border-radius: 100px;
    transition: transform 0.3s ease, opacity 0.3s ease;
    opacity: 0;
    white-space: nowrap;
    z-index: 100;
  }

  #toast.show {
    transform: translateX(-50%) translateY(0);
    opacity: 1;
  }

  #toast.ok  { border-color: var(--accent-green); color: var(--accent-green); }
  #toast.err { border-color: var(--accent-red);   color: var(--accent-red); }
</style>
</head>
<body>
<div class="container">
  <header>
    <h1>🏠 Smart Remote</h1>
    <p>Raspberry Pi IR Controller</p>
  </header>

  <!-- エアコン メイン -->
  <div class="section">
    <div class="section-title">❄️ Air Conditioner</div>
    <div class="grid grid-3">
      <button class="blue"   onclick="send('aircon:cool')">  <span class="icon">❄️</span><span class="label">冷房</span></button>
      <button class="red"    onclick="send('aircon:heat')">  <span class="icon">🔥</span><span class="label">暖房</span></button>
      <button class="purple" onclick="send('aircon:dry')">   <span class="icon">💧</span><span class="label">除湿</span></button>
    </div>
  </div>

  <!-- エアコン 停止 -->
  <div class="section">
    <div class="grid">
      <button class="orange" onclick="send('aircon:off')"><span class="icon">⏹</span><span class="label">停止</span></button>
    </div>
  </div>

  <!-- エアコン 温度・風量 -->
  <div class="section">
    <div class="section-title">🌡️ Temperature / Fan</div>
    <div class="grid grid-2">
      <button onclick="send('aircon:temp_up')">        <span class="icon">🌡️▲</span><span class="label">温度UP</span></button>
      <button onclick="send('aircon:temp_down')">      <span class="icon">🌡️▼</span><span class="label">温度DOWN</span></button>
      <button onclick="send('aircon:wind_volume')">    <span class="icon">💨</span><span class="label">風量</span></button>
      <button onclick="send('aircon:wind_direction')"> <span class="icon">↕️</span><span class="label">風向</span></button>
    </div>
  </div>

  <!-- エアコン タイマー・その他 -->
  <div class="section">
    <div class="section-title">⏰ Timer / Other</div>
    <div class="grid grid-3">
      <button onclick="send('aircon:timer_on')">  <span class="icon">⏰</span><span class="label">入タイマー</span></button>
      <button onclick="send('aircon:sleep_off')"> <span class="icon">😴</span><span class="label">おやすみ切</span></button>
      <button onclick="send('aircon:clean')">     <span class="icon">🧹</span><span class="label">内部洗浄</span></button>
    </div>
  </div>

  <!-- 照明 -->
  <div class="section">
    <div class="section-title">💡 Living Light</div>
    <div class="grid grid-2">
      <button class="yellow" onclick="send('light:on')">  <span class="icon">💡</span><span class="label">ON</span></button>
      <button                onclick="send('light:off')"> <span class="icon">🌑</span><span class="label">OFF</span></button>
    </div>
  </div>

  <!-- テレビ -->
  <div class="section">
    <div class="section-title">📺 TV</div>
    <div class="grid grid-2">
      <button class="green" onclick="send('tv:on')">  <span class="icon">📺</span><span class="label">ON</span></button>
      <button               onclick="send('tv:off')"> <span class="icon">⏻</span><span class="label">OFF</span></button>
    </div>
  </div>
</div>

<div id="toast"></div>

<script>
  let toastTimer;

  async function send(key) {
    showToast('送信中...', '');
    try {
      const res = await fetch(`/send/${key}`);
      const data = await res.json();
      if (data.success) {
        showToast('✓ ' + key, 'ok');
      } else {
        showToast('✗ 失敗: ' + key, 'err');
      }
    } catch(e) {
      showToast('✗ 通信エラー', 'err');
    }
  }

  function showToast(msg, type) {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.className = 'show ' + type;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { t.className = ''; }, 2500);
  }
</script>
</body>
</html>
"""
