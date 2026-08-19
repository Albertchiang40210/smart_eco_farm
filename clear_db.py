import pymysql
import os
from dotenv import load_dotenv

# 載入環境變數 (在 Docker 內會自動讀取 docker-compose 傳入的變數)
load_dotenv()

try:
    # 這裡直接套用跟你網頁一模一樣的連線邏輯！
    conn = pymysql.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),  # 容器內會自動變成 'farm_db'
        port=3306,                               # 容器內直通都是 3306
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "P@ssw0rd"),
        database=os.getenv("DB_NAME", "smart_eco_farm_db"),
        charset="utf8mb4"
    )
    cursor = conn.cursor()
    
    # 執行清洗指令
    cursor.execute("TRUNCATE TABLE farm_tasks_v2;")
    conn.commit()
    
    print("\n✅【成功提示】(100% Docker 內執行) MySQL 資料庫已完美清洗抹平！\n")
    cursor.close()
    conn.close()

except Exception as e:
    print(f"\n❌ 清洗失敗，原因: {e}\n")