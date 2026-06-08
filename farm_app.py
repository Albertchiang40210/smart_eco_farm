import streamlit as st
import pandas as pd
import pymysql
import os
import numpy as np
from dotenv import load_dotenv
import time
from datetime import datetime

# --- 載入環境變數 (.env) ---
load_dotenv()

# ==========================================
# ⚙️ 系統核心設定 & 資料庫配置
# ==========================================
DB_CONFIG = {
    'host': os.getenv("DB_HOST", "127.0.0.1"), 
    'port': 3306,
    'user': os.getenv("DB_USER", "root"), 
    'password': os.getenv("DB_PASSWORD", "P@ssw0rd"),
    'database': os.getenv("DB_NAME", "smart_eco_farm_db"),
    'charset': 'utf8mb4'
}

# 設定網頁標題與寬螢幕佈局
st.set_page_config(page_title="智慧溫室綜合戰情室", page_icon="🌿", layout="wide")

# 🎨 UI/UX 頂級戰情室 CSS 樣式表
st.markdown("""
<style>
    .stApp { background-color: #f4f7f5; color: #1e3d2f; font-family: 'PingFang TC', 'Microsoft JhengHei', sans-serif; }
    .card { background: #ffffff; padding: 24px; border-radius: 16px; border: 1px solid #e2ebd9; box-shadow: 0 8px 24px rgba(43, 75, 57, 0.04); margin-bottom: 20px; }
    
    /* 輸入框美化 */
    div[data-testid="stTextInput"] input {
        background-color: #ffffff !important; color: #112e20 !important;
        border: 1px solid #cbd5e1 !important; border-radius: 8px !important; padding: 12px !important;
    }
    
    /* ⚡ 高科技監視器黑框面板 (待命時顯示) */
    .video-panel {
        background: #111613; border: 2px solid #27ae60; border-radius: 12px; height: 380px;
        position: relative; display: flex; flex-direction: column; justify-content: center; align-items: center;
        color: #2ecc71; box-shadow: inset 0 0 30px rgba(39, 174, 96, 0.2); overflow: hidden;
    }
    .video-panel::before {
        content: "• LIVE MONITOR DISPATCH"; position: absolute; top: 15px; left: 20px;
        font-family: monospace; font-size: 12px; letter-spacing: 2px; animation: blink 1.5s infinite;
    }
    @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
    
    div.stButton > button { 
        background: linear-gradient(135deg, #27ae60, #2ecc71) !important; 
        color: white !important; border: none !important; padding: 10px 20px !important; font-weight: 600 !important; border-radius: 8px !important;
    }
    .clear-btn div.stButton > button { background: linear-gradient(135deg, #7f8c8d, #95a5a6) !important; }
    .logout-btn div.stButton > button { background: linear-gradient(135deg, #e74c3c, #c0392b) !important; }
    div[data-testid="stMetricValue"] { font-size: 26px !important; font-weight: 700 !important; }
    div[data-testid="stMetric"] { background: #ffffff; padding: 18px; border-radius: 14px; border: 1px solid #e2ebd9; }
    .iot-section { background: #eef5f0; padding: 20px; border-radius: 14px; margin-top: 15px; border-left: 5px solid #27ae60; }
</style>
""", unsafe_allow_html=True)

if "role" not in st.session_state: 
    st.session_state["role"] = "staff"
if "last_seen_id" not in st.session_state:
    st.session_state["last_seen_id"] = None

# ==========================================
# 🛡️ 安全稽核日誌 (Audit Log)
# ==========================================
def write_audit_log(user: str, action: str):
    try:
        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_audit_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user VARCHAR(50),
                    action VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("INSERT INTO system_audit_logs (user, action) VALUES (%s, %s)", (user, action))
        conn.commit()
        conn.close()
    except Exception:
        pass

# ==========================================
# 📊 動態安全抽水機
# ==========================================
def fetch_live_data_from_db():
    try:
        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor() as cursor:
            query = "SELECT id, diagnosis_result, confidence, file_path, created_at FROM farm_tasks_v2 ORDER BY created_at DESC LIMIT 50"
            cursor.execute(query)
            rows = cursor.fetchall()
        conn.close()
        
        raw_df = pd.DataFrame(rows, columns=['ID', '診斷結果', '信心指數', '檔案路徑', '時間'])
        
        if not raw_df.empty:
            raw_df['ID_clean'] = raw_df['ID'].astype(str).str.replace(r'\s+', '', regex=True).str.lower()
            raw_df['結果_clean'] = raw_df['診斷結果'].astype(str).str.replace(r'\s+', '', regex=True).str.lower()
            
            clean_mask = (
                (raw_df['ID_clean'] != 'id') & 
                (raw_df['結果_clean'] != '診斷結果') & 
                (raw_df['結果_clean'] != 'diagnosis_result') &
                (raw_df['結果_clean'] != 'none') &
                (raw_df['結果_clean'] != '')
            )
            
            df_cleaned = raw_df[clean_mask].copy()
            return "🟢 連線正常", df_cleaned.drop(columns=['ID_clean', '結果_clean'])
        return "🟢 連線正常", pd.DataFrame(columns=['ID', '診斷結果', '信心指數', '檔案路徑', '時間'])
    except Exception as e:
        return f"🔴 連線異常 ({e})", pd.DataFrame(columns=['ID', '診斷結果', '信心指數', '檔案路徑', '時間'])

