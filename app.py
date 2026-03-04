from flask import Flask, request, jsonify, Response
from flask_socketio import SocketIO, emit
import threading
import requests
import socket
import time
import base64
import json
import os
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from datetime import datetime
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
HTML_CONTENT = """<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>FF Login Tool — Senzu</title>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;500;600;700&family=Orbitron:wght@400;700;900&display=swap" rel="stylesheet"/>
<script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.min.js"></script>
<style>
  :root {
    --bg: #050508;
    --bg2: #0a0a12;
    --bg3: #0f0f1a;
    --panel: rgba(10,10,20,0.85);
    --border: rgba(255,80,0,0.18);
    --border-hot: rgba(255,80,0,0.6);
    --accent: #ff5000;
    --accent2: #ff8c00;
    --accent3: #ffcc00;
    --text: #e8e0d0;
    --text-dim: #7a7060;
    --green: #00ff88;
    --cyan: #00e5ff;
    --red: #ff3366;
    --yellow: #ffcc00;
    --glow: 0 0 20px rgba(255,80,0,0.4);
    --glow2: 0 0 40px rgba(255,80,0,0.2);
  }

  * { margin:0; padding:0; box-sizing:border-box; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'Rajdhani', sans-serif;
    min-height: 100vh;
    overflow-x: hidden;
    position: relative;
  }

  /* ── Animated background grid */
  body::before {
    content:'';
    position:fixed; inset:0;
    background-image:
      linear-gradient(rgba(255,80,0,0.03) 1px, transparent 1px),
      linear-gradient(90deg, rgba(255,80,0,0.03) 1px, transparent 1px);
    background-size: 40px 40px;
    animation: grid-drift 20s linear infinite;
    pointer-events:none; z-index:0;
  }

  body::after {
    content:'';
    position:fixed; inset:0;
    background: radial-gradient(ellipse 80% 50% at 50% -10%, rgba(255,80,0,0.12) 0%, transparent 70%);
    pointer-events:none; z-index:0;
  }

  @keyframes grid-drift { from{background-position:0 0} to{background-position:40px 40px} }

  /* ── Scanlines */
  .scanlines {
    position:fixed; inset:0; pointer-events:none; z-index:999;
    background: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.03) 2px, rgba(0,0,0,0.03) 4px);
  }

  /* ── Layout */
  .container {
    position:relative; z-index:1;
    max-width: 1100px;
    margin: 0 auto;
    padding: 24px 20px 60px;
  }

  /* ── Header */
  header {
    text-align: center;
    padding: 40px 0 32px;
    position: relative;
  }

  .skull-icon {
    font-size: 2.8rem;
    display: block;
    margin-bottom: 12px;
    filter: drop-shadow(0 0 12px rgba(255,80,0,0.8));
    animation: pulse-glow 2s ease-in-out infinite;
  }

  @keyframes pulse-glow {
    0%,100%{ filter: drop-shadow(0 0 12px rgba(255,80,0,0.8)); }
    50%{ filter: drop-shadow(0 0 28px rgba(255,140,0,1)); }
  }

  h1 {
    font-family: 'Orbitron', monospace;
    font-size: clamp(1.6rem, 4vw, 2.8rem);
    font-weight: 900;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    background: linear-gradient(135deg, #ff5000 0%, #ffcc00 60%, #ff5000 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-size: 200% auto;
    animation: shine 3s linear infinite;
  }

  @keyframes shine { to { background-position: 200% center; } }

  .subtitle {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.78rem;
    color: var(--text-dim);
    letter-spacing: 0.3em;
    margin-top: 8px;
    text-transform: uppercase;
  }

  .subtitle span {
    color: var(--accent);
  }

  /* Decorative line */
  .deco-line {
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--accent), var(--accent3), var(--accent), transparent);
    margin: 28px 0;
    position: relative;
    overflow: visible;
  }
  .deco-line::before {
    content: '◆';
    position: absolute; left:50%; top:50%;
    transform: translate(-50%,-50%);
    color: var(--accent); font-size:10px;
    background: var(--bg);
    padding: 0 8px;
  }

  /* ── Grid layout */
  .grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    align-items: start;
  }

  @media(max-width:720px){ .grid{ grid-template-columns:1fr; } }

  /* ── Panel */
  .panel {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 4px;
    backdrop-filter: blur(12px);
    position: relative;
    overflow: hidden;
    transition: border-color 0.3s, box-shadow 0.3s;
  }

  .panel:hover { border-color: var(--border-hot); box-shadow: var(--glow2); }

  .panel::before {
    content:'';
    position:absolute; top:0; left:0; right:0; height:1px;
    background: linear-gradient(90deg, transparent, var(--accent), transparent);
  }

  /* Corner accents */
  .panel::after {
    content:'';
    position:absolute; bottom:0; right:0;
    width:30px; height:30px;
    border-bottom: 2px solid var(--accent);
    border-right: 2px solid var(--accent);
    opacity:0.4;
  }

  .corner-tl {
    position:absolute; top:0; left:0;
    width:30px; height:30px;
    border-top: 2px solid var(--accent);
    border-left: 2px solid var(--accent);
    opacity:0.4;
  }

  .panel-header {
    padding: 14px 20px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .panel-title {
    font-family: 'Orbitron', monospace;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--accent2);
  }

  .panel-icon { font-size: 1rem; }

  .panel-body { padding: 20px; }

  /* ── Token Input Panel */
  .token-label {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.72rem;
    color: var(--text-dim);
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 8px;
    display: block;
  }

  .token-input-wrap {
    position: relative;
    margin-bottom: 16px;
  }

  .token-input {
    width: 100%;
    background: rgba(255,255,255,0.03);
    border: 1px solid var(--border);
    color: var(--text);
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.82rem;
    padding: 12px 44px 12px 14px;
    border-radius: 3px;
    outline: none;
    transition: border-color 0.2s, box-shadow 0.2s;
    letter-spacing: 0.05em;
  }

  .token-input:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 2px rgba(255,80,0,0.15), inset 0 0 20px rgba(255,80,0,0.03);
  }

  .token-input::placeholder { color: #3a3530; }

  .token-clear-btn {
    position:absolute; right:10px; top:50%; transform:translateY(-50%);
    background:none; border:none; cursor:pointer;
    color: var(--text-dim); font-size:16px;
    line-height:1; padding:4px;
    transition: color 0.2s;
  }
  .token-clear-btn:hover { color: var(--red); }

  /* ── Buttons */
  .btn {
    width: 100%;
    padding: 13px;
    border: none; border-radius: 3px;
    font-family: 'Orbitron', monospace;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    cursor: pointer;
    position: relative;
    overflow: hidden;
    transition: all 0.2s;
    margin-bottom: 10px;
  }

  .btn:last-child { margin-bottom:0; }

  .btn::before {
    content:'';
    position:absolute; top:0; left:-100%;
    width:100%; height:100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent);
    transition: left 0.4s;
  }
  .btn:hover::before { left:100%; }

  .btn-start {
    background: linear-gradient(135deg, #ff3a00, #ff6600);
    color: #fff;
    box-shadow: 0 0 20px rgba(255,80,0,0.4);
  }
  .btn-start:hover { box-shadow: 0 0 30px rgba(255,80,0,0.7); transform:translateY(-1px); }
  .btn-start:active { transform:translateY(0); }
  .btn-start:disabled { background: #333; box-shadow:none; cursor:not-allowed; color:#666; }

  .btn-stop {
    background: transparent;
    border: 1px solid var(--red);
    color: var(--red);
  }
  .btn-stop:hover { background: rgba(255,51,102,0.1); box-shadow: 0 0 20px rgba(255,51,102,0.3); }
  .btn-stop:disabled { border-color:#333; color:#555; cursor:not-allowed; }

  /* ── Status badge */
  .status-row {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 16px;
    font-family:'Share Tech Mono', monospace;
    font-size:0.75rem;
    color: var(--text-dim);
  }

  .status-dot {
    width:8px; height:8px; border-radius:50%;
    background: #333;
    transition: all 0.3s;
    flex-shrink:0;
  }

  .status-dot.idle    { background:#555; }
  .status-dot.running { background:var(--green); box-shadow: 0 0 8px var(--green); animation: blink 1s ease-in-out infinite; }
  .status-dot.error   { background:var(--red); box-shadow: 0 0 8px var(--red); }
  .status-dot.stopped { background:var(--yellow); box-shadow: 0 0 6px var(--yellow); }

  @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.4} }

  #status-text { transition: color 0.3s; }

  /* ── Stats row */
  .stats-row {
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:10px;
    margin-bottom: 16px;
  }

  .stat-box {
    background: rgba(255,80,0,0.04);
    border: 1px solid var(--border);
    border-radius: 3px;
    padding: 10px 12px;
  }

  .stat-label {
    font-family:'Share Tech Mono', monospace;
    font-size:0.6rem;
    color: var(--text-dim);
    letter-spacing:0.15em;
    text-transform:uppercase;
    margin-bottom:4px;
  }

  .stat-value {
    font-family:'Orbitron', monospace;
    font-size:1.1rem;
    font-weight:700;
    color: var(--accent2);
  }

  .stat-value.green { color: var(--green); }
  .stat-value.red { color: var(--red); }

  /* ── Console Panel */
  .console-panel {
    grid-column: 1 / -1;
  }

  .console-controls {
    display:flex; gap:8px; margin-left:auto;
  }

  .icon-btn {
    background:none; border:1px solid var(--border);
    color:var(--text-dim); padding:4px 10px;
    border-radius:3px; cursor:pointer; font-size:0.72rem;
    font-family:'Share Tech Mono', monospace;
    letter-spacing:0.1em;
    transition: all 0.2s;
  }
  .icon-btn:hover { border-color:var(--accent); color:var(--accent); }

  .console-body {
    padding: 0;
    height: 340px;
    overflow-y: auto;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.8rem;
    line-height: 1.7;
    background: rgba(0,0,0,0.3);
  }

  .console-body::-webkit-scrollbar { width:4px; }
  .console-body::-webkit-scrollbar-track { background:transparent; }
  .console-body::-webkit-scrollbar-thumb { background:rgba(255,80,0,0.3); border-radius:2px; }

  .log-line {
    padding: 3px 18px;
    display:flex; gap:12px;
    animation: slide-in 0.15s ease-out;
    border-left: 2px solid transparent;
    transition: background 0.1s;
  }
  .log-line:hover { background:rgba(255,255,255,0.02); }

  @keyframes slide-in {
    from { opacity:0; transform:translateX(-6px); }
    to   { opacity:1; transform:translateX(0); }
  }

  .log-time { color: #3a3530; min-width:60px; flex-shrink:0; }

  .log-line.success { border-left-color: var(--green);  }
  .log-line.error   { border-left-color: var(--red);    }
  .log-line.warn    { border-left-color: var(--yellow); }
  .log-line.cyan    { border-left-color: var(--cyan);   }
  .log-line.info    { border-left-color: #333;           }

  .log-line.success .log-msg { color: var(--green); }
  .log-line.error   .log-msg { color: var(--red);   }
  .log-line.warn    .log-msg { color: var(--yellow);}
  .log-line.cyan    .log-msg { color: var(--cyan);  }
  .log-line.info    .log-msg { color: var(--text);  }

  .console-empty {
    height:100%;
    display:flex; flex-direction:column;
    align-items:center; justify-content:center;
    color: #2a2520;
    gap:12px;
  }

  .console-empty-icon { font-size:2.5rem; opacity:0.3; }

  .console-empty-text {
    font-family:'Share Tech Mono', monospace;
    font-size:0.72rem;
    letter-spacing:0.2em;
    text-transform:uppercase;
  }

  /* ── Saved token indicator */
  .saved-token-row {
    display:flex; align-items:center; justify-content:space-between;
    background: rgba(255,80,0,0.06);
    border: 1px solid rgba(255,80,0,0.15);
    border-radius:3px; padding:9px 12px;
    margin-bottom:16px;
    font-family:'Share Tech Mono', monospace;
    font-size:0.72rem;
    display:none;
  }

  .saved-token-row .label { color: var(--text-dim); }
  .saved-token-row .value { color:var(--accent2); overflow:hidden; text-overflow:ellipsis; max-width:120px; white-space:nowrap; }

  .del-saved-btn {
    background:none; border:none; cursor:pointer;
    color:var(--text-dim); font-size:12px;
    transition:color 0.2s; padding:2px 6px;
    font-family:'Share Tech Mono', monospace;
    letter-spacing:0.1em;
  }
  .del-saved-btn:hover { color:var(--red); }

  /* ── Server info */
  .server-info {
    background:rgba(0,229,255,0.04);
    border:1px solid rgba(0,229,255,0.12);
    border-radius:3px;
    padding:12px 14px;
    font-family:'Share Tech Mono', monospace;
    font-size:0.75rem;
    margin-bottom:16px;
    display:none;
  }

  .server-info .si-row { display:flex; justify-content:space-between; margin-bottom:4px; }
  .server-info .si-row:last-child { margin-bottom:0; }
  .server-info .si-key { color:var(--text-dim); }
  .server-info .si-val { color:var(--cyan); }

  /* ── Footer */
  footer {
    text-align:center;
    padding: 30px 0 10px;
    font-family:'Share Tech Mono', monospace;
    font-size:0.68rem;
    color: #2a2520;
    letter-spacing:0.2em;
    text-transform:uppercase;
  }
  footer span { color: var(--accent); }

  /* ── Particle */
  .particle-canvas {
    position:fixed; inset:0;
    pointer-events:none;
    z-index:0; opacity:0.4;
  }

  /* ── Toast */
  .toast {
    position:fixed; bottom:30px; right:30px;
    background: var(--panel);
    border: 1px solid var(--border-hot);
    border-radius:3px;
    padding:12px 20px;
    font-family:'Share Tech Mono', monospace;
    font-size:0.78rem;
    color:var(--text);
    z-index:1000;
    transform:translateY(80px); opacity:0;
    transition: all 0.3s cubic-bezier(.34,1.56,.64,1);
    box-shadow: var(--glow);
  }
  .toast.show { transform:translateY(0); opacity:1; }
</style>
</head>
<body>
<div class="scanlines"></div>
<canvas class="particle-canvas" id="particles"></canvas>

<div class="container">

  <!-- Header -->
  <header>
    <span class="skull-icon">☠️</span>
    <h1>Free Fire Login Tool</h1>
    <p class="subtitle">Version <span>OB52</span> · Following TikTok: <span>Senzu.!</span></p>
  </header>

  <div class="deco-line"></div>

  <!-- Grid -->
  <div class="grid">

    <!-- ── Left: Token + Controls -->
    <div class="panel">
      <div class="corner-tl"></div>
      <div class="panel-header">
        <span class="panel-icon">🔑</span>
        <span class="panel-title">Access Token</span>
      </div>
      <div class="panel-body">

        <div class="saved-token-row" id="saved-token-row">
          <span class="label">TOKEN ĐÃ LƯU:</span>
          <span class="value" id="saved-token-preview">—</span>
          <button class="del-saved-btn" id="del-token-btn" title="Xóa token">✕ XÓA</button>
        </div>

        <label class="token-label">Nhập Access Token Garena</label>
        <div class="token-input-wrap">
          <input
            class="token-input"
            id="token-input"
            type="text"
            placeholder="Dán access token tại đây..."
            autocomplete="off"
            spellcheck="false"
          />
          <button class="token-clear-btn" id="clear-input" title="Xóa">✕</button>
        </div>

        <div class="status-row">
          <div class="status-dot idle" id="status-dot"></div>
          <span id="status-text">Chờ lệnh...</span>
        </div>

        <button class="btn btn-start" id="start-btn">▶ BẮT ĐẦU LOGIN</button>
        <button class="btn btn-stop" id="stop-btn" disabled>■ DỪNG SESSION</button>
      </div>
    </div>

    <!-- ── Right: Stats -->
    <div class="panel">
      <div class="corner-tl"></div>
      <div class="panel-header">
        <span class="panel-icon">📊</span>
        <span class="panel-title">Session Stats</span>
      </div>
      <div class="panel-body">

        <div class="server-info" id="server-info">
          <div class="si-row"><span class="si-key">GAME SERVER</span><span class="si-val" id="si-server">—</span></div>
          <div class="si-row"><span class="si-key">WHISPER</span><span class="si-val" id="si-whisper">—</span></div>
        </div>

        <div class="stats-row">
          <div class="stat-box">
            <div class="stat-label">Packets Sent</div>
            <div class="stat-value green" id="stat-sent">0</div>
          </div>
          <div class="stat-box">
            <div class="stat-label">Errors</div>
            <div class="stat-value red" id="stat-err">0</div>
          </div>
          <div class="stat-box">
            <div class="stat-label">Session Time</div>
            <div class="stat-value" id="stat-time">00:00</div>
          </div>
          <div class="stat-box">
            <div class="stat-label">Responses</div>
            <div class="stat-value green" id="stat-recv">0</div>
          </div>
        </div>

        <div style="padding:12px 0 4px">
          <div class="stat-label" style="margin-bottom:8px">ACTIVITY</div>
          <div id="spark-bars" style="display:flex;gap:3px;align-items:flex-end;height:36px">
            <!-- dynamic bars -->
          </div>
        </div>
      </div>
    </div>

    <!-- ── Console (full width) -->
    <div class="panel console-panel">
      <div class="corner-tl"></div>
      <div class="panel-header">
        <span class="panel-icon">⚡</span>
        <span class="panel-title">Console Output</span>
        <div class="console-controls">
          <button class="icon-btn" id="auto-scroll-btn" title="Auto scroll">↓ AUTO</button>
          <button class="icon-btn" id="clear-console-btn">⊘ CLEAR</button>
        </div>
      </div>
      <div class="console-body" id="console">
        <div class="console-empty" id="console-empty">
          <div class="console-empty-icon">⚡</div>
          <div class="console-empty-text">Chờ khởi động session...</div>
        </div>
      </div>
    </div>

  </div><!-- /grid -->

  <footer>
    <p>Free Fire Spam Login Tool · <span>OB52</span> · Made for educational use only</p>
  </footer>
</div>

<div class="toast" id="toast"></div>

<script>
// ── Socket
const socket = io();

// ── State
let running = false;
let autoScroll = true;
let sentCount = 0;
let errCount  = 0;
let recvCount = 0;
let sessionStart = null;
let timerInterval = null;
let sparkData = Array(20).fill(0);

// ── Elements
const tokenInput    = document.getElementById('token-input');
const startBtn      = document.getElementById('start-btn');
const stopBtn       = document.getElementById('stop-btn');
const statusDot     = document.getElementById('status-dot');
const statusText    = document.getElementById('status-text');
const consoleEl     = document.getElementById('console');
const consoleEmpty  = document.getElementById('console-empty');
const clearInputBtn = document.getElementById('clear-input');
const clearConsBtn  = document.getElementById('clear-console-btn');
const autoScrollBtn = document.getElementById('auto-scroll-btn');
const savedRow      = document.getElementById('saved-token-row');
const savedPreview  = document.getElementById('saved-token-preview');
const delTokenBtn   = document.getElementById('del-token-btn');
const statSent      = document.getElementById('stat-sent');
const statErr       = document.getElementById('stat-err');
const statTime      = document.getElementById('stat-time');
const statRecv      = document.getElementById('stat-recv');
const sparkBars     = document.getElementById('spark-bars');
const serverInfo    = document.getElementById('server-info');
const siServer      = document.getElementById('si-server');
const siWhisper     = document.getElementById('si-whisper');
const toast         = document.getElementById('toast');

// ── Load saved token
fetch('/api/token').then(r=>r.json()).then(d => {
  if (d.token) {
    tokenInput.value = d.token;
    savedRow.style.display = 'flex';
    savedPreview.textContent = d.token.slice(0,12) + '…' + d.token.slice(-6);
  }
});

delTokenBtn.addEventListener('click', () => {
  fetch('/api/token', {method:'DELETE'}).then(() => {
    savedRow.style.display = 'none';
    tokenInput.value = '';
    showToast('Token đã xóa');
  });
});

clearInputBtn.addEventListener('click', () => {
  tokenInput.value = '';
  tokenInput.focus();
});

// ── Console logging
function addLog(level, msg, time) {
  if (consoleEmpty) consoleEmpty.style.display = 'none';
  const line = document.createElement('div');
  line.className = `log-line ${level}`;
  line.innerHTML = `<span class="log-time">${time}</span><span class="log-msg">${escapeHtml(msg)}</span>`;
  consoleEl.appendChild(line);
  if (autoScroll) consoleEl.scrollTop = consoleEl.scrollHeight;

  // Update stats
  if (level === 'success' && msg.includes('Sent OK')) {
    sentCount++;
    statSent.textContent = sentCount;
    if (msg.includes('Nhận')) {
      recvCount++;
      statRecv.textContent = recvCount;
    }
    addSpark(1);
  } else if (level === 'error' && msg.match(/^\\[\\d+\\]/)) {
    errCount++;
    statErr.textContent = errCount;
    addSpark(0);
  } else if (level === 'cyan') {
    sentCount++;
    statSent.textContent = sentCount;
    addSpark(1);
  }
}

function escapeHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// ── Sparkline
function addSpark(ok) {
  sparkData.push(ok ? 1 : -1);
  if (sparkData.length > 20) sparkData.shift();
  renderSpark();
}

function renderSpark() {
  sparkBars.innerHTML = '';
  sparkData.forEach(v => {
    const b = document.createElement('div');
    const h = v === 0 ? 4 : v > 0 ? 24+Math.random()*12 : 14;
    b.style.cssText = `flex:1; height:${h}px; background:${v>0?'var(--green)':v<0?'var(--red)':'#333'}; border-radius:1px; opacity:0.7; transition:height 0.2s`;
    sparkBars.appendChild(b);
  });
}
renderSpark();

// ── Timer
function startTimer() {
  sessionStart = Date.now();
  clearInterval(timerInterval);
  timerInterval = setInterval(() => {
    const elapsed = Math.floor((Date.now() - sessionStart) / 1000);
    const m = String(Math.floor(elapsed/60)).padStart(2,'0');
    const s = String(elapsed%60).padStart(2,'0');
    statTime.textContent = `${m}:${s}`;
  }, 1000);
}

function stopTimer() {
  clearInterval(timerInterval);
}

// ── Status
function setStatus(state, text) {
  statusDot.className = `status-dot ${state}`;
  statusText.textContent = text;
}

// ── Socket events
socket.on('log', ({level, message, time}) => {
  addLog(level, message, time);
});

socket.on('loop_started', ({ip, port}) => {
  serverInfo.style.display = 'block';
  siServer.textContent = `${ip}:${port}`;
});

socket.on('session_ended', () => {
  running = false;
  setStatus('stopped', 'Session đã dừng');
  startBtn.disabled = false;
  stopBtn.disabled = true;
  stopTimer();
});

// ── Buttons
startBtn.addEventListener('click', () => {
  const token = tokenInput.value.trim();
  if (!token) { showToast('Vui lòng nhập access token!'); return; }

  running = true;
  sentCount = errCount = recvCount = 0;
  statSent.textContent = statErr.textContent = statRecv.textContent = '0';
  statTime.textContent = '00:00';
  sparkData = Array(20).fill(0);
  renderSpark();
  serverInfo.style.display = 'none';
  siWhisper.textContent = '—';

  // Clear console
  consoleEl.innerHTML = '';
  if (!consoleEmpty.parentNode) consoleEl.appendChild(consoleEmpty);
  consoleEmpty.style.display = 'none';

  setStatus('running', 'Session đang chạy...');
  startBtn.disabled = true;
  stopBtn.disabled = false;
  startTimer();

  socket.emit('start_session', { token });
});

stopBtn.addEventListener('click', () => {
  if (!running) return;
  socket.emit('stop_session');
  setStatus('stopped', 'Đang dừng...');
  stopBtn.disabled = true;
});

// ── Auto scroll
autoScrollBtn.addEventListener('click', () => {
  autoScroll = !autoScroll;
  autoScrollBtn.textContent = autoScroll ? '↓ AUTO' : '↕ MANUAL';
  autoScrollBtn.style.color = autoScroll ? '' : 'var(--accent)';
});

// ── Clear console
clearConsBtn.addEventListener('click', () => {
  consoleEl.innerHTML = '';
  const empty = document.createElement('div');
  empty.className = 'console-empty'; empty.id = 'console-empty';
  empty.innerHTML = '<div class="console-empty-icon">⚡</div><div class="console-empty-text">Console đã được xóa</div>';
  consoleEl.appendChild(empty);
});

// ── Toast
function showToast(msg) {
  toast.textContent = msg;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 2500);
}

// ── Particles
(function() {
  const canvas = document.getElementById('particles');
  const ctx = canvas.getContext('2d');
  let W, H, particles = [];

  function resize() {
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }
  resize();
  window.addEventListener('resize', resize);

  function randBetween(a,b){ return a + Math.random()*(b-a); }

  for(let i=0;i<40;i++){
    particles.push({
      x: Math.random()*window.innerWidth,
      y: Math.random()*window.innerHeight,
      r: randBetween(0.3,1.5),
      vx: randBetween(-0.2,0.2),
      vy: randBetween(-0.4,-0.1),
      alpha: randBetween(0.1,0.5)
    });
  }

  function draw(){
    ctx.clearRect(0,0,W,H);
    particles.forEach(p=>{
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI*2);
      ctx.fillStyle = `rgba(255,100,0,${p.alpha})`;
      ctx.fill();
      p.x += p.vx; p.y += p.vy;
      if(p.y < -5){ p.y=H+5; p.x=Math.random()*W; }
      if(p.x<0||p.x>W) p.vx*=-1;
    });
    requestAnimationFrame(draw);
  }
  draw();
})();
</script>
</body>
</html>
"""


