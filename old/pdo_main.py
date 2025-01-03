import canopen
import time
import keyboard

class CANopenMotorController:
    def __init__(self, node_id=4, channel='can0', eds_path='config/ZeroErr Driver_V1.5.eds'):
        self.node_id = node_id
        self.network = canopen.Network()
        self.network.connect(bustype='socketcan', channel=channel)
        self.node = self.network.add_node(node_id, eds_path)
        self.target_position = 0

    def initialize(self):
        """초기 설정 및 리셋"""
        self.node.sdo[0x6040].raw = 0x27
        self.node.sdo[0x6040].raw = 0x26
        self.network.nmt.send_command(0x02)  # Stop
        time.sleep(0.5)
        self.network.nmt.send_command(0x82)  # Reset
        time.sleep(1)

    def clear_fault(self):
        """오류 초기화"""
        try:
            self.node.sdo[0x6040].raw = 0x80
            time.sleep(0.1)
        except Exception as e:
            print("Error clearing fault:", e)

    def set_profile_position_mode(self):
        """PP 모드 설정"""
        try:
            self.node.sdo[0x6060].raw = 1
            time.sleep(0.1)
            current_mode = self.node.sdo[0x6061].raw
            print(f"Current Operation Mode: {current_mode}")
        except Exception as e:
            print("Error setting PP mode:", e)

    def set_motion_parameters(self, velocity=262143, acceleration=262143, deceleration=262143):
        """모션 파라미터 설정"""
        try:
            self.node.sdo[0x6081].raw = velocity
            self.node.sdo[0x6083].raw = acceleration
            self.node.sdo[0x6084].raw = deceleration
            time.sleep(0.1)
        except Exception as e:
            print("Error setting motion parameters:", e)

    def enable_motor(self):
        """모터 활성화"""
        try:
            self.node.sdo[0x6040].raw = 0x0080
            time.sleep(0.1)
            self.node.sdo[0x6040].raw = 0x0026
            time.sleep(0.1)
            self.node.sdo[0x6040].raw = 0x0027
            time.sleep(0.1)
            self.node.sdo[0x6040].raw = 0x002F
            time.sleep(0.1)
        except Exception as e:
            print("Error enabling motor:", e)

    def move_to_position(self, target_position):
        """지정된 위치로 이동"""
        try:
            self.node.sdo[0x607A].raw = target_position
            time.sleep(0.1)
            self.node.sdo[0x6040].raw = 0x003F
            time.sleep(0.1)
        except Exception as e:
            print("Error moving to position:", e)

    def monitor_position(self):
        """위치 모니터링"""
        try:
            while True:
                position_actual = self.node.sdo[0x6064].raw
                print(f"Actual Position = {position_actual}")

                if abs(position_actual - self.target_position) < 10:
                    print("Reached target position!")
                    self.target_position = 262144 if self.target_position == 0 else 0
                    self.enable_motor()
                    self.move_to_position(self.target_position)

                time.sleep(0.2)

        except KeyboardInterrupt:
            print("Emergency stop triggered by user!")
            self.emergency_stop()

    def emergency_stop(self):
        """긴급 정지"""
        self.node.sdo[0x6040].raw = 0x0002
        self.network.disconnect()

    def get_error_code(self):
        """에러 코드 확인"""
        return self.node.sdo[0x603f].raw

def main():
    # 컨트롤러 인스턴스 생성
    controller = CANopenMotorController()
    
    # 초기화 시퀀스
    controller.initialize()
    controller.clear_fault()
    controller.set_profile_position_mode()
    controller.set_motion_parameters()
    controller.enable_motor()
    
    # 에러 코드 확인
    error_code = controller.get_error_code()
    print(f'error_code: {error_code}')
    
    # 초기 위치 이동 및 모니터링
    controller.move_to_position(0)
    controller.monitor_position()


if __name__ == "__main__":
    main()
