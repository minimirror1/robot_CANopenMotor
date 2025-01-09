import time
import numpy as np
from motor_controller import MotorController
from motor_factory import MotorFactory

def run_admittance_control():
    # 모터 컨트롤러 초기화
    controller = MotorController(channel='can0', bustype='socketcan', bitrate=1000000)
    motor = MotorFactory.create_motor("VendorZeroErr", 1, "config/ZeroErr Driver_V1.5.eds", zero_offset=84303)
    controller.add_motor(motor)

    # 기본 설정
    controller.reset_all()
    controller.init_all()
    controller.pdo_mapping_all()
    controller.set_switchOn_all()
    controller.pdo_callback_register_all()
    
    controller.admittance.M = 0.1
    controller.admittance.B = 2   
    controller.admittance.K = 10.0
    
    # 어드미턴스 제어 파라미터
    mass = 0.1       # 가상 질량 [kg]
    damping = 2.0    # 댐핑 계수 [Ns/m]
    stiffness = 10.0 # 강성 계수 [N/m]
    
    dt = 0.01  # 제어 주기 [s]
    duration = 600.0  # 실행 시간 [s]
    
    try:
        # 동기 통신 시작
        controller.sync_start(dt)
        
        start_time = time.time()
        while time.time() - start_time < duration:
            # 가상의 외력 생성 (실제로는 센서에서 읽어와야 함)
            # t = time.time() - start_time
            # external_force = 100000.0 * np.sin(2 * np.pi * 0.5 * t)  # 10N 진폭, 0.5Hz 사인파
            
            external_force = controller.get_torque(motor.node_id) / 1000.0  # mN.m를 N.m로 변환
            print(f"Torque: {external_force:.3f} N.m")
            
            # 어드미턴스 제어 실행
            controller.update_admittance_control(motor.node_id, external_force, dt)
            
            time.sleep(dt)
            
    except KeyboardInterrupt:
        print("\n사용자에 의해 중단됨")
    
    finally:
        # 정리
        controller.disconnect()
        print("프로그램 종료")

if __name__ == "__main__":
    run_admittance_control()
