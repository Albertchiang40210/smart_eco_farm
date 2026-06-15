# 1. 採用 Python 3.10 輕量基底
FROM python:3.10-slim

# 2. 設定工作目錄
WORKDIR /app

# 3. 🟢 修正：換成最標準的 libgl1，100% 解決 slim 的 exit code 100 找不到套件問題
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libxcb1 \
    libgl1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# 4. 複製套件清單並安裝
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 複製所有原始碼與 YOLO 權重
COPY . .

# 6. 開放 FastAPI 的 8000 埠口
EXPOSE 8000

# 7. 啟動服務
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]