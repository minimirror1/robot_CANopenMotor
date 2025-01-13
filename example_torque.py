import canopen
import time
import math
from abstract_motor import AbstractMotor

from motor_factory import MotorFactory
from motor_controller import MotorController


import random

# 1 84,303
# 2 78,500
# 3 69,238
# 4 81,038

def get_wave_data(current_time):
    # frequency: Hz (주파수)
    # amplitude: 진폭
    # offset: 오프셋
    frequency = 0.1  # 60Hz
    amplitude = 50000
    offset = 0
    
    # 실시간으로 사인파 계산
    # 2π * frequency * time => 각속도 * 시간
    current_value = amplitude * math.sin(2 * math.pi * frequency * current_time) + offset
    return int(current_value)
    
    
    
def is_position_reached(current_pos, target_pos, tolerance=10):
    return abs(current_pos - target_pos) <= tolerance

def main():
    # 예시: CAN Bus controller 생성
    controller = MotorController(channel='can0', bustype='socketcan', bitrate=1000000)

    # 예시: 모터 생성(제조사별)
    motorA = MotorFactory.create_motor("VendorZeroErr", 1, "config/ZeroErr Driver_V1.5.eds", zero_offset=84303, operation_mode='PROFILE_TORQUE')
    #motorB = MotorFactory.create_motor("VendorZeroErr", 2, "config/ZeroErr Driver_V1.5.eds", zero_offset=78500, operation_mode='PROFILE_POSITION')
    #motorC = MotorFactory.create_motor("VendorZeroErr", 3, "config/ZeroErr Driver_V1.5.eds", zero_offset=69238, operation_mode='PROFILE_POSITION')
    #motorD = MotorFactory.create_motor("VendorZeroErr", 4, "config/ZeroErr Driver_V1.5.eds", zero_offset=81038)

    """motorA = MotorFactory.create_motor("VendorZeroErr", 1, "config/ZeroErr Driver_V1.5.eds", zero_offset=0)
    motorB = MotorFactory.create_motor("VendorZeroErr", 2, "config/ZeroErr Driver_V1.5.eds", zero_offset=0)
    motorC = MotorFactory.create_motor("VendorZeroErr", 3, "config/ZeroErr Driver_V1.5.eds", zero_offset=0)
    motorD = MotorFactory.create_motor("VendorZeroErr", 4, "config/ZeroErr Driver_V1.5.eds", zero_offset=0)"""
    #motorB = MotorFactory.create_motor("VendorB", 2, "vendorB.eds")

    # 컨트롤러에 모터 등록
    controller.add_motor(motorA)
    #controller.add_motor(motorB)
    #controller.add_motor(motorC)
    #controller.add_motor(motorD)
    #time.sleep(3) 
    
    # 리셋
    controller.reset_all()    
    
    # 모터 전체 초기화
    controller.init_all()    
    
    # PDO 매핑
    controller.pdo_mapping_all()

    # Switch On
    controller.set_switchOn_all()

    # PDO 콜백 등록
    controller.pdo_callback_register_all()
   
    # 동기화 시작
    controller.sync_start(0.01)
    
    # 위치 설정    
    # controller.set_position_all(0)

    # time.sleep(5)

    # controller.set_torque(1, 500)
    controller.set_torque(1, 250)
    cnt = 0
    try:
        while True:
            time.sleep(0.01)
            
            if cnt % 100 == 0:
                print(f"Torque: {controller.get_torque(1)}")
                print(f"Velocity: {controller.get_velocity(1)}")
                print(f"Acceleration: {controller.get_acceleration(1)}")
            cnt += 1
    except KeyboardInterrupt:
        controller.set_torque(1, 0)
        print("\n프로그램을 종료합니다...")
    
    # 종료 전 네트워크 해제
    controller.disconnect()

if __name__ == "__main__":
    main()


    
