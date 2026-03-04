from flask import Flask, render_template, request, jsonify
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

app = Flask(__name__)
app.config['SECRET_KEY'] = 'freefire-secret-key-2024'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

FREEFIRE_VERSION = "OB52"
AES_KEY = bytes([89,103,38,116,99,37,68,69,117,104,54,37,90,99,94,56])
AES_IV  = bytes([54,111,121,90,68,114,50,50,69,51,121,99,104,106,77,37])

TOKEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saved_token.txt")

# Active sessions: sid -> stop_event
active_sessions = {}

# ── AES
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
    """Emit log to specific client"""
    socketio.emit('log', {'level': level, 'message': message, 'time': datetime.now().strftime('%H:%M:%S')}, room=sid)

def run_login_session(sid, access_token, stop_event):
    def emit_log(level, msg):
        log(sid, level, msg)

    try:
        emit_log('info', '🔍 Kiểm tra token...')
        open_id, platform = inspect_token(access_token)
        emit_log('success', f'✅ Token OK | open_id={open_id} | platform={platform}')
    except Exception as e:
        emit_log('error', f'❌ {e}')
        socketio.emit('session_ended', {}, room=sid)
        return

    try:
        emit_log('info', '🔐 MajorLogin...')
        jwt_token, key, iv, ts = major_login(open_id, access_token, platform)
        emit_log('success', '✅ MajorLogin thành công')
    except Exception as e:
        emit_log('error', f'❌ {e}')
        socketio.emit('session_ended', {}, room=sid)
        return

    try:
        emit_log('info', '🌐 GetLoginData...')
        whisper_ip, whisper_port, online_ip, online_port = get_login_data(jwt_token, open_id, access_token, platform)
        emit_log('success', f'✅ Game Server: {online_ip}:{online_port}')
        if whisper_ip:
            emit_log('success', f'✅ Whisper: {whisper_ip}:{whisper_port}')
    except Exception as e:
        emit_log('error', f'❌ {e}')
        socketio.emit('session_ended', {}, room=sid)
        return

    try:
        emit_log('info', '📦 Build packet...')
        packet = build_login_packet(jwt_token, key, iv, ts)
        emit_log('success', f'✅ Packet OK ({len(packet)} bytes)')
    except Exception as e:
        emit_log('error', f'❌ {e}')
        socketio.emit('session_ended', {}, room=sid)
        return

    # Whisper
    if whisper_ip and whisper_port:
        try:
            ws = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            ws.settimeout(5); ws.connect((whisper_ip, int(whisper_port)))
            ws.send(packet); time.sleep(0.5); ws.close()
            emit_log('success', f'✅ Whisper sent → {whisper_ip}:{whisper_port}')
        except Exception as e:
            emit_log('warn', f'⚠️ Whisper lỗi: {e}')

    emit_log('info', f'🚀 Bắt đầu Login Loop → {online_ip}:{online_port}')
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
                emit_log('success', f'[{i}] ✅ Sent OK | Nhận {len(data)} bytes')
            except socket.timeout:
                emit_log('cyan', f'[{i}] 📤 Sent OK | Không có response')
            s.close()
        except Exception as e:
            emit_log('error', f'[{i}] ❌ Lỗi: {e}')
        time.sleep(1.0)

    emit_log('warn', '⛔ Session đã dừng.')
    socketio.emit('session_ended', {}, room=sid)
    if sid in active_sessions:
        del active_sessions[sid]

# ── Token file ops
def save_token(t): open(TOKEN_FILE, 'w').write(t.strip())
def load_token(): return open(TOKEN_FILE).read().strip() if os.path.exists(TOKEN_FILE) else None
def delete_token():
    if os.path.exists(TOKEN_FILE): os.remove(TOKEN_FILE)

# ── Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/token', methods=['GET'])
def get_token():
    t = load_token()
    return jsonify({'token': t or ''})

@app.route('/api/token', methods=['DELETE'])
def del_token():
    delete_token()
    return jsonify({'ok': True})

# ── SocketIO events
@socketio.on('connect')
def on_connect():
    pass

@socketio.on('start_session')
def on_start(data):
    sid = request.sid
    token = data.get('token', '').strip()
    if not token:
        emit('log', {'level': 'error', 'message': '❌ Token không được để trống', 'time': datetime.now().strftime('%H:%M:%S')})
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
        emit('log', {'level': 'warn', 'message': '⛔ Đang dừng session...', 'time': datetime.now().strftime('%H:%M:%S')})

@socketio.on('disconnect')
def on_disconnect():
    sid = request.sid
    if sid in active_sessions:
        active_sessions[sid].set()
        del active_sessions[sid]

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