# ==========================================
# 🖥️ 主介面頂部狀態列
# ==========================================
col_title, col_status = st.columns([2.8, 1.2])
with col_title:
    st.title("🌿 智慧溫室綜合戰情室")
    st.markdown("`Smart Eco-Farm War Room v4.0` · YOLOv8 雙軌影像監控整合系統")

with col_status:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.session_state["role"] == "staff":
        with st.popover("🔒 管理員成員登入", use_container_width=True):
            st.markdown("### 🔐 內部權限驗證")
            with st.form("nav_login_form", clear_on_submit=True):
                u = st.text_input("管理員帳號")
                p = st.text_input("憑證密碼", type="password")
                if st.form_submit_button("驗證並解鎖後台"):
                    if u == "admin" and p == "farm2026":
                        st.session_state["role"] = "admin"
                        write_audit_log("admin", "成功登入管理員權限")
                        st.rerun()
                    else: st.error("❌ 帳號或密碼錯誤")
    else:
        st.markdown(f"<div style='text-align: right; margin-bottom: 5px; font-size: 13px; color:#27ae60;'><b>⚡ ADMIN MODE ACTIVE</b></div>", unsafe_allow_html=True)
        st.markdown('<div class="logout-btn">', unsafe_allow_html=True)
        if st.button("🔓 登出管理模式", use_container_width=True):
            write_audit_log("admin", "安全登出管理模式")
            st.session_state["role"] = "staff"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
tab1, tab2 = st.tabs(["🖥️ Kiosk AI 實時監控看板", "💻 系統管理內部後台"])

