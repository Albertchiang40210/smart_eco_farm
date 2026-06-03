import time

class GreenhouseActuatorController:
    """
    工業級溫室執行器控制中樞 (PLC 抽象層)
    封裝散熱風扇與變頻水泵的實體控制邏輯，並內建硬體冷卻防護機制（防短時間內連續開關燒毀馬達）。
    """
    def __init__(self):
        # 紀錄執行器當前狀態
        self.fan_status = "OFF"
        self.pump_status = "OFF"
        
        # 內建工業級防抖動冷卻時間 (Cooldown, 單位：秒)
        # 防止微氣候在臨界值微幅震盪時，導致執行器頻繁開關
        self.COOLDOWN_TIME = 5  
        self.last_fan_toggle_time = 0
        self.last_pump_toggle_time = 0

    def set_fan(self, command: str) -> bool:
        """
        控制溫室大棚強力散熱風扇
        :param command: "ON" 或 "OFF"
        :return: bool 是否成功切換狀態
        """
        current_time = time.time()
        command = command.upper()
        
        if command == self.fan_status:
            return False  # 狀態相同，無需重複驅動
            
        # 安全機制：檢查是否過了冷卻時間
        if current_time - self.last_fan_toggle_time < self.COOLDOWN_TIME:
            print(f"⚠️ [PLC 防護熔斷] 風扇切換過於頻繁，冷卻保護中... 剩餘 {round(self.COOLDOWN_TIME - (current_time - self.last_fan_toggle_time), 1)} 秒")
            return False

        # 模擬發送 PLC 暫存器指令或 MQTT 訊號給現地硬體
        self.fan_status = command
        self.last_fan_toggle_time = current_time
        print(f"⚙️ [🚀 執行器實時硬體驅動] MQTT 傳輸成功 ➔ 溫室排風扇已強制變更為: {self.fan_status}")
        return True

    def set_pump(self, command: str) -> bool:
        """
        控制工業級精準變頻灌溉水泵
        :param command: "ON" 或 "OFF"
        """
        current_time = time.time()
        command = command.upper()
        
        if command == self.pump_status:
            return False
            
        if current_time - self.last_pump_toggle_time < self.COOLDOWN_TIME:
            print(f"⚠️ [PLC 防護熔斷] 水泵切換過於頻繁，冷卻保護中...")
            return False

        self.pump_status = command
        self.last_pump_toggle_time = current_time
        print(f"⚙️ [🚀 執行器實時硬體驅動] MQTT 傳輸成功 ➔ 變頻灌溉水泵已強制變更為: {self.pump_status}")
        return True

# 建立全域單例控制器，供主程式動態調用
actuator_controller = GreenhouseActuatorController()