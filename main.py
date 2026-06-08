from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from ultralytics import YOLO
from PIL import Image, ImageOps  # 💡 引入 ImageOps 來處理重力感應標籤
from dotenv import load_dotenv
from datetime import datetime
import pymysql
import io
import os

load_dotenv()

# 🧠 宣告雙核心專家大腦
model_insect = None
model_disease = None

def get_db_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "P@ssw0rd"),
        database=os.getenv("DB_NAME", "smart_eco_farm_db"),
        charset="utf8mb4"
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model_insect, model_disease
    print("🔥 [系統啟動] 正在載入雙軌制 AI 專家大腦...")
    
    path_insect = "result/train/weights/best.pt"
    if os.path.exists(path_insect):
        model_insect = YOLO(path_insect)
        print("✅ [模型成功] 昆蟲物件偵測大腦已就位！")
    else:
        print(f"⚠️ [模型缺失] 找不到昆蟲權重 {path_insect}")
        model_insect = YOLO("yolov8s.pt")

    path_disease = "result/runs/classify/train/weights/best.pt"
    if os.path.exists(path_disease):
        model_disease = YOLO(path_disease)
        print("✅ [模型成功] 植物病變影像分類大腦已就位！")
    else:
        print(f"⚠️ [模型缺失] 找不到植物病變權重 {path_disease}")
        model_disease = YOLO("yolov8s.pt")
        
    os.makedirs("result", exist_ok=True)
    yield
    print("💤 [系統關閉] 釋放資源...")

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
                        statusDiv.innerHTML = `✅ 鑑定完成：\${data.diagnosis} (\${Math.round(data.confidence * 100)}%)`;
                    }
                } catch (error) {
                    statusDiv.innerHTML = "🚨 連線失敗，請檢查 NGROK";
                }
            });
        </script>
    </body>
    </html>
    """

@app.post("/api/v1/detect_bugs")
def detect_bugs(file: UploadFile = File(...)):
    try:
        image_bytes = file.file.read()
        
        # 1. 開啟圖片並啟動「重力感應強制翻正雷達」
        raw_image = Image.open(io.BytesIO(image_bytes))
        image = ImageOps.exif_transpose(raw_image) # 💡 核心關鍵：這行會自動看 EXIF 標籤，把拿直的手機照片轉正！
        
        # 2. 生成實體儲存路徑
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_location = f"result/mobile_{timestamp}.jpg"
        
        # 3. 將翻正後的圖片儲存到本地（如果是 PNG 會自動轉 RGB 存 JPEG）
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        image.save(file_location, "JPEG", quality=90)

        # 4. 雙腦同時平行開工！
        res_insect = model_insect(image)   # 物件偵測
        res_disease = model_disease(image) # 影像分類
        
        diagnosis = "Healthy"
        top_confidence = 0.0
        
        # 🎯 智慧決策分流器：優先看昆蟲大腦有沒有「圈出框框」
        if len(res_insect[0].boxes) > 0 and float(res_insect[0].boxes[0].conf[0]) > 0.25:
            box = res_insect[0].boxes[0]
            class_id = int(box.cls[0])
            diagnosis = model_insect.names[class_id]
            top_confidence = float(box.conf[0])
            print(f"🐜 昆蟲偵測大腦勝出！圈出目標類別：{diagnosis} (信心度: {top_confidence:.2f})")
            
            # ✨ 將帶有綠色方框的推論圖片存下來，覆蓋原本翻正後的圖片
            res_insect[0].save(filename=file_location)
            
        else:
            # 如果畫面上沒有發現任何蟲子框框，轉交給植物病變分類大腦！
            if hasattr(res_disease[0], 'probs') and res_disease[0].probs is not None:
                top1_idx = int(res_disease[0].probs.top1)
                diagnosis = model_disease.names[top1_idx]
                top_confidence = float(res_disease[0].probs.top1conf)
                print(f"🍂 畫面上無昆蟲框框，轉交植物分類大腦！判定為：{diagnosis} (信心度: {top_confidence:.2f})")

        # 寫入 MySQL
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = "INSERT INTO farm_tasks_v2 (file_path, status, diagnosis_result, confidence) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (file_location, 'completed', diagnosis, top_confidence))
        conn.commit()
        cursor.close()
        conn.close()

        return {"status": "success", "diagnosis": diagnosis, "confidence": round(top_confidence, 2)}
    except Exception as e:
        return {"status": "error", "message": str(e)}