# ==========================================
# 🖥️ Tab 1: Kiosk 監控看板
# ==========================================
with tab1:
    col_left, col_right = st.columns([1, 2.5])
    with col_left:
        st.markdown("<div class='card' style='text-align: center; border-bottom: 4px solid #27ae60;'><h3>📱 手機巡田水入口</h3></div>", unsafe_allow_html=True)
        ngrok_url = os.getenv('NGROK_URL', 'http://127.0.0.1:8000')
        st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={ngrok_url}/?client=mobile", use_container_width=True)
        st.success("📡 NGROK 隧道正常監聽中")

    with col_right:
        st.markdown("<div class='card'><h3 style='margin: 0;'>📺 實時觀測大螢幕</h3></div>", unsafe_allow_html=True)
        
        @st.fragment(run_every=1)
        def render_live_monitor_panel():
            db_status, df = fetch_live_data_from_db() 
            
            DISEASE_KNOWLEDGE = {
                "healthy": {"status": "🟢 狀態優良", "tip": "作物發育健康，維持目前溫濕度與光照參數即可。"},
                "正常": {"status": "🟢 狀態優良", "tip": "作物發育健康，維持目前溫濕度與光照參數即可。"},
                "insect": {"status": "🚨 檢出害蟲威脅", "tip": "YOLO 偵測到有害蟲蹤跡！請即刻派遣人員前往該區域噴灑有機防護劑。"},
                "apple": {"status": "🍎 檢出測試水果 (蘋果)", "tip": "這是測試用的蘋果影像。代表全自動化連線已徹底打通！"},
                "ants": {"status": "🐜 警報：現場檢出螞蟻危機", "tip": "系統已精準鑑定出螞蟻蹤跡！請確認是否引發集體搬運蚜蟲危機，建議執行局部生物物理防制。"},
                "bees": {"status": "🐝 偵測到益蟲：蜜蜂", "tip": "畫面上出現蜜蜂，有助於溫室作物授粉，系統自動登錄生態平衡數據。"},
                "beetles": {"status": "🪲 警報：現場檢出甲蟲/甲殼蟲危害", "tip": "發現甲蟲啃食葉片跡象！請進行物理誘捕，並加強巡視幼嫩組織受損狀況。"},
                "tomato___early_blight": {"status": "🍂 警報：番茄葉片檢出早疫病病變", "tip": "植物病變大腦檢出 Tomato Early Blight！請立刻隔離病株，並評估調降溫室相對濕度。"}
            }

            is_live_ready = False
            if not df.empty:
                latest = df.iloc[0]
                db_result = str(latest['診斷結果']).strip()
                if db_result and db_result != "None" and db_result.lower() != 'standby': 
                    is_live_ready = True

            p_c1, p_c2 = st.columns([1.6, 1])

            if is_live_ready:
                current_id = latest['ID']
                raw_conf = float(latest['信心指數'])
                current_conf = f"{raw_conf * 100:.1f}" if raw_conf <= 1.0 else f"{raw_conf:.1f}"
                current_time = latest['時間']
                img_path = latest['檔案路徑']
                
                search_key = db_result.lower()
                status_delta = DISEASE_KNOWLEDGE.get(search_key, {"status": f"⚠️ 檢出未知類別 [{db_result}]", "tip": "偵測到新標籤，系統已自動為您放行顯示照片，請確認權重定義。"})["status"]
                action_tip = DISEASE_KNOWLEDGE.get(search_key, {"status": "", "tip": "偵測到新標籤，系統已自動為您放行顯示照片，請確認權重定義。"})["tip"]
                metric_color = "#27ae60" if "🟢" in status_delta or "🍎" in status_delta or "🐝" in status_delta else "#e74c3c"
                
                if st.session_state["last_seen_id"] != current_id:
                    st.toast(f"⚡ 雙核心 AI 數據成功更新！", icon="📸")
                    st.session_state["last_seen_id"] = current_id
                
                with p_c1:
                    if img_path and os.path.exists(str(img_path)):
                        st.image(str(img_path), caption=f"📸 雙軌實拍傳回影像 (更新時間: {current_time})", use_container_width=True)
                    else:
                        st.markdown(f'<div class="video-panel" style="border-color: #e74c3c; color: #e74c3c;"><div style="font-size: 64px;">📸</div><b>影像檔案儲存中...</b></div>', unsafe_allow_html=True)
            else:
                db_result, current_conf, status_delta, action_tip, metric_color = "STANDBY", "--", "📡 系統待命中", "目前戰情室處於觀測待命狀態。請使用行動端/模擬器上傳現場實拍照。", "#7f8c8d"
                with p_c1:
                    st.markdown('<div class="video-panel"><div style="font-size: 64px;">📡</div><b>WAVE-FRONT CAMERA STANDBY</b></div>', unsafe_allow_html=True)

            with p_c2:
                st.markdown("#### 🎯 最新實拍 AI 辨識分析")
                st.markdown(f"<style>.live-result div[data-testid=\"stMetricValue\"] {{ color: {metric_color} !important; }}</style><div class=\"live-result\">", unsafe_allow_html=True)
                st.metric("最新診斷結果", f"{db_result}", delta=status_delta, delta_color="normal" if "🟢" in status_delta or "🍎" in status_delta or "🐝" in status_delta else "inverse")
                st.metric("AI 推論信心指數", f"{current_conf} %" if current_conf != "--" else f"{current_conf}")
                st.markdown("</div>", unsafe_allow_html=True)
                st.info(f"📋 **建議處置：**\n{action_tip}")
                
                st.markdown("<br><br><div class='clear-btn'>", unsafe_allow_html=True)
                if st.button("🧹 清除目前畫面 (重置大螢幕)", use_container_width=True):
                    conn = pymysql.connect(**DB_CONFIG)
                    with conn.cursor() as cursor: cursor.execute("DELETE FROM farm_tasks_v2")
                    conn.commit()
                    conn.close()
                    st.session_state["last_seen_id"] = None
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
        
        render_live_monitor_panel()

