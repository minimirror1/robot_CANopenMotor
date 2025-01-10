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
    
    # 엔코더 카운트 -> 라디안 변환 계수
    COUNTS_PER_REV = 524288
    COUNTS_TO_RAD = 2 * np.pi / COUNTS_PER_REV
    RAD_TO_COUNTS = COUNTS_PER_REV / (2 * np.pi)
    
    # 어드미턴스 제어 파라미터 조정
    controller.admittance.M = 0.005  # 가상 질량 [kg⋅m²]
    controller.admittance.B = 0.1    # 댐핑 [N⋅m⋅s/rad]
    controller.admittance.K = 2.0   # 강성 [N⋅m/rad]
    
    dt = 0.01  # 제어 주기 [s]
    duration = 600.0  # 실행 시간 [s]
    
    try:
        # 동기 통신 시작
        controller.sync_start(dt)
        
        start_time = time.time()
        while time.time() - start_time < duration:

            # 토크 읽기 및 단위 변환 (mN.m -> N.m)
            external_force = controller.get_torque(motor.node_id) / 1000.0
            
            # 현재 위치와 속도 읽기 (엔코더 카운트)
            current_pos_counts = controller.get_position(motor.node_id)
            current_vel_counts = controller.get_velocity(motor.node_id)
            
            # 어드미턴스 제어 실행 (내부적으로 라디안 변환 처리)
            target_pos_counts = controller.admittance.compute(
                external_force, dt, current_pos_counts, current_vel_counts)
            
            # 목표 위치 설정
            controller.set_position(motor.node_id, target_pos_counts)
            
            # 현재 상태 출력 (라디안과 카운트 모두 표시)
            current_pos_rad = current_pos_counts * controller.admittance.COUNTS_TO_RAD
            print(f"Torque: {external_force:.3f} N.m, "
                  f"Position: {current_pos_rad:.3f} rad ({current_pos_counts} counts)")
            
            time.sleep(dt)
            
    except KeyboardInterrupt:
        print("\n사용자에 의해 중단됨")
    
    finally:
        # 정리
        controller.disconnect()
        print("프로그램 종료")

if __name__ == "__main__":
    run_admittance_control()
