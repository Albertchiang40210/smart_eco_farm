from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from ultralytics import YOLO
from PIL import Image, ImageOps  # 💡 引入 ImageOps 來處理重力感應標籤
from dotenv import load_dotenv
from datetime import datetime
import asyncio
import io
import os

from sqlalchemy.orm import Session
from database import SessionLocal, init_db, SensorLog, FarmTask, SystemAuditLog, EnvironmentRule
from notifier import send_line_alert
from loguru import logger
import redis
import json
from auth import create_access_token, get_password_hash, verify_password, get_current_user

redis_client = redis.Redis(host=os.getenv("REDIS_HOST", "localhost"), port=6379, db=0, decode_responses=True)

# 設定 Loguru 日誌，自動切割
logger.add("logs/system_{time}.log", rotation="12:00", retention="7 days", level="INFO")

# 💡 引入 actuators.py 裡面的全域單例硬體控制器
from actuators import actuator_controller 

load_dotenv()

# 🧠 宣告雙核心專家大腦
model_insect = None
model_disease = None

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 💡 定義從 sensors.py 傳過來的 IoT 資料格式
class SensorPayload(BaseModel):
    device_id: str
    temperature: float
    humidity: float
    soil_moisture: float

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model_insect, model_disease
    logger.info("🔥 [系統啟動] 正在初始化資料庫與載入雙軌制 AI 專家大腦...")
    init_db() # 啟動時初始化資料表
    
    path_insect_onnx = "result/train/weights/best.onnx"
    path_insect = "result/train/weights/best.pt"
    if os.path.exists(path_insect_onnx):
        model_insect = YOLO(path_insect_onnx, task='detect')
        logger.info("✅ [模型成功] 昆蟲 ONNX 加速大腦已就位！")
    elif os.path.exists(path_insect):
        model_insect = YOLO(path_insect)
        logger.info("✅ [模型成功] 昆蟲物件偵測大腦已就位！")
    else:
        logger.warning(f"⚠️ [模型缺失] 找不到昆蟲權重")
        model_insect = YOLO("yolov8s.pt")

    path_disease_onnx = "result/runs/classify/train/weights/best.onnx"
    path_disease = "result/runs/classify/train/weights/best.pt"
    if os.path.exists(path_disease_onnx):
        model_disease = YOLO(path_disease_onnx, task='classify')
        logger.info("✅ [模型成功] 植物病變 ONNX 加速大腦已就位！")
    elif os.path.exists(path_disease):
        model_disease = YOLO(path_disease)
        logger.info("✅ [模型成功] 植物病變影像分類大腦已就位！")
    else:
        logger.warning(f"⚠️ [模型缺失] 找不到植物病變權重")
        model_disease = YOLO("yolov8s.pt")
        
    os.makedirs("result", exist_ok=True)
    yield
    logger.info("💤 [系統關閉] 釋放資源...")