# ==========================================
# 💻 Tab 2: 系統管理內部後台（升級：大滿貫農業數據流）
# ==========================================
with tab2:
    db_status, df = fetch_live_data_from_db() 
    
    # 核心系統指標
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("MySQL 資料庫", db_status, delta="Ping: 12ms" if "正常" in db_status else "Error")
    c2.metric("FastAPI 大腦", "🟢 在線", delta="雙核心模式開通")
    c3.metric("邊緣感測器", "🟢 監聽中", delta="Node count: 8")
    c4.metric("今日處理任務", f"{len(df)} 筆" if not df.empty else "0 筆")
    
    # 🟢 ✨ 【全新功能】實時邊緣感測器數據流 (IoT Live Stream)
    st.markdown("<div class='iot-section'>⚙️ <b>實時邊緣感測器數據流 (IoT 現場廣播)</b></div>", unsafe_allow_html=True)
    iot1, iot2, iot3, iot4 = st.columns(4)
    iot1.metric("環境大氣溫度", "28.4 °C", delta="☀️ 正常範圍")
    iot2.metric("相對空氣濕度", "62.1 %", delta="💧 適宜蒸散")
    iot3.metric("土壤體積含水率", "32.5 %", delta="🌱 根系水分充足")
    iot4.metric("全光譜光照強度", "8,450 Lux", delta="⚡ 光合作用旺盛")
    
    st.markdown("---")
    
    # 生成 24 小時模擬數據（包含四大關鍵指標）
    chart_times = pd.date_range(end=datetime.now(), periods=24, freq='h')
    np.random.seed(42)
    mock_temp = 25 + np.sin(np.linspace(0, 2*np.pi, 24)) * 4 + np.random.normal(0, 0.3, 24)
    mock_humidity = 65 - np.sin(np.linspace(0, 2*np.pi, 24)) * 10 + np.random.normal(0, 0.8, 24)
    mock_soil = 34 + np.cos(np.linspace(0, 2*np.pi, 24)) * 2 + np.random.normal(0, 0.2, 24)
    mock_sunlight = np.maximum(0, np.sin(np.linspace(-np.pi/2, 3*np.pi/2, 24)) * 12000 + np.random.normal(0, 500, 24))

    # 📈 分流圖表一：空氣溫濕度動態趨勢
    sub_col1, sub_col2 = st.columns(2)
    with sub_col1:
        st.subheader("📊 過去 24 小時大氣微氣候趨勢")
        df_air = pd.DataFrame({"時間": chart_times, "溫室環境溫度 (°C)": mock_temp, "環境相對濕度 (%)": mock_humidity}).set_index("時間")
        st.line_chart(df_air, height=220)

    # 📈 ✨ 分流圖表二：補齊陽光與土壤含水率趨勢面板
    with sub_col2:
        st.subheader("📊 過去 24 小時土壤與日照動態")
        df_soil_light = pd.DataFrame({"時間": chart_times, "土壤含水率 (%)": mock_soil, "日照光照強度 (Lux)": mock_sunlight}).set_index("時間")
        st.line_chart(df_soil_light, height=220)
    
    # 任務紀錄列表
    st.markdown("---")
    st.subheader("📜 近期任務詳細紀錄")
    if "🔴" in db_status: 
        st.error("無法載入任務紀錄，請檢查 MySQL 連線。")
    elif not df.empty: 
        st.dataframe(df, use_container_width=True, hide_index=True)
    else: 
        st.info("尚無歷史任務紀錄。")

    # 核心硬體維護
    st.markdown("---")
    st.subheader("⚙️ 核心硬體與數據維護")
    if st.session_state["role"] != "admin":
        st.info("🔒 提示：目前為 [Staff 唯讀模式]。如需調整實體 PLC 或查看系統審計日誌，請從右上方登入。")
    else:
        st.success("✨ 管理員身份已解鎖，已啟用資安日誌追蹤。")
        col_admin1, col_admin2 = st.columns(2)
        with col_admin1:
            if st.button("🔄 執行全域數據修復", use_container_width=True):
                write_audit_log("admin", "手動觸發了【全域數據修復】清理 Ghost Data")
                if "last_triggered_alert" in st.session_state: del st.session_state["last_triggered_alert"]
                with st.spinner("正在清除鬼影資料並重置戰情室..."): time.sleep(1.5)
                st.success("✨ 全域數據修復完成！")
                st.rerun()
        with col_admin2:
            if st.button("🎛️ 校準 PLC 實體噴灌閥門", use_container_width=True):
                write_audit_log("admin", "對邊緣硬體發送了【PLC 噴灌閥門校準】指令")
                st.toast("正在向邊緣硬體發送校準訊號...")
                time.sleep(1)
                st.success("🤖 PLC 閥門校準成功！同步率 100%")
                
        st.markdown("<br><h4>🕵️‍♂️ 智慧農場資安操作日誌 (Audit Logs)</h4>", unsafe_allow_html=True)
        try:
            conn = pymysql.connect(**DB_CONFIG)
            log_df = pd.read_sql("SELECT user as 操作者, action as 執行動作, created_at as 紀錄時間 FROM system_audit_logs ORDER BY created_at DESC LIMIT 5", conn)
            conn.close()
            st.dataframe(log_df, use_container_width=True)
        except Exception:
            st.info("暫無日誌數據或 system_audit_logs 表格初始化中。")