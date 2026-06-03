import pymysql

try:
    # 建立與你網頁完全相同的實體連線
    conn = pymysql.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password="P@ssw0rd",
        database="smart_eco_farm_db",
        charset="utf8mb4"
    )
    cursor = conn.cursor()
    
    # 徹底摧毀並抹平整個表格，連 ID 計數器都會歸零
    cursor.execute("TRUNCATE TABLE farm_tasks_v2;")
    conn.commit()
    
    print("\n🎯 【成功提示】實體 MySQL 資料庫已完美清洗抹平！舊資料徹底清除、計數器已歸零！\n")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"\n❌ 清洗失敗，原因: {e}\n")