app = Flask(__name__)
app.config['SECRET_KEY'] = 'freefire-secret-key-2024'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

FREEFIRE_VERSION = "OB52"
AES_KEY = bytes([89,103,38,116,99,37,68,69,117,104,54,37,90,99,94,56])
AES_IV  = bytes([54,111,121,90,68,114,50,50,69,51,121,99,104,106,77,37])

TOKEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saved_token.txt")

active_sessions = {}

def aes_encrypt(data: bytes, key=AES_KEY, iv=AES_IV) -> bytes:
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return cipher.encrypt(pad(data, AES.block_size))

def aes_decrypt(data: bytes, key, iv) -> bytes:
    if isinstance(key, str): key = bytes.fromhex(key)
    if isinstance(iv, str):  iv  = bytes.fromhex(iv)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(data), AES.block_size)

def decode_jwt(token: str) -> dict:
    p = token.split('.')[1]
    p += '=' * (-len(p) % 4)
    return json.loads(base64.urlsafe_b64decode(p))

def _varint(v):
    r = bytearray()
    while v > 0x7F:
        r.append((v & 0x7F) | 0x80); v >>= 7
    r.append(v); return bytes(r)

def _str_field(field, value):
    if isinstance(value, str): value = value.encode()
    return _varint((field << 3) | 2) + _varint(len(value)) + value

