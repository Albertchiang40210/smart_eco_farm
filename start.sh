#!/bin/bash

# ==============================================================================
# 🌿 智慧生態農場 AIoT 營運中台：一鍵自動化部署與行程生命週期管理腳本 (DevOps)
# ==============================================================================

# 定義文字顏色輸出格式
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 [DevOps 營運通報] 智慧生態農場自動化部署鏈路開始導通...${NC}"

# 1. 自動激活本地相容性隔離虛擬環境 (.venv)
if [ -d ".venv" ]; then
    echo -e "📦 偵測到本地隔離環境，正在激活專案虛擬環境..."
    source .venv/bin/activate
else
    echo -e "${RED}❌ 錯誤：找不到 .venv 虛擬環境目錄，請先執行 python -m venv .venv 進行環境建置。${NC}"
    exit 1
fi

# 2. 定義行程清理機制 (根除邊緣端記憶體溢出與殭屍程序痛點)
cleanup() {
    echo -e "\n${RED}⚠️ [DevOps 警報] 偵測到關閉訊號 (SIGINT/SIGTERM)，啟動行程熔斷清理機制...${NC}"
    
    # 尋找並獵殺此專案引發的背景 ngrok 反向代理行程
    if [ ! -z "$NGROK_PID" ]; then
        echo -e "🧹 正在終止反向代理通道安全 ngrok (PID: $NGROK_PID)..."
        kill -9 $NGROK_PID 2>/dev/null
    fi
    
    # 獵殺可能殘留的 Streamlit 行程
    echo -e "🧹 正在清理 Streamlit 網頁前台殘留行程..."
    pkill -f "streamlit run farm_app.py" 2>/dev/null
    
    echo -e "${GREEN}🟢 [清理完畢] 所有邊緣背景程序已同生共死，硬體記憶體完全釋放。交班封存完畢。${NC}"
    exit 0
}

# 🛠️ 核心精髓：導入 Linux trap 監聽器，一有風吹草動立刻啟動同生共死機制
trap cleanup SIGINT SIGTERM

# 3. 異步背景掛載反向代理通道 (ngrok)
echo -e "${YELLOW}🌐 正在建立公網安全隧道反向代理 (ngrok)...${NC}"
# 讀取當前工作區下的 ngrok 配置並於背景異步掛載
ngrok http 8501 --log=stdout > /dev/null &
NGROK_PID=$!
echo -e "🟢 反向代理成功掛載於背景，分流 PID: ${GREEN}$NGROK_PID${NC}"

# 預留緩衝時間確保隧道穿透成功
sleep 2

# 4. 正式啟動智慧農場監控看板前台 (Streamlit)
echo -e "${GREEN}🖥️ 正在驅動溫室 Kiosk 實時分析大腦前台 (Streamlit)...${NC}"
echo -e "${YELLOW}💡 提示：若要關閉整套系統，請直接在終端機按下 [Ctrl + C]，系統將自動啟動安全清理。${NC}"
echo "----------------------------------------------------------------------"

# 啟動 Streamlit 主行程 (不放在背景，用以作為前台的主阻塞監聽器)
streamlit run farm_app.py --server.port=8501 --server.address=0.0.0.0

#./start.sh 一鍵啟動

# 後台帳密：admin
          #farm2026