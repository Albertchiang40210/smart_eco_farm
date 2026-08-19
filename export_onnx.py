from ultralytics import YOLO
import os

def export_models():
    print("🚀 開始將 YOLO 模型匯出為 ONNX 格式以加速推論...")
    
    path_insect = "result/train/weights/best.pt"
    if os.path.exists(path_insect):
        print(f"📦 匯出昆蟲模型：{path_insect}")
        model_insect = YOLO(path_insect)
        model_insect.export(format="onnx")
        print("✅ 昆蟲模型 ONNX 匯出成功！")
    else:
        print(f"⚠️ 找不到昆蟲權重 {path_insect}，跳過匯出。")

    path_disease = "result/runs/classify/train/weights/best.pt"
    if os.path.exists(path_disease):
        print(f"📦 匯出植物病變模型：{path_disease}")
        model_disease = YOLO(path_disease)
        model_disease.export(format="onnx")
        print("✅ 植物病變模型 ONNX 匯出成功！")
    else:
        print(f"⚠️ 找不到植物病變權重 {path_disease}，跳過匯出。")
        
if __name__ == "__main__":
    export_models()
