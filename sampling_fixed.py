import os
import shutil
import random

# ==================== sampling_fixed.py 的路徑設定 ====================
SRC_TRAIN = "./raw_dataset/archive/train"  
SRC_VALID = "./raw_dataset/archive/valid"

# 抽樣後的目標輸出，會自動在你的專案底下建立
TRAIN_TARGET_DIR = "./sampled_dataset/train"
VALID_TARGET_DIR = "./sampled_dataset/valid"

TOTAL_TRAIN_GOAL = 10000
TOTAL_VALID_GOAL = 2500
# =====================================================================

def process_sampling(src_dir, target_dir, total_goal):
    if not os.path.exists(src_dir):
        print(f"❌ 找不到來源資料夾：{src_dir}，請檢查 raw_dataset 裡面是不是真的有 archive 資料夾！")
        return
    
    # 取得子資料夾清單
    categories = [c for c in os.listdir(src_dir) if os.path.isdir(os.path.join(src_dir, c)) and not c.startswith('.')]
    
    if len(categories) == 0:
        print(f"❌ 在 {src_dir} 內找不到任何分類資料夾！")
        return
        
    images_per_category = total_goal // len(categories)
    total_copied = 0

    print(f"📊 偵測到 {len(categories)} 個分類，平均每個類別抽取大約 {images_per_category} 張照片。")

    for category in categories:
        source_category_path = os.path.join(src_dir, category)
        all_images = [img for img in os.listdir(source_category_path) if img.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        # 決定抽樣張數
        current_sample_count = min(images_per_category, len(all_images))
        sampled_images = random.sample(all_images, current_sample_count)
        
        dest_category_path = os.path.join(target_dir, category)
        os.makedirs(dest_category_path, exist_ok=True)
        
        # 複製照片
        for img_name in sampled_images:
            shutil.copy(os.path.join(source_category_path, img_name), os.path.join(dest_category_path, img_name))
            
        total_copied += current_sample_count
        print(f" └─ {category}: 成功抽選 {current_sample_count} 張")
    
    print(f"✅ 成功精選出共 {total_copied} 張照片至 {target_dir}")

if __name__ == "__main__":
    print("🚀 開始執行智慧農場資料集精簡計畫...")
    print("1. 正在處理 Train 訓練集...")
    process_sampling(SRC_TRAIN, TRAIN_TARGET_DIR, TOTAL_TRAIN_GOAL)
    print("\n2. 正在處理 Valid 驗證集...")
    process_sampling(SRC_VALID, VALID_TARGET_DIR, TOTAL_VALID_GOAL)
    print("\n🎉 全部搞定！你的輕量化資料集已準備就緒。")