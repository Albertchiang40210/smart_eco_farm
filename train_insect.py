from ultralytics import YOLO

def train_insect_eye():
    print("🐛 正在初始化 YOLOv8 物件偵測模型...")
    # 載入預訓練的偵測模型（yolov8s.pt 代表 Small 模型，對小昆蟲靈敏且速度極快）
    model = YOLO("yolov8s.pt") 

    print("🔥 啟動 M5 Pro GPU 加速，開始訓練 12 類昆蟲偵測...")
    
    # 開始訓練物件偵測
    model.train(
        data="./data.yaml",     # 👈 指向你剛剛改好的 12 類地圖指南
        epochs=30,              # 物件偵測任務較複雜，我們先跑 30 輪
        imgsz=416,              # 💡 終極優化：鎖定 416 解析度，比 640 快將近 2.4 倍！
        batch=32,               # 讓 M5 Pro 48GB 記憶體穩穩跑的黃金批次量
        device="mps",           # 召喚 Apple Silicon GPU 的狂暴算力
        workers=4               # 使用 4 個 CPU 線程來全速搬運照片
    )
    
    print("\n🏆 12 類昆蟲偵測大腦訓練完成！")
    print("📍 最佳權重檔路徑：runs/detect/train/weights/best.pt")

if __name__ == "__main__":
    train_insect_eye()