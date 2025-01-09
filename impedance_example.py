from motor_controller import MotorController
from motor_vendor.motorVendorZeroErr import MotorVendorZeroErr
import time
import math

def main():
    # 모터 컨트롤러 초기화
    controller = MotorController(channel='can0', bustype='socketcan', bitrate=1000000)
    
    try:
        # 모터 1번 등록 (node_id=1)
        motor1 = MotorVendorZeroErr(node_id=1, eds_path='path/to/eds/file.eds')
        controller.add_motor(motor1)
        
        # 모터 초기화 및 PDO 매핑
        controller.all_motors_init_start()
        time.sleep(1)  # 초기화 대기
        
        # 임피던스 제어 모드 활성화
        motor1.enable_impedance_mode()
        time.sleep(0.5)  # 모드 전환 대기
        
        # 임피던스 파라미터 설정
        # stiffness: 강성계수 (위치 오차에 대한 복원력)
        # damping: 감쇠계수 (속도에 대한 저항)
        motor1.set_impedance(stiffness=100.0, damping=10.0)
        
        print("Starting impedance control demo...")
        
        # 목표 위치를 사인파로 변경하면서 임피던스 제어 테스트
        start_time = time.time()
        try:
            while True:
                current_time = time.time() - start_time
                
                # 사인파 목표 궤적 생성 (진폭: 1000 counts, 주기: 4초)
                target_position = 1000 * math.sin(2 * math.pi * current_time / 4.0)
                motor1.set_position(int(target_position))
                
                # 현재 상태 출력
                current_pos = motor1.get_position()
                current_torque = motor1.get_torque()
                print(f"Time: {current_time:.2f}s, Target: {target_position:.0f}, "
                      f"Current: {current_pos}, Torque: {current_torque}")
                
                time.sleep(0.01)  # 10ms 주기로 제어
                
        except KeyboardInterrupt:
            print("\nStopping impedance control demo...")
    
    finally:
        # 정리
        print("Cleaning up...")
        controller.disconnect()

if __name__ == "__main__":
    main()
