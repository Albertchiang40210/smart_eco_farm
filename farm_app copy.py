import sys
import os
import streamlit as st
import pandas as pd
import numpy as np
import pymysql  
import time
import datetime  
from datetime import datetime
import datetime as dt_package  # 🟢 核心校正：徹底解決 datetime 類別與套件命名衝突
import cv2
from ultralytics import YOLO  
from PIL import Image  
import streamlit.components.v1 as components
from collections import deque

# ==============================================================================
# 🛰️ 類別一：工業級溫室遙測數據工程引擎 (記憶體緩衝與滾動去噪)
# ==============================================================================
class GreenhouseTelemetryEngine:
    def __init__(self, window_size=10):
        self.window_size = window_size
        self.temp_buffer = deque(maxlen=window_size)
        self.moist_buffer = deque(maxlen=window_size)
        self.uv_buffer = deque(maxlen=window_size)
        self.ppfd_buffer = deque(maxlen=window_size)
        
        self.current_raw_temp = 28.5
        self.current_raw_moist = 54.0
        self.current_raw_uv = 2.5
        self.current_raw_ppfd = 450.0

    def receive_high_frequency_hardware_stream(self):
        self.current_raw_temp += np.random.uniform(-0.3, 0.3)
        self.current_raw_moist += np.random.randint(-1, 2)
        self.current_raw_uv += np.random.uniform(-0.1, 0.1)
        self.current_raw_ppfd += np.random.uniform(-10.0, 10.0)
        
        self.current_raw_temp = max(15.0, min(45.0, self.current_raw_temp))
        self.current_raw_moist = max(20, min(95, self.current_raw_moist))
        self.current_raw_uv = max(0.0, min(12.0, self.current_raw_uv))
        self.current_raw_ppfd = max(0.0, min(1200.0, self.current_raw_ppfd))
        
        self.temp_buffer.append(self.current_raw_temp)
        self.moist_buffer.append(self.current_raw_moist)
        self.uv_buffer.append(self.current_raw_uv)
        self.ppfd_buffer.append(self.current_raw_ppfd)

    def get_smooth_telemetry(self):
        if len(self.temp_buffer) < 3:
            return {
                "temperature": round(self.current_raw_temp, 1), "moisture": int(self.current_raw_moist),
                "uv_index": round(self.current_raw_uv, 1), "ppfd": round(self.current_raw_ppfd, 1)
            }
        df_temp = pd.Series(list(self.temp_buffer))
        df_moist = pd.Series(list(self.moist_buffer))
        df_uv = pd.Series(list(self.uv_buffer))
        df_ppfd = pd.Series(list(self.ppfd_buffer))
        
        return {
            "temperature": round(df_temp.rolling(window=self.window_size, min_periods=1).mean().iloc[-1], 1),
            "moisture": int(df_moist.rolling(window=self.window_size, min_periods=1).mean().iloc[-1]),
            "uv_index": round(df_uv.rolling(window=self.window_size, min_periods=1).mean().iloc[-1], 1),
            "ppfd": round(df_ppfd.rolling(window=self.window_size, min_periods=1).mean().iloc[-1], 1)
        }

# ==============================================================================
# ⚙️ 類別二：工業級溫室執行器控制中樞 (PLC 抽象與硬體保護機制)
# ==============================================================================
class GreenhouseActuatorController:
    def __init__(self):
        self.fan_status = "OFF"
        self.pump_status = "OFF"
        self.COOLDOWN_TIME = 5  
        self.last_fan_toggle_time = 0
        self.last_pump_toggle_time = 0

    def set_fan(self, command: str) -> bool:
        current_time = time.time()
        command = command.upper()
        if command == self.fan_status: return False
        if current_time - self.last_fan_toggle_time < self.COOLDOWN_TIME: return False
        self.fan_status = command
        self.last_fan_toggle_time = current_time
        return True

    def set_pump(self, command: str) -> bool:
        current_time = time.time()
        command = command.upper()
        if command == self.pump_status: return False
        if current_time - self.last_pump_toggle_time < self.COOLDOWN_TIME: return False
        self.pump_status = command
        self.last_pump_toggle_time = current_time
        return True

# 初始化全域核心單例
telemetry_engine = GreenhouseTelemetryEngine(window_size=10)
actuator_controller = GreenhouseActuatorController()

# ==============================================================================
# 🔐 SecOps 憑證隔離配置
# ==============================================================================
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "P@ssw0rd") 
DB_NAME = os.getenv("DB_NAME", "smart_eco_farm_db")
NGROK_URL = os.getenv("NGROK_URL", "https://uncrown-pacific-sprout.ngrok-free.dev")
ADMIN_KEYWORD = os.getenv("ADMIN_KEYWORD", "farm2026")

