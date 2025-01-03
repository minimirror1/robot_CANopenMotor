import canopen
import time

# CANopen 네트워크 생성 및 연결
network = canopen.Network()
network.connect(channel='can0', bustype='socketcan', bitrate=1000000)

# 노드 추가
node = network.add_node(1, "config/ZeroErr Driver_V1.5.eds")

# RPDO1 설정
node.rpdo.read()
node.rpdo[1].clear()
node.rpdo[1].add_variable('Controlword')
node.rpdo[1].add_variable('Target Position')
node.rpdo[1].trans_type = 1  # SYNC 기반 동작 설정
node.rpdo[1].enabled = True
node.rpdo.save()

# SYNC 신호 설정 및 브로드캐스트
network.sync.start(5)

# RPDO1 데이터 송신
node.rpdo[1]['Controlword'].phys = 0x2F
node.rpdo[1]['Target Position'].phys = 10000
node.rpdo[1].transmit()

print("RPDO1 data sent. SYNC signals will apply the data.")

for i in range(10):
    time.sleep(1)