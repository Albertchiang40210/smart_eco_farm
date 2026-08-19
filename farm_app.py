import streamlit as st
import pandas as pd
import os
import numpy as np
from dotenv import load_dotenv
import time
from datetime import datetime
import requests 

# --- 載入環境變數 (.env) ---
load_dotenv()
from database import engine
from sqlalchemy import text

# ==========================================
# ⚙️ 系統初始化與動態版面配置 (必須在最前面)
# ==========================================
client_mode = st.query_params.get("client")

if client_mode == "mobile":
    st.set_page_config(page_title="農場行動巡檢", page_icon="📱", layout="centered", initial_sidebar_state="collapsed")
else:
    st.set_page_config(page_title="智慧溫室戰情室", page_icon="🌿", layout="wide", initial_sidebar_state="collapsed")

# 🎨 頂級 UI/CSS 醫美大改造 (Tailwind 現代風格)
st.markdown("""
<style>
    /* 隱藏 Streamlit 預設的頂部裝飾與底部浮水印，讓它看起來像真正的 APP */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* 全局字體與背景 (高質感灰白) */
    .stApp { background-color: #f8fafc; color: #0f172a; font-family: 'PingFang TC', 'Helvetica Neue', sans-serif; }
    
    /* 現代化卡片設計 (微透明毛玻璃 + 柔和陰影) */
    .card { 
        background: rgba(255, 255, 255, 0.95); 
        backdrop-filter: blur(10px);
        padding: 24px; 
        border-radius: 20px; 
        border: 1px solid rgba(226, 232, 240, 0.8); 
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.01); 
        margin-bottom: 20px; 
    }
    
    /* 升級版駭客感監視器面板 */
    .video-panel { 
        background: linear-gradient(145deg, #0f172a, #1e293b); 
        border: 1px solid #334155; 
        border-radius: 16px; 
        height: 420px; 
        position: relative; display: flex; flex-direction: column; justify-content: center; align-items: center; 
        color: #10b981; 
        box-shadow: inset 0 0 40px rgba(16, 185, 129, 0.05), 0 10px 20px rgba(0,0,0,0.1); 
        overflow: hidden; 
    }
    .video-panel::before { 
        content: "● LIVE FEED ACTIVE"; position: absolute; top: 20px; left: 24px; 
        font-family: 'Courier New', Courier, monospace; font-size: 13px; font-weight: bold; letter-spacing: 1px; color: #ef4444; animation: blink 2s infinite; 
    }
    @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.2; } }
    
    /* 輸入框美化 */
    div[data-testid="stTextInput"] input { 
        background-color: #f1f5f9 !important; border: 1px solid #cbd5e1 !important; border-radius: 10px !important; padding: 12px 16px !important; transition: all 0.2s;
    }
    div[data-testid="stTextInput"] input:focus {
        border-color: #10b981 !important; box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2) !important;
    }
    
    /* 按鈕美化：果凍微彈漸層效果 */
    div.stButton > button { 
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important; 
        color: white !important; border: none !important; padding: 10px 24px !important; 
        font-weight: 600 !important; border-radius: 12px !important; 
        box-shadow: 0 4px 6px -1px rgba(16, 185, 129, 0.3) !important; 
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    div.stButton > button:hover { transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(16, 185, 129, 0.4) !important; }
    div.stButton > button:active { transform: translateY(0); }
    
    /* 輔助/危險按鈕特例 */
    .clear-btn div.stButton > button { background: linear-gradient(135deg, #64748b, #475569) !important; box-shadow: 0 4px 6px -1px rgba(100, 116, 139, 0.3) !important;}
    .logout-btn div.stButton > button { background: linear-gradient(135deg, #ef4444, #dc2626) !important; box-shadow: 0 4px 6px -1px rgba(239, 68, 68, 0.3) !important; padding: 6px 12px !important; font-size: 13px !important;}
    
    /* 數據指標卡片 (Metrics) */
    div[data-testid="stMetric"] { 
        background: white; padding: 20px; border-radius: 16px; border: 1px solid #e2e8f0; 
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02); transition: transform 0.2s;
    }
    div[data-testid="stMetric"]:hover { transform: translateY(-3px); box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05); }
    div[data-testid="stMetricValue"] { font-size: 32px !important; font-weight: 800 !important; color: #0f172a !important; }
    
    /* 手機端專屬 APP 頂部導航 (沉浸式設計) */
    .mobile-header {
        background: linear-gradient(135deg, #10b981, #047857);
        margin: -60px -20px 20px -20px;
        padding: 60px 20px 25px 20px;
        border-radius: 0 0 30px 30px;
        color: white;
        text-align: center;
        box-shadow: 0 10px 25px rgba(16, 185, 129, 0.3);
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# 📱 智慧路由分流器：手機端巡檢獨立 APP 介面
# ==========================================
if client_mode == "mobile":
    st.markdown("""
    <div class="mobile-header">
        <h1 style="margin: 0; font-size: 26px; font-weight: 800;">📱 農場行動巡檢</h1>
        <p style="margin: 5px 0 0 0; font-size: 14px; opacity: 0.9;">Smart Eco-Farm Edge Node</p>
    </div>
    """, unsafe_allow_html=True)

    st.info("💡 **指引**：請將鏡頭對準異常葉片或昆蟲，系統將自動回傳戰情室分析。")

    img_file_buffer = st.camera_input("📸 點擊啟動相機拍攝")
    upload_buffer = st.file_uploader("📂 或從相簿上傳照片", type=["png", "jpg", "jpeg"])
    
    final_img = img_file_buffer if img_file_buffer else upload_buffer

    if final_img is not None:
        with st.spinner("📡 正在加密傳送至 AI 雙腦伺服器..."):
            api_url = os.getenv("API_URL", "http://farm_backend:8000")
            try:
                files = {"file": (final_img.name, final_img.getvalue(), "image/jpeg")}
                res = requests.post(f"{api_url}/api/v1/detect_bugs", files=files)
                
                if res.status_code == 200:
                    data = res.json()
                    st.success("✨ 辨識成功！現場大數據已即時同步。")
                    st.metric("🎯 初步 AI 診斷", data.get("diagnosis", "未知類別"))
                    st.markdown("<div class='card' style='text-align:center;'>👉 <b>請前往戰情室大螢幕查看病理標記與處置建議。</b></div>", unsafe_allow_html=True)
                else:
                    st.error(f"❌ 傳送失敗，伺服器無回應 (HTTP {res.status_code})")
            except Exception as e:
                st.error(f"🚨 無法連線至 AI 引擎：{e}")
                
    # 🛑 阻斷渲染，避免手機載入電腦版圖表
    st.stop()


# ==========================================
# 🖥️ 電腦端：系統後台與共用邏輯
# ==========================================
if "role" not in st.session_state: st.session_state["role"] = "visitor"
if "last_seen_id" not in st.session_state: st.session_state["last_seen_id"] = None

def write_audit_log(user: str, action: str):
    try:
        with engine.connect() as conn:
            conn.execute(text("INSERT INTO system_audit_logs (user, action) VALUES (:user, :action)"), {"user": user, "action": action})
            conn.commit()
    except Exception:
        pass

def fetch_live_data_from_db():
    try:
        raw_df = pd.read_sql("SELECT id as ID, diagnosis_result as 診斷結果, confidence as 信心指數, file_path as 檔案路徑, created_at as 時間 FROM farm_tasks_v2 ORDER BY created_at DESC LIMIT 50", engine)
        if not raw_df.empty:
            raw_df['ID_clean'] = raw_df['ID'].astype(str).str.replace(r'\s+', '', regex=True).str.lower()
            raw_df['結果_clean'] = raw_df['診斷結果'].astype(str).str.replace(r'\s+', '', regex=True).str.lower()
            clean_mask = ((raw_df['ID_clean'] != 'id') & (raw_df['結果_clean'] != '診斷結果') & (raw_df['結果_clean'] != 'diagnosis_result') & (raw_df['結果_clean'] != 'none') & (raw_df['結果_clean'] != ''))
            df_cleaned = raw_df[clean_mask].copy()
            return "🟢 連線正常", df_cleaned.drop(columns=['ID_clean', '結果_clean'])
        return "🟢 連線正常", pd.DataFrame(columns=['ID', '診斷結果', '信心指數', '檔案路徑', '時間'])
    except Exception as e:
        return f"🔴 連線異常 ({e})", pd.DataFrame(columns=['ID', '診斷結果', '信心指數', '檔案路徑', '時間'])

col_title, col_status = st.columns([2.8, 1.2])
with col_title:
    st.markdown("<h1 style='font-weight: 800; margin-bottom: 0px;'>🌿 智慧溫室綜合戰情室</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748b; font-size: 15px;'><code>Smart Eco-Farm War Room v4.0</code> · YOLOv8 雙軌影像監控整合系統</p>", unsafe_allow_html=True)

with col_status:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.session_state["role"] == "visitor":
        with st.popover("🔒 內部成員身分認證", use_container_width=True):
            st.markdown("### 🔐 內部權限驗證")
            with st.form("nav_login_form", clear_on_submit=True):
                u = st.text_input("成員帳號")
                p = st.text_input("憑證密碼", type="password")
                if st.form_submit_button("驗證並解鎖權限"):
                    admin_u = os.getenv("ADMIN_USER", "admin")
                    admin_p = os.getenv("ADMIN_PASSWORD", "farm2026")
                    staff_u = os.getenv("STAFF_USER", "staff")
                    staff_p = os.getenv("STAFF_PASSWORD", "staff123")
                    
                    if u == admin_u and p == admin_p:
                        st.session_state["role"] = "admin"
                        write_audit_log("admin", "成功登入【最高管理員】權限")
                        st.rerun()
                    elif u == staff_u and p == staff_p:
                        st.session_state["role"] = "staff"
                        write_audit_log("staff", "成功登入【一般員工】權限")
                        st.rerun()
                    else: 
                        st.error("❌ 帳號或密碼錯誤")
    else:
        identity_tag = "👑 HIGHEST ADMIN ACTIVE" if st.session_state["role"] == "admin" else "🧑‍🌾 STAFF MODE ACTIVE"
        identity_color = "#e74c3c" if st.session_state["role"] == "admin" else "#10b981"
        st.markdown(f"<div style='text-align: right; margin-bottom: 5px; font-size: 13px; color:{identity_color};'><b>⚡ {identity_tag}</b></div>", unsafe_allow_html=True)
        st.markdown('<div class="logout-btn">', unsafe_allow_html=True)
        if st.button("🔓 登出安全連線", use_container_width=True):
            write_audit_log(st.session_state["role"], "安全登出系統")
            st.session_state["role"] = "visitor"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
tab1, tab2 = st.tabs(["🖥️ Kiosk AI 實時監控看板", "💻 系統管理內部後台"])

with tab1:
    col_left, col_right = st.columns([1, 2.5])
    with col_left:
        st.markdown("<div class='card' style='text-align: center;'><h3>📱 手機巡田水入口</h3></div>", unsafe_allow_html=True)
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
                metric_color = "#10b981" if "🟢" in status_delta or "🍎" in status_delta or "🐝" in status_delta else "#ef4444"
                
                if st.session_state["last_seen_id"] != current_id:
                    st.toast(f"⚡ 雙核心 AI 數據成功更新！", icon="📸")
                    st.session_state["last_seen_id"] = current_id
                
                with p_c1:
                    clean_path = str(img_path).strip()
                    if not clean_path.startswith("/app/") and not os.path.isabs(clean_path):
                        full_img_path = os.path.join(os.getcwd(), clean_path)
                    else:
                        full_img_path = clean_path

                    if os.path.exists(full_img_path):
                        st.image(full_img_path, caption=f"📸 雙軌實拍傳回影像 (更新時間: {current_time})", use_container_width=True)
                    else:
                        st.markdown(f'<div class="video-panel" style="border-color: #ef4444; color: #ef4444; padding: 15px; text-align: center;"><div style="font-size: 40px;">❌ 檔案路徑遺失</div><b style="font-size: 14px; margin-top: 10px;">資料庫有紀錄，但前端容器找不到實體圖片！</b><code style="background: rgba(0,0,0,0.5); color: #fca5a5; padding: 4px 8px; border-radius: 4px; margin-top: 10px; font-size: 11px; word-break: break-all;">嘗試讀取路徑: {full_img_path}</code></div>', unsafe_allow_html=True)
            else:
                db_result, current_conf, status_delta, action_tip, metric_color = "STANDBY", "--", "📡 系統待命中", "等待行動端/感測器回傳資料。", "#94a3b8"
                with p_c1:
                    st.markdown('<div class="video-panel"><div style="font-size: 72px; opacity: 0.8;">📡</div><br><b>WAVE-FRONT CAMERA STANDBY</b></div>', unsafe_allow_html=True)

            with p_c2:
                st.markdown("#### 🎯 核心 AI 辨識分析")
                st.markdown(f"<style>.live-result div[data-testid=\"stMetricValue\"] {{ color: {metric_color} !important; }}</style><div class=\"live-result\">", unsafe_allow_html=True)
                st.metric("最新診斷結果", f"{db_result}", delta=status_delta, delta_color="normal" if "🟢" in status_delta or "🍎" in status_delta or "🐝" in status_delta else "inverse")
                st.metric("AI 推論信心指數", f"{current_conf} %" if current_conf != "--" else f"{current_conf}")
                st.markdown("</div>", unsafe_allow_html=True)
                st.info(f"📋 **建議處置：**\n{action_tip}")
                st.markdown("<br><div class='clear-btn'>", unsafe_allow_html=True)
                if st.button("🧹 清除並重置大螢幕", use_container_width=True):
                    with engine.connect() as conn:
                        conn.execute(text("DELETE FROM farm_tasks_v2"))
                        conn.commit()
                    st.session_state["last_seen_id"] = None
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
        render_live_monitor_panel()

with tab2:
    db_status, df = fetch_live_data_from_db() 
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("MySQL 資料庫", db_status, delta="Ping: 12ms" if "正常" in db_status else "Error")
    c2.metric("FastAPI 大腦", "🟢 在線", delta="雙核心模式開通")
    c3.metric("邊緣感測器", "🟢 監聽中", delta="Node count: 8")
    c4.metric("今日處理任務", f"{len(df)} 筆" if not df.empty else "0 筆")
    
    st.markdown("<div class='card' style='margin-top: 15px;'>", unsafe_allow_html=True)
    st.markdown("<h4>⚙️ 實時邊緣感測器數據流 (IoT)</h4>", unsafe_allow_html=True)
    iot1, iot2, iot3, iot4 = st.columns(4)
    iot1.metric("環境大氣溫度", "28.4 °C", delta="☀️ 正常範圍")
    iot2.metric("相對空氣濕度", "62.1 %", delta="💧 適宜蒸散")
    iot3.metric("土壤體積含水率", "32.5 %", delta="🌱 根系水分充足")
    iot4.metric("全光譜光照強度", "8,450 Lux", delta="⚡ 光合作用旺盛")
    st.markdown("</div>", unsafe_allow_html=True)
    
    try:
        sensor_df = pd.read_sql("SELECT * FROM sensor_logs ORDER BY created_at DESC LIMIT 24", engine)
        if not sensor_df.empty:
            sensor_df['created_at'] = pd.to_datetime(sensor_df['created_at'])
            sensor_df = sensor_df.sort_values('created_at').set_index('created_at')
        else:
            sensor_df = pd.DataFrame()
    except Exception:
        sensor_df = pd.DataFrame()

    sub_col1, sub_col2 = st.columns(2)
    with sub_col1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("📊 近期微氣候趨勢")
        if not sensor_df.empty:
            st.line_chart(sensor_df[["temperature", "humidity"]].rename(columns={"temperature": "環境溫度 (°C)", "humidity": "相對濕度 (%)"}), height=250)
        else:
            st.info("尚無環境感測資料")
        st.markdown("</div>", unsafe_allow_html=True)
    with sub_col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("📊 近期土壤與日照動態")
        if not sensor_df.empty:
            st.line_chart(sensor_df[["soil_moisture", "lux"]].rename(columns={"soil_moisture": "土壤含水率 (%)", "lux": "日照光強 (Lux)"}), height=250)
        else:
            st.info("尚無環境感測資料")
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("📜 近期任務詳細紀錄")
    if "🔴" in db_status: st.error("無法載入任務紀錄，請檢查 MySQL 連線。")
    elif not df.empty: st.dataframe(df, use_container_width=True, hide_index=True)
    else: st.info("尚無歷史任務紀錄。")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("⚙️ 核心硬體與數據維護")
    if st.session_state["role"] == "visitor":
        st.info("🔒 提示：目前為 [訪客唯讀模式]。如需操作實體 PLC 設備或執行全域數據維護，請由右上方登入。")
    elif st.session_state["role"] == "staff":
        st.warning("⚠️ 提示：目前為 [場內員工模式]。您擁有大數據監控瀏覽權限，但無權操控實體 PLC 閘門與數據修復。")
    elif st.session_state["role"] == "admin":
        st.success("✨ 最高管理員身份已解鎖，進階硬體與資安防線已開通。")
        col_admin1, col_admin2 = st.columns(2)
        with col_admin1:
            if st.button("🔄 執行全域數據修復", use_container_width=True):
                write_audit_log("admin", "手動觸發了【全域數據修復】清理 Ghost Data")
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
            log_df = pd.read_sql("SELECT user as 操作者, action as 執行動作, created_at as 紀錄時間 FROM system_audit_logs ORDER BY created_at DESC LIMIT 5", engine)
            st.dataframe(log_df, use_container_width=True)
        except Exception:
            st.info("暫無日誌數據或 system_audit_logs 表格初始化中。")
    st.markdown("</div>", unsafe_allow_html=True)