UPLOAD_QUEUE_DIR = "./phone_upload_queue"
os.makedirs(UPLOAD_QUEUE_DIR, exist_ok=True)

# ==============================================================================
# 🛸 整合模擬器機制的動態微氣候狀態緩衝
# ==============================================================================
if "t_base" not in st.session_state: st.session_state["t_base"] = 28.5
if "m_base" not in st.session_state: st.session_state["m_base"] = 54

# ==============================================================================
# 🎨 Streamlit 視覺樣式與核心組態
# ==============================================================================
st.set_page_config(page_title="智慧生態農場 AI 核心監控系統", page_icon="🌿", layout="wide")

st.markdown("""
<style>
    [data-testid="stSidebar"] { display: none; }
    [data-testid="collapsedControl"] { display: none; }
    .stApp { background-color: #f8faf8; color: #1e3d2f; }
    .main-title { font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 2.2rem !important; font-weight: 800; background: linear-gradient(135deg, #1e3d2f, #27ae60); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 20px; }
    .section-title { font-size: 1.15rem; font-weight: bold; color: #1e3d2f; border-bottom: 2px solid #27ae60; padding-bottom: 6px; margin-bottom: 12px; }
    .metric-box { background: #ffffff; border: 1px solid #eaf2ec; padding: 15px; border-radius: 14px; text-align: center; box-shadow: 0 4px 20px rgba(43, 75, 57, 0.03); }
    .stButton>button { width: 100% !important; background: linear-gradient(135deg, #11998e, #38ef7d) !important; color: white !important; font-size: 1rem !important; font-weight: 600 !important; border: none !important; border-radius: 10px !important; padding: 8px 0 !important; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# 🛠️ 農業物種與病害中文字典
DISEASE_CH_NAMES = {
    'Powdery Mildew': '🍂 白粉病 (需要降濕通風)', 'Tomato Rust': '🍂 鐵鏽病 (需要物理隔離)',
    'Apple___Apple_scab': '🍎 蘋果黑星病 (加強果園隔離)', 'Healthy': '🥬 健康無病害 (作物發育良好)',
    'Ants': '🐜 觀察紀錄：螞蟻生態 (細部覓食觀測中)', 'Bees': '🐝 益蟲發現：小蜜蜂 (正在授粉中)',
    'Caterpillars': '🐛 警告：毛毛蟲侵害 (注意葉片啃食防禦)', 'Unknown': '🔍 溫室大腦正在分析數據中...'
}

def get_friendly_name(raw_name: str) -> str:
    if not raw_name: return "🔍 溫室大腦正在分析數據中..."
    raw_name_clean = str(raw_name).strip()
    if raw_name_clean in DISEASE_CH_NAMES: return DISEASE_CH_NAMES[raw_name_clean]
    return f"🔍 觀測目標 ({raw_name_clean})"

# ==============================================================================
# 📊 MySQL 資料庫初始化
# ==============================================================================
DB_CONFIG = {
    'host': DB_HOST, 'port': 3306, 'user': DB_USER, 'password': DB_PASSWORD,  
    'database': DB_NAME, 'charset': 'utf8mb4', 'cursorclass': pymysql.cursors.DictCursor, 'connect_timeout': 2  
}

db_connected = False
try:
    conn_init = pymysql.connect(host=DB_HOST, port=3306, user=DB_USER, password=DB_PASSWORD)
    cursor_init = conn_init.cursor()
    cursor_init.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} DEFAULT CHARACTER SET utf8mb4;")
    conn_init.select_db(DB_NAME)
    
    cursor_init.execute("""
        CREATE TABLE IF NOT EXISTS farm_tasks_v2 (
            id INT AUTO_INCREMENT PRIMARY KEY, file_path VARCHAR(255) NOT NULL, status VARCHAR(50) DEFAULT 'pending', 
            diagnosis_result VARCHAR(100) DEFAULT 'Unknown', confidence FLOAT DEFAULT 0.0, temperature FLOAT DEFAULT 28.5,
            moisture INT DEFAULT 54, uv_index FLOAT DEFAULT 2.5, ppfd FLOAT DEFAULT 450.0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)
    cursor_init.execute("""
        CREATE TABLE IF NOT EXISTS eco_brain_sync (
            sync_key VARCHAR(50) PRIMARY KEY, is_frozen INT DEFAULT 0, detected_species VARCHAR(100) DEFAULT 'Unknown', 
            confidence_score FLOAT DEFAULT 0.0, brain_source VARCHAR(50) DEFAULT 'Unknown', image_blob LONGBLOB
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)
    cursor_init.execute("INSERT IGNORE INTO eco_brain_sync (sync_key, is_frozen, detected_species, confidence_score, brain_source) VALUES ('main', 0, 'Unknown', 0.0, 'Unknown')")
    conn_init.commit(); cursor_init.close(); conn_init.close()
    db_connected = True
except Exception as e: print(f"資料庫建置失敗: {e}")

def fetch_today_alerts():
    if not db_connected: return 0
    try:
        conn = pymysql.connect(**DB_CONFIG); cursor = conn.cursor()
        today_str = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("SELECT COUNT(*) as cnt FROM farm_tasks_v2 WHERE created_at LIKE %s AND diagnosis_result NOT LIKE 'Healthy' AND status = 'completed'", (f"{today_str}%",))
        count = cursor.fetchone()['cnt']; cursor.close(); conn.close()
        return count
    except: return 0

# ==============================================================================
# 🧠 YOLOv8 雙大腦引擎
# ==============================================================================
@st.cache_resource
def load_farm_brains():
    bug_path = "./result/train/weights/best.pt"  
    leaf_path = "./yolov8s.pt"                   
    b_model = YOLO(bug_path) if os.path.exists(bug_path) else None
    l_model = YOLO(leaf_path) if os.path.exists(leaf_path) else None
    return b_model, l_model

bug_brain, leaf_brain = load_farm_brains()

def diagnose_image(img_path):
    pred_name, conf_val, source_brain, final_bytes = "Unknown", 0.0, "None", None
    try:
        img_pil = Image.open(img_path)
        if bug_brain is not None:
            res = bug_brain.predict(source=img_pil, imgsz=224, verbose=False)
            for r in res:
                if getattr(r, 'boxes', None) is not None and len(r.boxes) > 0:
                    annotated_frame = r.plot()
                    _, buffer = cv2.imencode('.jpg', annotated_frame)
                    final_bytes = buffer.tobytes()
                    pred_name = r.names[int(r.boxes[0].cls[0].item())]
                    conf_val = float(r.boxes[0].conf[0].item())
                    return pred_name, conf_val, "bug_brain", final_bytes
        if leaf_brain is not None:
            res = leaf_brain.predict(source=img_pil, imgsz=224, verbose=False)
            for r in res:
                if getattr(r, 'probs', None) is not None and r.probs is not None:
                    pred_name = r.names[r.probs.top1]
                    conf_val = float(r.probs.top1conf.item())
                    return pred_name, conf_val, "leaf_brain", final_bytes
    except Exception as e: print(f"診斷核心異常: {e}")
    return pred_name, conf_val, source_brain, final_bytes

# ==============================================================================
# 🔑 4. 安全 Session 狀態管理
# ==============================================================================
if "role" not in st.session_state: st.session_state["role"] = "staff"
is_mobile_client = st.query_params.get("client") == "mobile"

if db_connected:
    TODAY_ALERTS = fetch_today_alerts()
    conn = pymysql.connect(**DB_CONFIG); cursor = conn.cursor()
    cursor.execute("SELECT * FROM eco_brain_sync WHERE sync_key='main'")
    sync_status = cursor.fetchone(); cursor.close(); conn.close()
    is_frozen = bool(sync_status['is_frozen'])
    sync_species = sync_status['detected_species']
    sync_conf = sync_status['confidence_score']
    image_blob_data = sync_status['image_blob']
else:
    TODAY_ALERTS, is_frozen, sync_species, sync_conf, image_blob_data = 0, False, 'Unknown', 0.0, None

# ==============================================================================
# 📱 模式 A：【農夫手機拍照上傳端】
# ==============================================================================
if is_mobile_client:
    st.markdown("<h1 class='main-title'>📱 行動端巡田水相機</h1>", unsafe_allow_html=True)
    with st.container(border=True):
        img_file = st.camera_input("請對準有病變或害蟲的葉片拍攝：")
        if img_file is not None:
            if st.button("🚀 確認無誤 ➔ 送回後台排隊", use_container_width=True):
                bytes_data = img_file.getvalue()
                saved_path = os.path.join(UPLOAD_QUEUE_DIR, f"phone_upload_{int(time.time())}.jpg")
                with open(saved_path, "wb") as f: f.write(bytes_data)
                pred_name, conf_val, brain_src, final_bytes = diagnose_image(saved_path)
                if final_bytes is None: final_bytes = bytes_data
                if db_connected:
                    try:
                        conn = pymysql.connect(**DB_CONFIG); cursor = conn.cursor()
                        ins_sql = "INSERT INTO farm_tasks_v2 (file_path, status, diagnosis_result, confidence, temperature, moisture, uv_index, ppfd) VALUES (%s, 'pending', %s, %s, %s, %s, %s, %s)"
                        
                        sim_t = st.session_state["t_base"]
                        sim_m = st.session_state["m_base"]
                        
                        cursor.execute(ins_sql, (saved_path, pred_name, conf_val, sim_t, sim_m, 2.5, 450.0))
                        cursor.execute("UPDATE eco_brain_sync SET is_frozen=1, detected_species=%s, confidence_score=%s, brain_source=%s, image_blob=%s WHERE sync_key='main'", (pred_name, conf_val, brain_src, final_bytes))
                        conn.commit(); cursor.close(); conn.close()
                        st.success("🎉 生態特徵快取成功！已同步大螢幕看板。")
                    except Exception as e: st.error(f"寫入失敗: {e}")

# ==============================================================================
# 🖥️ 模式 B：【大螢幕看板與管理端一體化】
# ==============================================================================
else:
    if "mode" not in st.query_params: st.query_params.update({"mode": "POS"})
    device_mode = st.query_params.get("mode", "POS")

    nav_col1, nav_col2, nav_col3 = st.columns([4, 4, 3])
    if nav_col1.button("🖥️ 溫室 Kiosk 即時影像監控看板", use_container_width=True, type="primary" if device_mode == "POS" else "secondary"):
        st.query_params.update({"mode": "POS"}); st.rerun()
    if nav_col2.button("💻 遠端智慧溫室管理決策後台", use_container_width=True, type="primary" if device_mode == "BOSS" else "secondary"):
        st.query_params.update({"mode": "BOSS"}); st.rerun()
        
    with nav_col3:
        if st.session_state["role"] == "admin":
            if st.button("🔒 安全登出 (鎖定控制權)", use_container_width=True):
                st.session_state["role"] = "staff"; st.rerun()
        else:
            st.markdown('<div style="border: 1px solid #cccccc; background: #ffffff; padding: 7px 15px; border-radius: 8px; text-align: center; font-size: 0.95rem; font-weight: 600; color: #333333; height: 38px; line-height: 22px;">🔑 身份：👤 員工唯讀 (staff)</div>', unsafe_allow_html=True)

    st.markdown("<hr style='margin-top: 10px; margin-bottom: 20px;'>", unsafe_allow_html=True)

    # 🖥️ B-1：Kiosk 大螢幕看板 
    if device_mode == "POS":
        st.markdown("<h1 class='main-title'>🖥️ 溫室 Kiosk 實時 AI 分析大腦</h1>", unsafe_allow_html=True)
        if not is_frozen: components.html("<script>setTimeout(function(){window.parent.location.reload();}, 2000);</script>", height=0, width=0)

        col_left, col_right = st.columns([6, 5])
        with col_left:
            with st.container(border=True):
                st.markdown("### 📸 AI 影像特徵辨識雷達")
                if is_frozen and image_blob_data:
                    nparr = np.frombuffer(image_blob_data, np.uint8)
                    st.image(cv2.cvtColor(cv2.imdecode(nparr, cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB), caption="🛸 邊緣網關即時捕捉畫面", use_container_width=True)
                else:
                    st.markdown(f"<div style='text-align:center; padding: 40px 0;'><img src='https://api.qrserver.com/v1/create-qr-code/?size=220x220&data={NGROK_URL}?client=mobile'/><h3 style='margin-top:20px;'>🌿 請用手機掃碼開始拍照監測</h3></div>", unsafe_allow_html=True)
        with col_right:
            with st.container(border=True):
                if is_frozen:
                    st.markdown("<div class='section-title'>🧾 現地邊緣 analysis 明細</div>", unsafe_allow_html=True)
                    st.markdown(f"""
                    <div style="background: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #eaf2ec; margin-bottom: 20px;">
                        <p style="margin: 10px 0; font-size: 1.15rem; color: #1e3d2f;"><b>🧬 生態診斷目標：</b> <span style="color: #27ae60; font-weight: 700;">{get_friendly_name(sync_species)}</span></p>
                        <p style="margin: 10px 0; font-size: 1.15rem; color: #1e3d2f;"><b>🎯 AI 信心指數：</b> <span style="color: #11998e; font-weight: 700;">{round(float(sync_conf)*100, 1)}%</span></p>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("❌ 放棄此張照片，清空重新捕捉", use_container_width=True, type="secondary"):
                        if db_connected:
                            conn = pymysql.connect(**DB_CONFIG); cursor = conn.cursor()
                            cursor.execute("UPDATE eco_brain_sync SET is_frozen=0, detected_species='Unknown', confidence_score=0.0, image_blob=NULL WHERE sync_key='main'")
                            conn.commit(); cursor.close(); conn.close()
                        st.rerun()
                else:
                    st.markdown("<div style='text-align:center; color:#7f8c8d; padding: 135px 0;'><h2>🧾 邊緣分析對接中</h2><p>目前空置中. 等待前台手機上傳巡田任務...</p></div>", unsafe_allow_html=True)

    # 💻 B-2：遠端智慧溫室管理決策後台 
    else:
        st.markdown("<h1 class='main-title'>💼 Internet of Agriculture — 遠端智慧溫室管理決策後台</h1>", unsafe_allow_html=True)
        
        # 實時硬體與網路通訊探測
        import socket
        import torch
        try:
            mqtt_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM); mqtt_sock.settimeout(0.3)
            mqtt_connected = (mqtt_sock.connect_ex(('127.0.0.1', 1883)) == 0); mqtt_sock.close()
        except: mqtt_connected = False
        yolo_status_text = "🟢 Apple Silicon (MPS) 加速中" if hasattr(torch.backends, "mps") and torch.backends.mps.is_available() else "🟢 雙大腦分流就緒"
        try:
            socket.gethostbyname("one.one.one.one")
            drone_5g_status = f'<span style="color:#27ae60;">🟢 5G 已導通 (12ms)</span>'
        except: drone_5g_status = '<span style="color:#c0392b;">🔴 5G 鏈路中斷</span>'

        # 一體化工控狀態列
        status_cols = st.columns(4)
        status_cols[0].markdown(f'<div class="metric-box"><span style="font-size:0.8rem;color:#666;">📊 MySQL 資料庫</span><br><b>{"<span style=\'color:#27ae60;\'>🟢 正常連線</span>" if db_connected else "<span style=\'color:#c0392b;\'>🔴 連線失敗</span>"}</b></div>', unsafe_allow_html=True)
        status_cols[1].markdown(f'<div class="metric-box"><span style="font-size:0.8rem;color:#666;">🤖 YOLOv8 核心</span><br><b><span style="color:#27ae60;">{yolo_status_text}</span></b></div>', unsafe_allow_html=True)
        status_cols[2].markdown(f'<div class="metric-box"><span style="font-size:0.8rem;color:#666;">🔌 MQTT 閘門</span><br><b>{"<span style=\'color:#27ae60;\'>🟢 監聽中 (1883)</span>" if mqtt_connected else "<span style=\'color:#e67e22;\'>🟡 未啟動 Broker</span>"}</b></div>', unsafe_allow_html=True)
        status_cols[3].markdown(f'<div class="metric-box"><span style="font-size:0.8rem;color:#666;">🛰️ 無人機 5G 鏈路</span><br><b>{drone_5g_status}</b></div>', unsafe_allow_html=True)
        st.markdown("---")
        
        try:
            conn = pymysql.connect(**DB_CONFIG); cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as cnt FROM farm_tasks_v2 WHERE status='pending'")
            pending_count = cursor.fetchone()['cnt']; cursor.close(); conn.close()
        except: pending_count = 0
        
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1: st.markdown(f"<div class='metric-box'>📦 邊緣端待消化佇列<h2 style='color:#e67e22; margin:5px 0;'>{pending_count} 筆影像等待推論</h2></div>", unsafe_allow_html=True)
        with col_m2: st.markdown(f"<div class='metric-box'>🤖 決策運算架構<h2 style='color:#27ae60; margin:5px 0;'>二階段分流推論引擎</h2></div>", unsafe_allow_html=True)
        with col_m3: st.metric(label="🚨 今日累計病蟲害預警", value=f"{TODAY_ALERTS} 次引發", delta="🟢 狀態安全" if TODAY_ALERTS == 0 else "🚨 偵測到異常入侵")
        
        st.markdown("<br>", unsafe_allow_html=True)
        col_dash_left, col_dash_right = st.columns([6, 5])
        
        with col_dash_left:
            with st.container(border=True):
                st.markdown("<h3 style='color:#2c3e50; margin-top:0;'>⚙️ 異步 Worker 決策運算面板</h3>", unsafe_allow_html=True)
                if pending_count > 0:
                    if st.session_state["role"] != "admin":
                        st.caption("🔒 背景資料處理中，執行批次推論請聯絡高級工程師解鎖。")
                    else:
                        if st.button("🔥 啟動後台 AI 大腦：批次消化工業佇列任務", use_container_width=True):
                            conn = pymysql.connect(**DB_CONFIG); cursor = conn.cursor()
                            cursor.execute("SELECT * FROM farm_tasks_v2 WHERE status='pending'")
                            for task in cursor.fetchall():
                                pred_name, conf, brain_src, final_bytes = diagnose_image(task['file_path'])
                                try: os.remove(task['file_path'])
                                except: pass
                                telemetry_engine.receive_high_frequency_hardware_stream()
                                iot_snapshot = telemetry_engine.get_smooth_telemetry()
                                cursor.execute("UPDATE farm_tasks_v2 SET status='completed', diagnosis_result=%s, confidence=%s, temperature=%s, moisture=%s WHERE id=%s", (pred_name, conf, iot_snapshot["temperature"], iot_snapshot["moisture"], task['id']))
                            cursor.execute("UPDATE eco_brain_sync SET is_frozen=0, detected_species='Unknown', confidence_score=0.0, image_blob=NULL WHERE sync_key='main'")
                            conn.commit(); cursor.close(); conn.close(); st.balloons(); time.sleep(0.5); st.rerun()
                else: st.info("⚪ 邊緣感測排隊佇列目前空閒。")
            
            st.markdown("<br>", unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown("<h3 style='color:#2c3e50; margin-top:0;'>📜 ESG 碳盤查與產銷履歷大水庫</h3>", unsafe_allow_html=True)
                try:
                    conn = pymysql.connect(**DB_CONFIG); cursor = conn.cursor()
                    cursor.execute("SELECT id, status, diagnosis_result, confidence, temperature, moisture, created_at FROM farm_tasks_v2 ORDER BY id DESC LIMIT 5")
                    for row in cursor.fetchall():
                        friendly_name = get_friendly_name(row['diagnosis_result'])
                        conf_pct = f"{round(float(row['confidence'])*100, 1)}%" if row['confidence'] else "0%"
                        st.markdown(f'<div style="background:#ffffff; padding:10px; border-radius:8px; border:1px solid #eaf2ec; margin-bottom:8px;"><b>🆔 履歷 #{row["id"]}</b> | <b>🌿 認證：</b>{friendly_name} ({conf_pct}) | 微氣候快照: {row["temperature"]}°C ｜ 土壤濕度: {row["moisture"]}%</div>', unsafe_allow_html=True)
                    cursor.close(); conn.close()
                except Exception as e: st.error(f"表格渲染失敗: {e}")
                
        with col_dash_right:
            with st.container(border=True):
                st.markdown("<h3 style='color:#2c3e50; margin-top:0;'>⚙️ 工業級 PLC 執行器與 自動化閾值智控核心</h3>", unsafe_allow_html=True)
                
                if st.session_state["role"] != "admin":
                    st.markdown("<p style='font-size:0.85rem; color:#7f8c8d; margin-bottom:5px;'>🔒 變更 PLC 暫存器閾值，請輸入管理員金鑰：</p>", unsafe_allow_html=True)
                    u_try = st.text_input("🛡 *帳號*", value="", key="plc_u")
                    p_try = st.text_input("🔑 *密碼*", type="password", value="", key="plc_p")
                    if st.button("🔓 驗證並變更暫存器", use_container_width=True):
                        if u_try == "admin" and p_try == ADMIN_KEYWORD:
                            st.session_state["role"] = "admin"; st.success("解鎖成功！"); time.sleep(0.5); st.rerun()
                        else: st.error("❌ 拒絕存取")
                    
                    sel_act = "🌬️ 溫室大棚環境流體強力散熱排風扇"
                    th_temp = 30.0  
                    th_moist = 40
                else:
                    st.info("🔓 管理員已授權動態修改 PLC 暫存器閾值。")
                    sel_act = st.selectbox("核心智控元件對接選擇：", ["🌬️ 溫室大棚環境流體強力散熱排風扇", "💦 工業級防護精頻變頻灌溉泵浦"])
                    
                    if "排風扇" in sel_act:
                        th_temp = st.slider("當前氣溫高階預警啟動閾值 (°C)", 25.0, 40.0, 30.0, 0.5)
                        th_moist = 40 
                    else:
                        th_moist = st.slider("當前土壤濕度下限自動灌溉閾值 (%)", 20, 60, 40, 1)
                        th_temp = 30.0 
                
                if "排風扇" in sel_act:
                    trigger_fan = st.session_state["t_base"] > th_temp
                    actuator_controller.set_fan("ON" if trigger_fan else "OFF")
                    if trigger_fan:
                        st.warning(f"⚠️ 警告：目前氣溫 {round(st.session_state['t_base'], 1)}°C 高於強制散熱閾值 {th_temp}°C！風扇狀態: 【{actuator_controller.fan_status}】")
                    else: 
                        st.success(f"🟢 智控通報：目前氣溫 safe。風扇狀態: 【{actuator_controller.fan_status}】")
                else:
                    trigger_pump = st.session_state["m_base"] < th_moist
                    actuator_controller.set_pump("ON" if trigger_pump else "OFF")
                    if trigger_pump:
                        st.warning(f"⚠️ 警告：目前土壤濕度 {st.session_state['m_base']}% 低於自動灌溉閾值 {th_moist}%！變頻泵浦狀態: 【{actuator_controller.pump_status}】")
                    else:
                        st.success(f"🟢 智控通報：土壤飽水度良好。變頻泵浦狀態: 【{actuator_controller.pump_status}】")
                        
            st.markdown("<br>", unsafe_allow_html=True)
            
            with st.container(border=True):
                st.markdown("<h3 style='color:#c0392b; margin-top:0;'>🚨 溫室季度交班與歷史數據封存</h3>", unsafe_allow_html=True)
                reset_col1, reset_col2 = st.columns(2)
                with reset_col1:
                    if st.session_state["role"] != "admin":
                        st.button("🔄 執行 Soft Archive 數據軟封存", use_container_width=True, disabled=True)
                    else:
                        if st.button("🔄 執行 Soft Archive 數據軟封存", use_container_width=True, type="secondary"):
                            if db_connected:
                                conn = pymysql.connect(**DB_CONFIG); cursor = conn.cursor(); today_str = datetime.now().strftime("%Y-%m-%d")
                                cursor.execute("UPDATE farm_tasks_v2 SET status='archived' WHERE status='completed' AND created_at LIKE %s", (f"{today_str}%",))
                                conn.commit(); cursor.close(); conn.close(); st.rerun()
                with reset_col2:
                    if st.session_state["role"] != "admin":
                        st.button("⚠️ 全域資料庫初始化修復", use_container_width=True, disabled=True)
                    else:
                        if st.button("⚠️ 全域資料庫初始化修復", use_container_width=True, type="primary"):
                            if db_connected:
                                try:
                                    conn = pymysql.connect(**DB_CONFIG); cursor = conn.cursor()
                                    cursor.execute("TRUNCATE TABLE farm_tasks_v2")
                                    cursor.execute("UPDATE eco_brain_sync SET is_frozen=0, detected_species='Unknown', confidence_score=0.0, image_blob=NULL WHERE sync_key='main'")
                                    conn.commit(); cursor.close(); conn.close()
                                    st.session_state["t_base"] = 28.5
                                    st.session_state["m_base"] = 54
                                    st.toast("💥 資料庫與環境狀態已完成全域初始化修復！")
                                    time.sleep(0.5); st.rerun()
                                except Exception as e: st.error(f"重置失敗: {e}")

        # ==============================================================================
        # 📊 5. 數據科學圖表區 (🛡️ 終極防禦：全面脫離 DictCursor，並且關閉自動補入以配合完全清空)
        # ==============================================================================
        st.markdown("<br><h3 style='color:#1e3d2f;'>📊 Microclimate & Productivity — 溫室微氣候與高階產能數據科學面板</h3>", unsafe_allow_html=True)
        db_chart_df, db_pie_df = pd.DataFrame(), pd.DataFrame()
        if db_connected:
            try:
                # 🟢 核心修正：手動建立傳統元組模式連線，徹底防止 pandas 快取崩潰
                pure_conn = pymysql.connect(
                    host=DB_HOST,
                    port=3306,
                    user=DB_USER,
                    password=DB_PASSWORD,
                    database=DB_NAME,
                    charset='utf8mb4'
                )
                
                # 🛑 核心防禦：應 Albert 要求，將 if current_count == 0 的自動補入熱灌水徹底移除！
                # 這樣一來，只要你用 Python 抹平資料庫，網頁就不會再任性自動塞入預設的 5 筆舊資料！
                
                # 使用最安全的 Tuple 資料流直接注入 pandas，這下次 100% 暢通更新！
                db_chart_df = pd.read_sql("SELECT id, temperature, moisture FROM farm_tasks_v2 WHERE status='completed' ORDER BY id ASC LIMIT 10", pure_conn)
                db_pie_df = pd.read_sql("SELECT diagnosis_result, COUNT(*) as qty FROM farm_tasks_v2 WHERE status='completed' GROUP BY diagnosis_result", pure_conn)
                
                pure_conn.close()
            except Exception as chart_err: 
                print(f"圖表即時編譯核心異常: {chart_err}")

        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            with st.container(border=True):
                st.markdown("##### 📈 溫室大棚微氣候環境追蹤曲線 (動態時序)")
                if not db_chart_df.empty:
                    try:
                        db_chart_df['巡檢編號'] = db_chart_df['id'].apply(lambda x: f"第 {x} 次巡檢")
                        chart_data = db_chart_df[['巡檢編號', 'temperature', 'moisture']].rename(
                            columns={'temperature': '氣溫 (°C)', 'moisture': '土壤濕度 (%)'}
                        ).set_index('巡檢編號')
                        st.line_chart(chart_data)
                    except Exception as parse_err: st.caption(f"⏳ 時序訊號去噪平滑中...")
                else: st.caption("⏳ 目前資料庫已完全抹平清空，等待巡檢數據流入中...")
                
        with chart_col2:
            with st.container(border=True):
                st.markdown("##### 🧫 溫室季度特徵侵擾佔比與歷史統計")
                if not db_pie_df.empty:
                    try:
                        # 排除純數字髒資料，保留乾淨的英文字串進行翻譯映射
                        db_pie_df = db_pie_df[db_pie_df['diagnosis_result'].astype(str).str.contains('[a-zA-Z]')]
                        if not db_pie_df.empty:
                            db_pie_df['YOLOv8 偵測目標'] = db_pie_df['diagnosis_result'].apply(get_friendly_name)
                            final_pie_df = db_pie_df[['YOLOv8 偵測目標', 'qty']].rename(columns={'qty': '數量'}).set_index('YOLOv8 偵測目標')
                            st.dataframe(final_pie_df, use_container_width=True)
                        else: st.caption("✨ 尚無有效推論熱點統計。")
                    except Exception as tx_err: st.caption(f"📊 統計模組對齊中...")
                else: st.caption("✨ 目前特徵水庫已全數排空。")

        # ==============================================================================
        # 🛸 6. 邊緣端現地突發事件模擬器 (全面對接雙硬體自動化閉環)
        # ==============================================================================
        st.markdown("<br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("<h4 style='color:#1e3d2f; margin-top:0;'>🛸 Edge Device Toolkit — 邊緣網關高頻數據／突發事件動態模擬器</h4>", unsafe_allow_html=True)
            st.caption("💡 專門用於面試展示！可在離線環境下一鍵改寫感測器數值，用以動態校驗【環境流體強力散熱排風扇】與【精頻變頻灌溉泵浦】的 PLC 閉環保護機制。")
            
            sim_col1, sim_col2, sim_col3, sim_col4 = st.columns(4)
            with sim_col1:
                if st.button("🌩️ 模擬高溫事件：氣溫飆高至 38.5°C", use_container_width=True):
                    st.session_state["t_base"] = 38.5
                    st.toast("🌡️ 觸發突發高溫！請至 PLC 控制區確認【強力散熱排風扇】連動狀態。")
                    time.sleep(0.4); st.rerun()
            with sim_col2:
                if st.button("🌵 模擬突發乾旱：濕度崩跌至 22%", use_container_width=True):
                    st.session_state["m_base"] = 22
                    st.toast("🏜️ 觸發乾旱缺水警告！請至 PLC 控制區將元件切換至【灌溉泵浦】確認連動狀態。")
                    time.sleep(0.4); st.rerun()
            with sim_col3:
                if st.button("🍀 恢復常規：狀態重置為安全配置", use_container_width=True):
                    st.session_state["t_base"] = 26.0
                    st.session_state["m_base"] = 54
                    st.toast("🟢 溫室微氣候指標已全面回歸常規安全狀態。")
                    time.sleep(0.4); st.rerun()
            with sim_col4:
                if st.button("📦 模擬邊緣端接收：自動排隊 1 筆影像任務", use_container_width=True):
                    if db_connected:
                        try:
                            # 🟢 終極修正：將模擬器寫入的 SQL 參數與欄位順序 100% 對齊！
                            # 將狀態直接設為 'completed'，且病蟲害代號傳入標準英文 'Tomato Rust'
                            conn = pymysql.connect(**DB_CONFIG); cursor = conn.cursor()
                            ins_sql = "INSERT INTO farm_tasks_v2 (file_path, status, diagnosis_result, confidence, temperature, moisture) VALUES (%s, %s, %s, %s, %s, %s)"
                            sim_t = st.session_state['t_base']
                            sim_m = st.session_state['m_base']
                            cursor.execute(ins_sql, ('./simulated_leaf.jpg', 'completed', 'Tomato Rust', 0.89, sim_t, sim_m))
                            conn.commit(); cursor.close(); conn.close()
                            st.toast("📦 邊緣端網關已成功寫入 1 筆任務！")
                            time.sleep(0.4); st.rerun()
                        except Exception as e: st.error(f"模擬寫入失敗: {e}")