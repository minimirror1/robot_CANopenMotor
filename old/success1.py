import canopen
import time
import keyboard

# CANopen 네트워크 초기화
network = canopen.Network()
network.connect(bustype='socketcan', channel='can0')

# 노드 추가 (노드 ID 1로 가정)
node_id = 4
node = network.add_node(node_id, 'config/ZeroErr Driver_V1.5.eds')


node.sdo[0x6040].raw = 0x27

node.sdo[0x6040].raw = 0x26

network.nmt.send_command(0x02)  # Stop
time.sleep(0.5)
network.nmt.send_command(0x82)  # Reset
time.sleep(1)  # 재설정 후 충분한 대기 시간

# -------------------------------------------------------------
# 1) 오류가 있으면 먼저 해제(또는 모터 정지 상태 만들기)
#    사진 상에서: "电机清除报警 (0x6040 set to 128)"
try:
    node.sdo[0x6040].raw = 0x80  # 128(0x80) -> Fault Reset
    time.sleep(0.1)
except Exception as e:
    print("Error clearing fault:", e)

# -------------------------------------------------------------
# 2) 프로파일 위치 모드(PP) 설정
#    사진 상에서: "0x6060 设置为1" (Profile Position mode = 1)
try:
    node.sdo[0x6060].raw = 1
    time.sleep(0.1)
    
    # 제대로 세팅되었는지 확인 (사진의 "核对运行模式"에 해당)
    current_mode = node.sdo[0x6061].raw  # 0x6061: Modes of Operation Display
    print(f"Current Operation Mode: {current_mode}")
except Exception as e:
    print("Error setting PP mode:", e)



# -------------------------------------------------------------
# 3) 속도/가속도/감속도 설정
#    사진 상에서: 
#     - "0x6081 = 5566" (Profile Velocity)
#     - "0x6083 = 5566" (Profile Acceleration)
#     - "0x6084 = 5566" (Profile Deceleration)
try:
    node.sdo[0x6081].raw = 262143  # Profile Velocity
    time.sleep(0.1)
    
    node.sdo[0x6083].raw = 262143  # Profile Acceleration
    time.sleep(0.1)
    
    node.sdo[0x6084].raw = 262143  # Profile Deceleration
    time.sleep(0.1)
except Exception as e:
    print("Error setting velocity/acc/dec:", e)

# -------------------------------------------------------------
# 4) 모터를 Enable 시키기 위한 Controlword 조작
#    사진에서 "电机使能" (Enable motor) 시퀀스
#    (Bit5=0 / Bit5=1 등 여러 가지 시퀀스가 있으나 여기서는 일반적인 6->7->15 시퀀스 예시)
try:
    node.sdo[0x6040].raw = 128
    time.sleep(0.1)

    # 0x6040 = 6 (Shutdown -> Switch on)
    node.sdo[0x6040].raw = 38
    time.sleep(0.1)
    
    # 0x6040 = 7 (Switch on -> Enable)
    node.sdo[0x6040].raw = 39
    time.sleep(0.1)
    
    # 0x6040 = 15 (Enable Operation)
    node.sdo[0x6040].raw = 47
    time.sleep(0.5)
    
    # (Bit5=0일 때는 실제 구동 명령이 별도 Controlword로 실행되는 케이스 등 다양)
except Exception as e:
    print("Error enabling motor:", e)


error_code = node.sdo[0x603f].raw
print(f'error_code: {error_code}')

"""for i in range(10):
    # 0x6040 = 7 (Switch on -> Enable)
    node.sdo[0x6040].raw = 39
    time.sleep(1)
    # 0x6040 = 15 (Enable Operation)
    node.sdo[0x6040].raw = 47
    time.sleep(1)"""

"""print(f"Release Brake {node.sdo[0x4602].raw}")
print(f"status word {node.sdo[0x6041].raw}")
print(f"Controlword {node.sdo[0x6040].raw}")
time.sleep(3)

node.sdo[0x4602].raw = 0x0000
time.sleep(1)

node.sdo[0x4602].raw = 0x0001
time.sleep(1)

print(f"Release Brake {node.sdo[0x4602].raw}")
print(f"status word {node.sdo[0x6041].raw}")
print(f"Controlword {node.sdo[0x6040].raw}")
time.sleep(3)"""

"""
for i in range(10):
    node.sdo[0x4602].raw = 0x0000
    time.sleep(0.5)
    node.sdo[0x4602].raw = 0x0001
    time.sleep(0.5)
node.sdo[0x4602].raw = 0x0001
time.sleep(0.5)
"""

# -------------------------------------------------------------
# 5) 목표 위치(Target Position) 설정
#    사진에서 예: "目标位置设置为55660 plus"
#    (임의로 55660을 예시값으로 사용)
try:
    TARGET_POSITION = 262144
    node.sdo[0x607A].raw = TARGET_POSITION  # Set Target Position
    time.sleep(0.1)
except Exception as e:
    print("Error setting target position:", e)

# -------------------------------------------------------------
# 6) 명령 실행(모터 동작)
#    사진에서: "0x6040 = 31" (일반적으로 0x1F, 즉 31을 쓰면 New set-point + Enable 움직임)
try:
    node.sdo[0x6040].raw = 63  # 31 (Operation start for PP mode)
    time.sleep(0.1)
except Exception as e:
    print("Error starting operation:", e)

# -------------------------------------------------------------
# 모터 동작 모니터링 (간단 예)
try:
    print("Moving to target position...")
    while True:
        
        position_actual = node.sdo[0x6064].raw  # Actual Position
        print(f"Actual Position = {position_actual}")
        
        # 목표 위치 근처면 탈출 (단순 예시)
        if abs(position_actual - TARGET_POSITION) < 10:
            print("Reached target position!")
            if TARGET_POSITION == 0:
                TARGET_POSITION = 262144
                # 0x6040 = 7 (Switch on -> Enable)
                node.sdo[0x6040].raw = 39
                time.sleep(1)
                
                # 0x6040 = 15 (Enable Operation)
                node.sdo[0x6040].raw = 47
                time.sleep(1)
            else:
                TARGET_POSITION = 0
            node.sdo[0x6040].raw = 47
            time.sleep(0.5)
            node.sdo[0x607A].raw = TARGET_POSITION
            node.sdo[0x6040].raw = 63  # 31 (Operation start for PP mode)
            time.sleep(0.1)
            
        
        time.sleep(0.2)
        
        # 키보드로 ESC를 누르면 긴급 중단

except KeyboardInterrupt:
    print("Emergency stop triggered by user!")
    # 0x6040 = 0x02 로 quick stop 등
    node.sdo[0x6040].raw = 0x02
    network.disconnect()
        
except Exception as e:
    print("Error during motion:", e)

# -------------------------------------------------------------
# 마무리
# -------------------------------------------------------------
print("Done.")
