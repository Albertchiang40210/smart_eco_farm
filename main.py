from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from ultralytics import YOLO
from PIL import Image, ImageOps  # 💡 引入 ImageOps 來處理重力感應標籤
from datetime import datetime
import asyncio
import io
import os

from sqlalchemy.orm import Session
from database import SessionLocal, init_db, SensorLog, FarmTask, SystemAuditLog, EnvironmentRule
from notifier import send_alert
import operator
import settings
from loguru import logger
import redis
import json
from auth import create_access_token, authenticate_admin, get_current_user, require_device, require_user_or_device

redis_client = redis.Redis(host=settings.REDIS_HOST, port=6379, db=0, decode_responses=True, socket_connect_timeout=1, socket_timeout=1)

# 設定 Loguru 日誌，自動切割
logger.add("logs/system_{time}.log", rotation="12:00", retention="7 days", level="INFO")

# 💡 引入 actuators.py 裡面的全域單例硬體控制器
from actuators import actuator_controller 

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
    temperature: float = Field(ge=-40, le=80)
    humidity: float = Field(ge=0, le=100)
    soil_moisture: float = Field(ge=0, le=100)
    lux: float = Field(default=0.0, ge=0)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model_insect, model_disease
    logger.info("🔥 [系統啟動] 正在初始化資料庫與載入雙軌制 AI 專家大腦...")
    init_db() # 啟動時初始化資料表
    os.makedirs("result", exist_ok=True)
    if settings.SKIP_MODEL_LOAD:
        logger.warning("SKIP_MODEL_LOAD=1，略過模型載入（僅限測試）")
        yield
        return
    
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
        
    yield
    logger.info("💤 [系統關閉] 釋放資源...")