def build_login_payload(open_id, access_token, platform):
    now = str(datetime.now())[:19]
    pl  = bytearray()
    pl += _str_field(3,  now)
    pl += _str_field(22, open_id)
    pl += _str_field(23, str(platform))
    pl += _str_field(29, access_token)
    pl += _str_field(99, str(platform))
    return bytes(pl)

def inspect_token(access_token):
    url = f"https://100067.connect.garena.com/oauth/token/inspect?token={access_token}"
    headers = {
        "Connection": "close",
        "Host": "100067.connect.garena.com",
        "User-Agent": "GarenaMSDK/4.0.19P4(G011A ;Android 9;en;US;)"
    }
    r = requests.get(url, headers=headers, timeout=10)
    d = r.json()
    if 'error' in d: raise Exception(f"Token lỗi: {d.get('error')}")
    return d.get('open_id'), int(d.get('platform', 8))

def major_login(open_id, access_token, platform):
    url = "https://loginbp.ggblueshark.com/MajorLogin"
    headers = {
        'X-Unity-Version': '2018.4.11f1',
        'ReleaseVersion':  FREEFIRE_VERSION,
        'Content-Type':    'application/x-www-form-urlencoded',
        'X-GA':            'v1 1',
        'User-Agent':      'Dalvik/2.1.0 (Linux; U; Android 7.1.2; ASUS_Z01QD Build/QKQ1.190825.002)',
        'Host':            'loginbp.ggblueshark.com',
        'Connection':      'Keep-Alive'
    }
    raw_payload = build_login_payload(open_id, access_token, platform)
    enc_payload = aes_encrypt(raw_payload)
    resp = requests.post(url, headers=headers, data=enc_payload, verify=False, timeout=10)
    if resp.status_code != 200:
        raise Exception(f"MajorLogin thất bại HTTP {resp.status_code}")
    try:
        import MajorLogin_res_pb2
        res = MajorLogin_res_pb2.MajorLoginRes()
        try:
            dec = aes_decrypt(resp.content, AES_KEY, AES_IV)
            res.ParseFromString(dec)
        except:
            res.ParseFromString(resp.content)
        return res.account_jwt, res.key, res.iv, 0
    except Exception as e:
        raise Exception(f"Parse MajorLogin lỗi: {e}")