app = FastAPI(title="智慧生態農場雙軌 API", version="4.1", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
def render_mobile_page():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>📱 智慧溫室 · 現場巡檢端</title>
        <style>
            body { font-family: system-ui; background: #f4f7f5; color: #1e3d2f; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; }
            .container { background: white; padding: 35px 25px; border-radius: 24px; box-shadow: 0 12px 40px rgba(43,75,57,0.06); text-align: center; width: 85%; max-width: 380px; border: 1px solid #e2ebd9; }
            .upload-btn { background: linear-gradient(135deg, #27ae60, #2ecc71); color: white; padding: 16px; border-radius: 14px; font-size: 16px; font-weight: bold; border: none; width: 100%; box-shadow: 0 6px 20px rgba(39,174,96,0.15); }
            .status { margin-top: 25px; font-size: 14px; color: #7f8c8d; font-weight: 600; padding: 10px; background: #fafafa; border-radius: 8px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div style="font-size: 50px;">🐜</div>
            <h2>智慧雙軌巡檢系統</h2>
            <p>拍攝現場「昆蟲」或「生病葉片」，系統將自動智慧分流給物件偵測或分類模型處理。</p>
            <input type="file" id="file-input" accept="image/*" capture="environment" style="display:none;">
            <button class="upload-btn" onclick="document.getElementById('file-input').click()">📸 啟動相機拍照診斷</button>
            <div id="upload-status" class="status">📡 系統就緒，等待拍照...</div>
        </div>
        <script>
            document.getElementById('file-input').addEventListener('change', async function(e) {
                const file = e.target.files[0];
                if (!file) return;
                const statusDiv = document.getElementById('upload-status');
                statusDiv.innerHTML = "⏳ 雙模組 AI 聯手鑑定中...";
                const formData = new FormData();
                formData.append("file", file);
                try {
                    const response = await fetch("/api/v1/detect_bugs", { method: "POST", body: formData });
                    const data = await response.json();
                    if (data.status === "success") {
                        statusDiv.innerHTML = `✅ 鑑定完成：${data.diagnosis} (${Math.round(data.confidence * 100)}%)`;
                    }
                } catch (error) {
                    statusDiv.innerHTML = "🚨 連線失敗，請檢查 NGROK";
                }
            });
        </script>
    </body>
    </html>
    """

def run_yolo_inference(image):
    # 此函式會在 ThreadPool 中執行，避免阻塞事件迴圈
    res_insect = model_insect(image)
    res_disease = model_disease(image)
    return res_insect, res_disease

@app.post("/api/v1/detect_bugs")
async def detect_bugs(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        image_bytes = await file.read()
        
        # 1. 開啟圖片並啟動「重力感應強制翻正雷達」
        raw_image = Image.open(io.BytesIO(image_bytes))
        image = ImageOps.exif_transpose(raw_image) # 💡 核心關鍵：這行會自動看 EXIF 標籤，把拿直的手機照片轉正！
        
        # 2. 生成實體儲存路徑
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_location = os.path.join("result", f"mobile_{timestamp}.jpg")
        
        # 3. 將翻正後的圖片儲存到本地
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        image.save(file_location, "JPEG", quality=90)

        # 4. 雙腦同時平行開工！ (改為非同步執行)
        res_insect, res_disease = await asyncio.to_thread(run_yolo_inference, image)
        
        diagnosis = "Healthy"
        top_confidence = 0.0
        
        # 🎯 智慧決策分流器：優先看昆蟲大腦有沒有「圈出框框」
        if len(res_insect[0].boxes) > 0 and float(res_insect[0].boxes[0].conf[0]) > 0.25:
            box = res_insect[0].boxes[0]
            class_id = int(box.cls[0])
            diagnosis = model_insect.names[class_id]
            top_confidence = float(box.conf[0])
            logger.info(f"🐜 昆蟲偵測大腦勝出！圈出目標類別：{diagnosis} (信心度: {top_confidence:.2f})")
            
            # ✨ 將帶有綠色方框的推論圖片存下來，覆蓋原本翻正後的圖片
            res_insect[0].save(filename=file_location)
            
            # 🔔 Line 通報
            send_line_alert(f"⚠️ [警報] 溫室內發現異常目標：{diagnosis} (信心度: {top_confidence:.0%})", file_location)
            
        else:
            # 如果畫面上沒有發現 any 蟲子框框，轉交給植物病變分類大腦！
            if hasattr(res_disease[0], 'probs') and res_disease[0].probs is not None:
                top1_idx = int(res_disease[0].probs.top1)
                diagnosis = model_disease.names[top1_idx]
                top_confidence = float(res_disease[0].probs.top1conf)
                logger.info(f"🍂 畫面上無昆蟲框框，轉交植物分類大腦！判定為：{diagnosis} (信心度: {top_confidence:.2f})")
                
                # 🔔 Line 通報 (若不是 Healthy)
                if diagnosis.lower() not in ["healthy", "正常", "apple", "bees"]:
                    send_line_alert(f"🍂 [警報] 偵測到植物病變：{diagnosis} (信心度: {top_confidence:.0%})", file_location)

        # 寫入 MySQL (透過 SQLAlchemy)
        new_task = FarmTask(
            file_path=file_location,
            status='completed',
            diagnosis_result=diagnosis,
            confidence=top_confidence
        )
        db.add(new_task)
        db.commit()

        return {"status": "success", "diagnosis": diagnosis, "confidence": round(top_confidence, 2)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# 💡 核心整合功能：自動化環控並連動寫入網頁戰情室日誌
@app.post("/api/v1/sensors")
def receive_sensor_data(data: SensorPayload, db: Session = Depends(get_db)):
    try:
        logger.info(f"📊 [接收數據] {data.device_id} -> 氣溫: {data.temperature}°C, 濕度: {data.humidity}%, 土壤: {data.soil_moisture}%")
        
        log_messages = []
        db_actions = []

        # 💡 動態載入智慧規則
        rules = db.query(EnvironmentRule).all()
        temp_high_rule = next((r for r in rules if r.sensor_type == 'temperature' and r.condition_operator == '>'), None)
        hum_low_rule = next((r for r in rules if r.sensor_type == 'humidity' and r.condition_operator == '<'), None)
        
        temp_threshold = temp_high_rule.threshold_value if temp_high_rule else 28.0
        hum_threshold = hum_low_rule.threshold_value if hum_low_rule else 65.0

        # 🌬️ 1. 氣溫環境監控邏輯 (排風扇控制)
        if data.temperature > temp_threshold:
            if actuator_controller.set_fan("ON"):
                action_text = f"自動觸發：因氣溫過高 ({data.temperature}°C > {temp_threshold}) 開啟排風扇降溫"
                log_messages.append(f"🔥 {action_text}")
                db_actions.append(action_text)
        else:
            if actuator_controller.set_fan("OFF"):
                if actuator_controller.fan_status == "ON": # 只有原本開著才記錄關閉
                    action_text = f"自動觸發：氣溫回落 ({data.temperature}°C) 關閉排風扇"
                    log_messages.append(f"🍃 {action_text}")
                    db_actions.append(action_text)

        # 💦 2. 濕度環境監控邏輯 (灌溉水泵控制)
        if data.humidity < hum_threshold:
            if actuator_controller.set_pump("ON"):
                action_text = f"自動觸發：因環境濕度過低 ({data.humidity}% < {hum_threshold}) 開啟變頻灌溉水泵"
                log_messages.append(f"🚨 {action_text}")
                db_actions.append(action_text)
        else:
            if actuator_controller.set_pump("OFF"):
                if actuator_controller.pump_status == "ON": # 只有原本開著才記錄關閉
                    action_text = f"自動觸發：環境濕度達標 ({data.humidity}%) 關閉變頻灌溉水泵"
                    log_messages.append(f"✅ {action_text}")
                    db_actions.append(action_text)

        # 寫入真實 Sensor 數據到資料庫
        new_sensor_log = SensorLog(
            device_id=data.device_id,
            temperature=data.temperature,
            humidity=data.humidity,
            soil_moisture=data.soil_moisture,
            lux=getattr(data, 'lux', 0.0) # 如果 payload 有 lux
        )
        db.add(new_sensor_log)

        # 寫入系統日誌
        for action in db_actions:
            new_audit = SystemAuditLog(user='system', action=action)
            db.add(new_audit)
            
            # 🔔 異常動作 Line 通報
            if "開啟" in action:
                send_line_alert(f"⚙️ [自動控制觸發] {action}")
            
        db.commit()

        # 4. 組裝回傳封包給 sensors.py 端顯示
        alert_info = " | ".join(log_messages) if log_messages else "環境數據穩定，硬體設備維持現狀。"
        return {
            "status": "success",
            "message": "感測器核心數據已同步接收",
            "alert": f"【系統核心決策】{alert_info}"
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ==========================================
# 5. 企業級 JWT 登入與儀表板 API
# ==========================================
fake_users_db = {
    "admin": {
        "username": "admin",
        "hashed_password": get_password_hash("secret"),
    }
}

@app.post("/api/v1/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user_dict = fake_users_db.get(form_data.username)
    if not user_dict or not verify_password(form_data.password, user_dict["hashed_password"]):
        raise HTTPException(status_code=400, detail="帳號或密碼錯誤")
    
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/v1/sensors/history")
def get_sensor_history(db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    try:
        cached = redis_client.get("sensor_history")
        if cached:
            return json.loads(cached)
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")
        
    logs = db.query(SensorLog).order_by(SensorLog.created_at.desc()).limit(24).all()
    result = [{"temperature": l.temperature, "humidity": l.humidity, "soil_moisture": l.soil_moisture, "created_at": l.created_at.isoformat()} for l in logs]
    
    try:
        redis_client.setex("sensor_history", 10, json.dumps(result))
    except:
        pass
        
    return result

@app.get("/api/v1/tasks/history")
def get_task_history(db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    tasks = db.query(FarmTask).order_by(FarmTask.created_at.desc()).limit(20).all()
    return tasks