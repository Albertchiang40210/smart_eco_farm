# 1. 採用 Python 3.10 輕量基底
FROM python:3.10-slim

# 2. 設定工作目錄
WORKDIR /app

# 3. OpenCV / ONNX 執行所需的系統函式庫
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libxcb1 \
    libgl1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# 4. 複製套件清單並安裝
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 複製原始碼（模型權重由 ./result volume 掛載，不打包進映像）
COPY . .

# 6. 開放 FastAPI 的 8000 埠口
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --retries=5 CMD python -c "import urllib.request as u; u.urlopen('http://localhost:8000/api/v1/health')"

# 7. 啟動服務
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]