app = FastAPI(title="Smart Eco-Farm API", version="5.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
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
                let key = localStorage.getItem("device_api_key");
                if (!key) { key = prompt("請輸入裝置 API Key"); if (key) localStorage.setItem("device_api_key", key); }
                const formData = new FormData();
                formData.append("file", file);
                try {
                    const response = await fetch("/api/v1/detect_bugs", { method: "POST", body: formData, headers: { "X-API-Key": key || "" } });
                    if (response.status === 401) { localStorage.removeItem("device_api_key"); statusDiv.innerHTML = "🔒 API Key 錯誤"; return; }
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
async def detect_bugs(
    background: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _auth: str = Depends(require_user_or_device),
):
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(status_code=415, detail="僅接受圖片檔")
    image_bytes = await file.read(settings.MAX_UPLOAD_BYTES + 1)
    if len(image_bytes) > settings.MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="圖片過大")
    if model_insect is None or model_disease is None:
        raise HTTPException(status_code=503, detail="AI 模型尚未載入")
    try:
        
        # 1. 開啟圖片並啟動「重力感應強制翻正雷達」
        raw_image = Image.open(io.BytesIO(image_bytes))
        image = ImageOps.exif_transpose(raw_image) # 💡 核心關鍵：這行會自動看 EXIF 標籤，把拿直的手機照片轉正！
        
        # 2. 生成實體儲存路徑
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
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
            background.add_task(send_alert, f"⚠️ [警報] 溫室內發現異常目標：{diagnosis} (信心度: {top_confidence:.0%})", file_location)
            
        else:
            # 如果畫面上沒有發現 any 蟲子框框，轉交給植物病變分類大腦！
            if hasattr(res_disease[0], 'probs') and res_disease[0].probs is not None:
                top1_idx = int(res_disease[0].probs.top1)
                diagnosis = model_disease.names[top1_idx]
                top_confidence = float(res_disease[0].probs.top1conf)
                logger.info(f"🍂 畫面上無昆蟲框框，轉交植物分類大腦！判定為：{diagnosis} (信心度: {top_confidence:.2f})")
                
                # 🔔 Line 通報 (若不是 Healthy)
                if diagnosis.lower() not in ["healthy", "正常", "apple", "bees"]:
                    background.add_task(send_alert, f"🍂 [警報] 偵測到植物病變：{diagnosis} (信心度: {top_confidence:.0%})", file_location)

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
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("影像診斷失敗")
        raise HTTPException(status_code=400, detail="無法處理此圖片") from e

# 💡 核心整合功能：自動化環控並連動寫入網頁戰情室日誌
OPERATORS = {">": operator.gt, "<": operator.lt, ">=": operator.ge, "<=": operator.le}
ACTUATOR_SETTERS = {"fan": actuator_controller.set_fan, "pump": actuator_controller.set_pump}
ACTUATOR_LABEL = {"fan": "排風扇", "pump": "灌溉水泵"}


def evaluate_rules(rules, readings: dict) -> dict:
    """依資料庫規則計算各執行器的目標狀態；任一規則成立即 ON，否則 OFF。

    回傳 {target: (command, 觸發的規則或 None)}。
    """
    decisions: dict = {}
    for rule in rules:
        target = rule.action_target
        decisions.setdefault(target, ("OFF", None))
        value = readings.get(rule.sensor_type)
        compare = OPERATORS.get(rule.condition_operator)
        if value is None or compare is None:
            continue
        if compare(value, rule.threshold_value):
            decisions[target] = (rule.action_command, rule)
    return decisions


@app.post("/api/v1/sensors")
def receive_sensor_data(
    data: SensorPayload,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    _device: str = Depends(require_device),
):
    logger.info(f"接收數據 {data.device_id}: {data.temperature}°C / {data.humidity}% / 土壤 {data.soil_moisture}%")

    readings = {
        "temperature": data.temperature,
        "humidity": data.humidity,
        "soil_moisture": data.soil_moisture,
        "lux": data.lux,
    }
    db.add(SensorLog(device_id=data.device_id, **readings))

    messages = []
    for target, (command, rule) in evaluate_rules(db.query(EnvironmentRule).all(), readings).items():
        setter = ACTUATOR_SETTERS.get(target)
        if setter is None or not setter(command):
            continue
        label = ACTUATOR_LABEL[target]
        if rule:
            action = f"自動觸發：{rule.rule_name}（{rule.sensor_type} {rule.condition_operator} {rule.threshold_value}，實測 {readings[rule.sensor_type]}）→ {label} {command}"
            background.add_task(send_alert, f"⚙️ {action}")
        else:
            action = f"自動觸發：環境恢復正常 → {label} OFF"
        messages.append(action)
        db.add(SystemAuditLog(user="system", action=action))

    db.commit()
    return {
        "status": "success",
        "alert": " | ".join(messages) if messages else "環境數據穩定，設備維持現狀。",
    }

# ==========================================
# 5. 企業級 JWT 登入與儀表板 API
# ==========================================
@app.post("/api/v1/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if not authenticate_admin(form_data.username, form_data.password):
        raise HTTPException(status_code=400, detail="帳號或密碼錯誤")
    return {"access_token": create_access_token({"sub": form_data.username}), "token_type": "bearer"}


@app.get("/api/v1/health")
def health():
    return {"status": "ok"}


@app.get("/api/v1/sensors/history")
def get_sensor_history(db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    try:
        cached = redis_client.get("sensor_history")
        if cached:
            return json.loads(cached)
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")
        
    logs = db.query(SensorLog).order_by(SensorLog.created_at.desc()).limit(24).all()
    result = [{"temperature": l.temperature, "humidity": l.humidity, "soil_moisture": l.soil_moisture, "lux": l.lux, "created_at": l.created_at.isoformat()} for l in logs]
    
    try:
        redis_client.setex("sensor_history", 10, json.dumps(result))
    except redis.RedisError:
        pass

    return result

@app.get("/api/v1/tasks/history")
def get_task_history(db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    tasks = db.query(FarmTask).order_by(FarmTask.created_at.desc()).limit(20).all()
    return [
        {"id": t.id, "status": t.status, "diagnosis_result": t.diagnosis_result,
         "confidence": t.confidence, "created_at": t.created_at.isoformat()}
        for t in tasks
    ]