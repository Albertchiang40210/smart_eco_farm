import time
import requests
import random
import os
import config # 讀取你的設定檔
from dotenv import load_dotenv

load_dotenv()

# 你的 FastAPI 伺服器位址
API_URL = os.getenv("SENSOR_API_URL", "http://127.0.0.1:8000/api/v1/sensors")
HEADERS = {"X-API-Key": os.getenv("DEVICE_API_KEY", "")}

def collect_and_send():
    print(f"🌱 啟動生態農場 IoT 感測器節點... (發送頻率: 每 {config.CHECK_INTERVAL} 秒)")
    
    while True:
        # 1. 模擬硬體讀取 (加入 random 讓數據有些微跳動)
        # ⚠️ 這裡已經補上 device_id，不會再報錯了！
        payload = {
            "device_id": "Sensor_Zone_A",
            "temperature": round(random.uniform(25.0, 35.0), 1),
            "humidity": round(random.uniform(50.0, 80.0), 1),
            "soil_moisture": round(random.uniform(30.0, 60.0), 1)
        }
        
        # 2. 發送 HTTP POST 給 FastAPI 後端引擎
        try:
            response = requests.post(API_URL, json=payload, headers=HEADERS, timeout=5)
            if response.status_code == 401:
                print("🔒 [驗證失敗] 請在 .env 設定正確的 DEVICE_API_KEY")
            else:
                print(f"[發送成功] {payload['device_id']} -> {response.json().get('alert')}")
                
        except requests.exceptions.RequestException:
            print("🚨 [連線失敗] 找不到 FastAPI 伺服器，請確認大腦已開機！")
            
        # 3. 休息指定的時間 (只會暫停這個腳本，不影響 FastAPI)
        time.sleep(config.CHECK_INTERVAL)

if __name__ == "__main__":
    collect_and_send()