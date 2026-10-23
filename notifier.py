import os

import requests
from loguru import logger

import settings

TIMEOUT = 10


def send_alert(message: str, image_path: str | None = None) -> bool:
    """透過 Telegram Bot 發送警報（Line Notify 已於 2025/3 終止服務）。未設定憑證時略過。"""
    token, chat_id = settings.TELEGRAM_BOT_TOKEN, settings.TELEGRAM_CHAT_ID
    if not token or not chat_id:
        logger.debug("未設定 TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID，略過警報推播")
        return False

    base = f"https://api.telegram.org/bot{token}"
    try:
        if image_path and os.path.exists(image_path):
            with open(image_path, "rb") as f:
                resp = requests.post(
                    f"{base}/sendPhoto",
                    data={"chat_id": chat_id, "caption": message},
                    files={"photo": f},
                    timeout=TIMEOUT,
                )
        else:
            resp = requests.post(
                f"{base}/sendMessage", data={"chat_id": chat_id, "text": message}, timeout=TIMEOUT
            )
        if resp.ok:
            logger.info("Telegram 警報發送成功")
            return True
        logger.error(f"Telegram 警報發送失敗：HTTP {resp.status_code}")
    except requests.RequestException as e:
        logger.error(f"Telegram 連線錯誤：{e}")
    return False
