from ultralytics import YOLO

def train_farm_brain():
    print("🧠 正在初始化 YOLOv8 影像分類模型...")
    # 載入預訓練的分類模型（yolov8m-cls.pt 代表中型分類模型，M5 Pro 跑這個輕輕鬆鬆）
    model = YOLO("yolov8m-cls.pt") 

    print("🔥 啟動 M5 Pro 硬體加速訓練流程...")
    
    # 開始訓練
    model.train(
        data="./sampled_dataset",  # 指向我們剛剛抽樣出來的黃金資料夾
        epochs=20,                 # 先跑 20 輪快速驗證模型效果
        imgsz=224,                 # 分類任務標準解析度 224x224
        batch=64,                  # 48GB 記憶體神機直接開到 64，速度飛快
        device="mps",              # ✨ 關鍵：強制呼叫 Apple Silicon GPU 加速
        workers=4                  # 使用 4 個 CPU 線程來搬運資料
    )
    
    print("\n🏆 訓練完成！這顆大腦的最佳權重檔已經儲存了！")
    print("📍 檔案路徑：runs/classify/train/weights/best.pt")

if __name__ == "__main__":
    train_farm_brain()