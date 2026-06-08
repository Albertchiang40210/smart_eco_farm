import subprocess
import time
import os
import sys

print("🚀 [智慧農場] 正在啟動全自動點火程序，請稍候...")

# 💡 自動偵測並使用你專案內的 .venv 虛擬環境 Python，避免套件路徑錯亂
if os.path.exists(".venv/bin/python"):
    python_exe = ".venv/bin/python"
    streamlit_exe = ".venv/bin/streamlit"
else:
    python_exe = sys.executable
    streamlit_exe = "streamlit"

processes = []

try:
    # 🧠 1. 啟動 FastAPI 雙核心大腦
    print("🧠 [1/3] 正在發動 FastAPI 後端伺服器 (Port 8000)...")
    fastapi_proc = subprocess.Popen([python_exe, "-m", "uvicorn", "main:app", "--reload", "--port", "8000"])
    processes.append(fastapi_proc)

    # ⏳ 給大腦一點載入 YOLOv8 模型權重的緩衝時間
    time.sleep(3)

    # 📺 2. 啟動 Streamlit 戰情大螢幕
    print("📺 [2/3] 正在點亮 Streamlit 戰情大螢幕...")
    streamlit_proc = subprocess.Popen([streamlit_exe, "run", "farm_app.py"])
    processes.append(streamlit_proc)

    # 📡 3. 啟動 Ngrok 外網穿透隧道
    print("📡 [3/3] 正在打通 Ngrok 遠端數據隧道...")
    ngrok_proc = subprocess.Popen(["ngrok", "http", "8000"])
    processes.append(ngrok_proc)

    print("\n🎉 【全線通車】智慧溫室戰情系統已全部就位！")
    print("👉 手機端請掃描大螢幕的 QR Code 連線，戰情室請觀看 Streamlit 網頁。")
    print("🛑 想要結束展示時，請在目前視窗按下 [Ctrl + C] 即可一次安全關閉所有服務。\n")

    # 讓主程式保持存活監聽
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("\n🛑 [安全機制] 偵測到中斷訊號，正在強制回收所有邊緣運算資源...")
    for proc in processes:
        proc.terminate()
        proc.wait()
    print("✅ 所有後台進程已全數安全返航！👋")

#python run_all.py