def _parse_proto_raw(data):
    result = {}; idx = 0
    while idx < len(data):
        if idx >= len(data): break
        tag = data[idx]; idx += 1
        fn = tag >> 3; wt = tag & 0x07
        if wt == 0:
            val = 0; shift = 0
            while idx < len(data):
                b = data[idx]; idx += 1
                val |= (b & 0x7F) << shift
                if not (b & 0x80): break
                shift += 7
            result[fn] = val
        elif wt == 2:
            ln = 0; shift = 0
            while idx < len(data):
                b = data[idx]; idx += 1
                ln |= (b & 0x7F) << shift
                if not (b & 0x80): break
                shift += 7
            vb = data[idx:idx+ln]; idx += ln
            try: result[fn] = vb.decode('utf-8')
            except: result[fn] = vb
        else:
            break
    return result

def get_login_data(jwt_token, open_id, access_token, platform):
    raw_payload = build_login_payload(open_id, access_token, platform)
    enc_payload = aes_encrypt(raw_payload)
    url = "https://clientbp.ggblueshark.com/GetLoginData"
    headers = {
        'Authorization':   f'Bearer {jwt_token}',
        'X-Unity-Version': '2018.4.11f1',
        'X-GA':            'v1 1',
        'ReleaseVersion':  FREEFIRE_VERSION,
        'Content-Type':    'application/x-www-form-urlencoded',
        'User-Agent':      'Dalvik/2.1.0 (Linux; U; Android 9; G011A Build/PI)',
        'Host':            'clientbp.ggblueshark.com',
        'Connection':      'close'
    }
    resp = requests.post(url, headers=headers, data=enc_payload, verify=False, timeout=10)
    if resp.status_code != 200:
        raise Exception(f"GetLoginData thất bại HTTP {resp.status_code}")

    try:
        import GetLoginData_res_pb2
        res = GetLoginData_res_pb2.GetLoginDataRes()
        res.ParseFromString(resp.content)
        online_addr  = res.ip_port_online
        whisper_addr = res.ip_port_chat if res.ip_port_chat else None
    except:
        parsed = _parse_proto_raw(resp.content)
        def _str(v):
            if isinstance(v, bytes): return v.decode()
            if isinstance(v, dict):  return v.get('data', '')
            return str(v)
        online_addr  = _str(parsed.get(14, ''))
        whisper_addr = _str(parsed.get(32, '')) if 32 in parsed else None

    if not online_addr:
        raise Exception("Không tìm thấy địa chỉ game server")

    online_ip   = online_addr[:-6]
    online_port = int(online_addr[-5:])
    whisper_ip = whisper_port = None
    if whisper_addr:
        whisper_ip   = whisper_addr[:-6]
        whisper_port = int(whisper_addr[-5:])
    return whisper_ip, whisper_port, online_ip, online_port

