import time
import canopen

def get_pdo_identifier(node_id, enable):
    """
    노드 아이디와 활성/비활성 상태를 입력받아 CAN Identifier를 반환하는 함수.
    
    Parameters:
        node_id (int): 노드 아이디 (1~127 범위)
        enable (bool): True이면 PDO 활성화, False이면 비활성화
    
    Returns:
        int: 계산된 PDO CAN Identifier (32비트 정수)
    """
    if not (1 <= node_id <= 127):
        raise ValueError("노드 아이디는 1~127 사이여야 합니다.")
    
    # 기본 COB-ID 계산 (TxPDO1은 0x180 + NodeID)
    cob_id = 0x180 + node_id
    
    # 활성 상태에 따라 Bit 31 설정
    if not enable:
        cob_id |= 0x80000000  # 비활성화 → Bit 31 = 1
    
    return cob_id



# 테스트
node_id = 1  # 노드 아이디
enable = False  # 활성화 여부 (False = 비활성화)

pdo_identifier = get_pdo_identifier(node_id, enable)
print(f"PDO CAN Identifier: 0x{pdo_identifier:08X}")



def main():
    # CANopen 네트워크 설정
    network = canopen.Network()
    # CAN 버스 연결
    network.connect(bustype='socketcan', channel='can0')

    node_id = 4
    node = network.add_node(node_id, 'config/ZeroErr Driver_V1.5.eds')
    
    network.add_node(node)

    # This will attempt to read an SDO from nodes 1 - 127
    network.scanner.search()
    # We may need to wait a short while here to allow all nodes to respond
    time.sleep(0.05)
    for node_id in network.scanner.nodes:
        print(f"Found node {node_id}!")
    
    # network.sync.start(10)



    # Stop remote node
    try:
        network.nmt.send_command(0x02)  # NMT 정지 명령 전송
        print('원격 노드 정지 명령을 전송했습니다.')
    except canopen.SdoCommunicationError as e:
        print(f'원격 노드 정지 중 오류 발생: {str(e)}')
    
    time.sleep(1)

    # Reset remote node
    try:
        network.nmt.send_command(0x82)  # NMT 재설정 명령 전송
        print('원격 노드 재설정 명령을 전송했습니다.')
    except canopen.SdoCommunicationError as e:
        print(f'원격 노드 재설정 중 오류 발생: {str(e)}')

    time.sleep(1)

    # node 10 profile position mode
    node.sdo['Modes of operation'].raw = 0x01  # write
    print(f'[write] Modes of operation: 0x01 Profile Position Mode')
    ModeOfOperationDisplay = node.sdo['Modes of operation display'].raw # read
    print(f'[read] Modes of operation display: {ModeOfOperationDisplay}')

    # Profile velocity
    node.sdo['Profile velocity'].raw = 5566
    print(f'[write] Profile velocity: 262144')

    # Profile acceleration
    node.sdo['Profile acceleration'].raw = 5566
    print(f'[write] Profile acceleration: 262144')

    # Profile deceleration
    node.sdo['Profile deceleration'].raw = 5566
    print(f'[write] Profile deceleration: 262144')

    # Disable sync
    node.sdo['COB-ID SYNC message'].raw = 0x80
    print(f'[write] COB-ID SYNC message: 0x80')

    # Communication Cycle Period
    node.sdo['Communication Cycle Period'].raw = 1000
    print(f'[write] Communication Cycle Period: 1000us')
   

    """    # Disable TxPDO1
    node.sdo['COB ID used by PDO'].raw = get_pdo_identifier(node_id, False)
    print(f'[write] TxPDO1 Disable')

    # Defines the transmission type
    node.sdo['transmission type'].raw = 0x01
    print(f'[write] Transmission type: SYNC based PDO')

    # Defines the number of valid entries in the mapping record
    node.sdo['Transmit PDO 1 Mapping'].raw = 0x00
    print(f'[write] Transmit PDO 1 Mapping: 0x00')"""


    # Read PDO configuration from node
    node.tpdo.read()
    node.rpdo.read()

    node.tpdo[1].clear()
    node.tpdo[1].add_variable('Statusword')
    node.tpdo[1].add_variable('Position actual value')
    node.tpdo[1].trans_type = 0
    node.tpdo[1].event_timer = 0
    node.tpdo[1].enabled = True



    node.rpdo[1].clear()
    node.rpdo[1].add_variable('Controlword')
    node.rpdo[1].add_variable('Target Position')
    node.rpdo[1].trans_type = 255  # 즉시 적용
    node.rpdo[1].event_timer = 0   # 이벤트 타이머 비활성화
    node.rpdo[1].enabled = True
    # node.rpdo[1].transmission_type = 255  # 비동기 전송 설정

    # Save new configuration (node must be in pre-operational)
    node.nmt.state = 'PRE-OPERATIONAL'
    node.tpdo.save()
    node.rpdo.save()



    # Start remote node
    # node.nmt.state = 'OPERATIONAL'
    try:
        network.nmt.send_command(0x01)  # NMT 시작 명령 전송
        print('원격 노드 시작 명령을 전송했습니다.')
    except canopen.SdoCommunicationError as e:
        print(f'원격 노드 시작 중 오류 발생: {str(e)}')

    print('5초 대기')
    time.sleep(5)


    # Get actual position
    ActualPosition = node.sdo['Position actual value'].raw
    print(f'[read] Position actual value: {ActualPosition}')

    # Send sync
    #network.sync.start(0.01)

    node.rpdo[1]['Controlword'].phys = 0x26
    node.rpdo[1].transmit()  # start() 대신 transmit() 사용    
    network.sync.transmit()

    node.rpdo[1]['Controlword'].phys = 0x27
    node.rpdo[1].transmit()
    network.sync.transmit()

    node.rpdo[1]['Controlword'].phys = 0x2f
    node.rpdo[1].transmit()
    network.sync.transmit()

    node.rpdo[1]['Controlword'].phys = 0x3f
    node.rpdo[1]['Target Position'].phys = ActualPosition
    node.rpdo[1].transmit()
    network.sync.transmit()

    network.subscribe(node.tpdo[1].cob_id, node.tpdo[1].on_message)

    node.tpdo[1].add_callback(tpdo1_callback)

    print('5초 대기')
    time.sleep(5)

    node.rpdo[1]['Controlword'].phys = 0x2f
    node.rpdo[1].transmit()
    network.sync.transmit()

    node.rpdo[1]['Controlword'].phys = 0x3f
    node.rpdo[1]['Target Position'].phys = 5000
    node.rpdo[1].transmit()
    network.sync.transmit()

    node.rpdo[1]['Controlword'].phys = 0x2f
    node.rpdo[1].transmit()
    network.sync.transmit()

    node.rpdo[1]['Controlword'].phys = 0x3f
    node.rpdo[1]['Target Position'].phys = 5000
    node.rpdo[1].transmit()
    network.sync.transmit()

    try:
        network.sync.start(1)
        
        # 프로그램이 Ctrl+C로 종료될 때까지 실행
        while True:
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print('\n프로그램을 종료합니다.')
    finally:
        network.sync.stop()  # sync 메시지 중지
        network.disconnect()  # CAN 연결 종료


def tpdo1_callback(message):
    position = message.data[2] | (message.data[3] << 8) | (message.data[4] << 16) | (message.data[5] << 24)
    if position & 0x80000000:  # 최상위 비트가 1이면 음수
        position = -((~position + 1) & 0xFFFFFFFF)  # 2의 보수 처리
    print(f'TPDO1 Position actual value: {position}')

      

if __name__ == "__main__":
    main()