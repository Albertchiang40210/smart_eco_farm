import os
import time
from datetime import datetime, timedelta
from database import engine
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

def run_cleanup(days_to_keep=30):
    """清理超過 n 天的資料庫紀錄與圖片檔案"""
    print(f"🧹 [清理排程啟動] 準備清理超過 {days_to_keep} 天的資料...")
    cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
    cutoff_str = cutoff_date.strftime("%Y-%m-%d %H:%M:%S")
    
    # 1. 刪除資料庫舊紀錄
    try:
        with engine.begin() as conn:
            # 清理 sensor_logs
            res_sensor = conn.execute(text("DELETE FROM sensor_logs WHERE created_at < :cutoff"), {"cutoff": cutoff_str})
            print(f"✅ 清理 sensor_logs: 刪除了 {res_sensor.rowcount} 筆紀錄。")
            
            # 清理 system_audit_logs
            res_audit = conn.execute(text("DELETE FROM system_audit_logs WHERE created_at < :cutoff"), {"cutoff": cutoff_str})
            print(f"✅ 清理 system_audit_logs: 刪除了 {res_audit.rowcount} 筆紀錄。")
            
            # 清理 farm_tasks_v2
            # 注意：如果需要先抓出檔名來刪除實體檔案，應該先 SELECT
            old_tasks = conn.execute(text("SELECT file_path FROM farm_tasks_v2 WHERE created_at < :cutoff"), {"cutoff": cutoff_str}).fetchall()
            
            # 實際刪除資料庫紀錄
            res_task = conn.execute(text("DELETE FROM farm_tasks_v2 WHERE created_at < :cutoff"), {"cutoff": cutoff_str})
            print(f"✅ 清理 farm_tasks_v2: 刪除了 {res_task.rowcount} 筆紀錄。")
            
            # 2. 刪除實體圖片檔案
            files_deleted = 0
            for row in old_tasks:
                file_path = row[0]
                if file_path and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        files_deleted += 1
                    except Exception as e:
                        print(f"⚠️ 無法刪除檔案 {file_path}: {e}")
            print(f"✅ 清理實體圖片: 成功刪除 {files_deleted} 個舊照片。")
            
    except Exception as e:
        print(f"❌ 清理過程發生錯誤：{e}")

if __name__ == "__main__":
    run_cleanup(30)