def build_login_packet(jwt_token, key, iv, ts):
    jwt_payload = decode_jwt(jwt_token)
    try:
        acc_id = int(jwt_payload.get('account_id', 0))
    except:
        acc_id = 0
    if isinstance(key, str): key = bytes.fromhex(key) if len(key) == 32 else key.encode()
    if isinstance(iv, str):  iv  = bytes.fromhex(iv)  if len(iv)  == 32 else iv.encode()
    enc_token = aes_encrypt(jwt_token.encode(), key, iv)
    body_len  = len(enc_token)
    exp = int(jwt_payload.get('exp', 0))
    exp_adj = max(exp - 28800, 0)
    acc_hex      = acc_id.to_bytes(8, "big").hex()
    time_hex     = exp_adj.to_bytes(4, "big").hex()
    body_len_hex = body_len.to_bytes(4, "big").hex()
    header_hex = "0115" + acc_hex + time_hex + body_len_hex
    return bytes.fromhex(header_hex) + enc_token

def log(sid, level, message):
    socketio.emit('log', {
        'level': level,
        'message': message,
        'time': datetime.now().strftime('%H:%M:%S')
    }, room=sid)

def run_login_session(sid, access_token, stop_event):
    def L(level, msg): log(sid, level, msg)

    try:
        L('info', '🔍 Kiểm tra token...')
        open_id, platform = inspect_token(access_token)
        L('success', f'✅ Token OK | open_id={open_id} | platform={platform}')
    except Exception as e:
        L('error', f'❌ {e}'); socketio.emit('session_ended', {}, room=sid); return

    try:
        L('info', '🔐 MajorLogin...')
        jwt_token, key, iv, ts = major_login(open_id, access_token, platform)
        L('success', '✅ MajorLogin thành công')
    except Exception as e:
        L('error', f'❌ {e}'); socketio.emit('session_ended', {}, room=sid); return

    try:
        L('info', '🌐 GetLoginData...')
        whisper_ip, whisper_port, online_ip, online_port = get_login_data(
            jwt_token, open_id, access_token, platform)
        L('success', f'✅ Game Server: {online_ip}:{online_port}')
        if whisper_ip:
            L('success', f'✅ Whisper: {whisper_ip}:{whisper_port}')
    except Exception as e:
        L('error', f'❌ {e}'); socketio.emit('session_ended', {}, room=sid); return

    try:
        L('info', '📦 Build packet...')
        packet = build_login_packet(jwt_token, key, iv, ts)
        L('success', f'✅ Packet OK ({len(packet)} bytes)')
    except Exception as e:
        L('error', f'❌ {e}'); socketio.emit('session_ended', {}, room=sid); return

    if whisper_ip and whisper_port:
        try:
            ws = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            ws.settimeout(5); ws.connect((whisper_ip, int(whisper_port)))
            ws.send(packet); time.sleep(0.5); ws.close()
            L('success', f'✅ Whisper sent → {whisper_ip}:{whisper_port}')
        except Exception as e:
            L('warn', f'⚠️ Whisper lỗi: {e}')

    L('info', f'🚀 Bắt đầu Login Loop → {online_ip}:{online_port}')
    socketio.emit('loop_started', {'ip': online_ip, 'port': online_port}, room=sid)

    i = 0
    while not stop_event.is_set():
        i += 1
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(8)
            s.connect((online_ip, int(online_port)))
            s.sendall(packet)
            try:
                data = s.recv(4096)
                L('success', f'[{i}] ✅ Sent OK | Nhận {len(data)} bytes')
            except socket.timeout:
                L('cyan', f'[{i}] 📤 Sent OK | Không có response')
            s.close()
        except Exception as e:
            L('error', f'[{i}] ❌ Lỗi: {e}')
        time.sleep(1.0)

    L('warn', '⛔ Session đã dừng.')
    socketio.emit('session_ended', {}, room=sid)
    if sid in active_sessions:
        del active_sessions[sid]

