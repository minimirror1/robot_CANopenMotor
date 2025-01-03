import canopen
import time
import keyboard
# CANopen 네트워크 초기화
network = canopen.Network()
# network.connect(channel='can0', bustype='socketcan')  # CAN 인터페이스에 맞게 설정
network.connect(bustype='socketcan', channel='can0')

# 노드 추가 (노드 ID 1로 가정)
node_id = 4
node = network.add_node(node_id, 'config/ZeroErr Driver_V1.5.eds')  # EDS 파일 경로 설정 필요



node.sdo[0x6040].raw = 0x27

node.sdo[0x6040].raw = 0x26

network.nmt.send_command(0x02)  # Stop
time.sleep(0.5)
network.nmt.send_command(0x82)  # Reset
time.sleep(1)  # 재설정 후 충분한 대기 시간


try:
    node.sdo[0x6040].raw = 0x80  # 128(0x80) -> Fault Reset
    time.sleep(0.1)
except Exception as e:
    print("Error clearing fault:", e)
    
# 네트워크 준비
"""node.nmt.state = 'PRE-OPERATIONAL'
time.sleep(1)
node.nmt.state = 'OPERATIONAL'
time.sleep(1)"""

"""try:
    node.network.nmt.send_command(0x01)  # NMT 시작 명령 전송
except canopen.SdoCommunicationError as e:
    time.sleep(0.3)"""

# 모드 설정 (CSP 모드)
#node.sdo['Modes of operation'].raw = 0x04  # 0x08 = CSP 모드
node.sdo['Modes of operation'].raw = 0x01  # 0x01 = PP 모드
time.sleep(0.1)


# Profile velocity
node.sdo['Profile velocity'].raw = 262143
print(f'[write] Profile velocity: 262144')

# Profile acceleration
node.sdo['Profile acceleration'].raw = 262143
print(f'[write] Profile acceleration: 262144')

# Profile deceleration
node.sdo['Profile deceleration'].raw = 262143
print(f'[write] Profile deceleration: 262144')


# 제어 워드 설정 (모터 준비)
node.sdo['Controlword'].raw = 0x0080
time.sleep(0.1)

node.sdo['Controlword'].raw = 0x0026
time.sleep(0.2)
node.sdo['Controlword'].raw = 0x0027
time.sleep(0.2)
node.sdo['Controlword'].raw = 0x002F  # 위치 제어 활성화
time.sleep(0.2)
# node.sdo['Controlword'].raw = 0x003F  # 위치 제어 활성화
# time.sleep(0.2)

#node.sdo['Target torque'].raw = 0

# # 목표 위치 설정
target_position = 0  # 원하는 위치 값
node.sdo['Target Position'].raw = target_position
time.sleep(0.2)

node.sdo['Controlword'].raw = 0x003F  # 새 위치 명령 실행
time.sleep(0.2)
print('check Controlword: ', node.sdo['Controlword'].raw)





# 모터가 목표 위치에 도달할 때까지 대기
try:
    while True:
        print(f"Current Position: {node.sdo['Position actual value'].raw}")
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nCtrl+C가 감지되었습니다. 프로그램을 종료합니다.")
finally:
    # 안전한 종료를 위한 정리 작업
    node.sdo['Target torque'].raw = 0
    network.disconnect()
    print("프로그램이 안전하게 종료되었습니다.")