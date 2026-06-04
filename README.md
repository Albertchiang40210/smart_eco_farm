# 🌾 AI-Powered Smart Eco-Farm & Environmental Monitoring System

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![YOLOv8](https://img.shields.io/badge/AI-YOLOv8%20%2F%20Computer%20Vision-green)](https://github.com/ultralytics/ultralytics)
[![MySQL](https://img.shields.io/badge/Database-MySQL-orange)](https://www.mysql.com/)

這是一個結合了 **電腦視覺（Computer Vision）與關聯式資料庫（MySQL）** 的 **智慧農業 / 生態農場自動化管理系統**。系統旨在解決傳統農業高度依賴人工巡檢、環境數據無法留存的痛點。透過 AI 進行作物健康度/病蟲害追蹤，並將即時環境數據與辨識日誌寫入 MySQL 資料庫，打造數據驅動的現代化新農業解決方案。

---

## 🚀 核心技術亮點 (Key Features)

- **農作物與病蟲害物件偵測 (Agri-CV Core):** 利用 YOLOv8 進行客製化目標偵測，能即時辨識不同作物的成熟度（如：未成熟、可採收），並精準捕捉早期病蟲害特徵。
- **時序數據與資料庫工程 (Database Engineering):** 獨立設計關聯式資料庫（MySQL），包含 `環境日誌表 (Sensor Logs)`、`AI 辨識警報表 (AI Detection Alerts)`。確保高頻率數據寫入時的穩定性。
- **異常事件觸發機制 (Event-Driven Alerts):** 當 AI 偵測到有害生物或環境數據（如溫度、濕度）超越安全門檻時，資料庫會自動觸發狀態更新，作為後端即時推播（如 Line Bot/Email 警報）的數據中樞。

---

## 📐 系統架構圖 (System Architecture)
[ 農場實體攝影機 ] ──────> [ YOLOv8 病蟲害 / 成熟度偵測 ] ──┐
▼
[ 環境感測器 (溫濕度) ] ──> [ 數據流處理 (Python Core) ] ───> [ MySQL 中央資料庫 ]
│
▼
[ 歷史數據分析 / 採收預警 ]

---

## 📂 專案目錄結構 (Project Structure)

SMART_ECO_FARM/
├── .env                  # 資料庫連線金鑰與密碼管理
├── data.yaml             # YOLO 訓練集配置 (病蟲害種類、作物類別)
├── train.py              # 農場專用 AI 模型訓練與超參數調校腳本
├── test_predict.py       # 本地端即時影像/串流辨識腳本
├── db_manager.py         # MySQL 資料庫模組 (處理 Sensor 資料寫入與歷史紀錄查詢)
├── sensor_simulator.py   # 模擬農場 IoT 感測器 (土壤溫度、濕度、光照) 數據生成腳本
├── result/               # 儲存最佳訓練權重 `best.pt` 與分析圖表
└── data/                 # 農場影像資料集 (作物、葉片病變、昆蟲標籤)

🐛 支援辨識與監控項目 (Monitoring Classes)
本系統目前針對以下農業核心指標進行監控：
	1.	作物成熟度分級: Unripe (未成熟) | Ripe (可採收)
	2.	植物病理與蟲害偵測: Leaf_Rust (葉鏽病) | Powdery_Mildew (白粉病) | Pests (害蟲/如蚜蟲、紅蜘蛛)
	3.	IoT 環境指標: 土壤水分 (Soil Moisture) | 空氣溫濕度 (Ambient Temp/Humidity) | 光照強度 (Lux)
🛠️ 快速開始 (Getting Started)
1. 環境安裝
pip install ultralytics pymysql pandas opencv-python

2. 資料庫初始化
請在 MySQL 中建立 smart_farm 資料庫，並執行對應的 SQL 語法建立 sensor_logs 與 ai_alerts 資料表。接著於 .env 配置連線：
DB_HOST=localhost
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=smart_farm

3. 啟動模擬環境與辨識
# 執行環境感測數據定時寫入 MySQL
python sensor_simulator.py

# 執行即時影像病蟲害偵測
python test_predict.py

📈 未來優化方向 (Future Roadmap)
	1.	多感測器時間序列預報: 引入機器學習迴歸模型（如 XGBoost），利用 MySQL 內的歷史溫濕度日誌，預測未來 3 天的土壤乾燥趨勢，達到自動化精準灌溉。
	2.	邊緣設備部署 (Edge AI): 將 YOLOv8 模型量化並部署至樹莓派 (Raspberry Pi) 或 Jetson Nano，實現真正的溫室在地端離線辨識。