def save_token(t): open(TOKEN_FILE, 'w').write(t.strip())
def load_token(): return open(TOKEN_FILE).read().strip() if os.path.exists(TOKEN_FILE) else None
def delete_token():
    if os.path.exists(TOKEN_FILE): os.remove(TOKEN_FILE)

@app.route('/')
def index():
    return Response(HTML_CONTENT, mimetype='text/html')



@app.route('/api/token', methods=['GET'])
def get_token():
    t = load_token()
    return jsonify({'token': t or ''})

@app.route('/api/token', methods=['DELETE'])
def del_token():
    delete_token()
    return jsonify({'ok': True})

@socketio.on('connect')
def on_connect():
    pass

@socketio.on('start_session')
def on_start(data):
    sid = request.sid
    token = data.get('token', '').strip()
    if not token:
        emit('log', {'level': 'error', 'message': '❌ Token không được để trống',
                     'time': datetime.now().strftime('%H:%M:%S')})
        return
    save_token(token)
    if sid in active_sessions:
        active_sessions[sid].set()
        time.sleep(0.5)
    stop_event = threading.Event()
    active_sessions[sid] = stop_event
    t = threading.Thread(target=run_login_session, args=(sid, token, stop_event), daemon=True)
    t.start()

@socketio.on('stop_session')
def on_stop():
    sid = request.sid
    if sid in active_sessions:
        active_sessions[sid].set()
        emit('log', {'level': 'warn', 'message': '⛔ Đang dừng session...',
                     'time': datetime.now().strftime('%H:%M:%S')})

@socketio.on('disconnect')
def on_disconnect():
    sid = request.sid
    if sid in active_sessions:
        active_sessions[sid].set()
        del active_sessions[sid]

if __name__ == '__main__':
    
    port = int(os.environ.get('PORT', 5000))

    socketio.run(app, host="0.0.0.0", port=port, debug=False, allow_unsafe_werkzeug=True)
