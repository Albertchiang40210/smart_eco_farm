import os
import requests
from dotenv import load_dotenv

load_dotenv()

LINE_NOTIFY_TOKEN = os.getenv("LINE_NOTIFY_TOKEN", "")

def send_line_alert(message: str, image_path: str = None) -> bool:
    """發送 Line Notify 警報"""
    if not LINE_NOTIFY_TOKEN:
        print("⚠️ 未設定 LINE_NOTIFY_TOKEN，跳過通報。")
        return False
        
    url = "https://notify-api.line.me/api/notify"
    headers = {
        "Authorization": f"Bearer {LINE_NOTIFY_TOKEN}"
    }
    data = {
        "message": message
    }
    
    files = {}
    if image_path and os.path.exists(image_path):
        files = {"imageFile": open(image_path, "rb")}
        
    try:
        response = requests.post(url, headers=headers, data=data, files=files if files else None)
        if response.status_code == 200:
            print("✅ Line Notify 發送成功！")
            return True
        else:
            print(f"❌ Line Notify 發送失敗，狀態碼：{response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Line Notify 連線錯誤：{e}")
        return False
    finally:
        if files and "imageFile" in files:
            files["imageFile"].close()
