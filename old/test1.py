import canopen
import time

class CANopenNode():
    def __init__(self):
        super().__init__()
        
        # CANopen 네트워크 설정
        self.network = canopen.Network()

        node_id = 4
        self.node = self.network.add_node(node_id, 'config/ZeroErr Driver_V1.5.eds')  # EDS 파일 경로 설정 필요

        self.network.add_node(self.node)

        # CAN 버스 연결        
        self.network.connect(bustype='socketcan', channel='can0')
        # self.network.sync.start(10)

        # 노드 상태 변경 전 지연 추가
        time.sleep(1)  # 1초 대기

        self.node.sdo[0x6040].raw = 0x27

        self.node.sdo[0x6040].raw = 0x26


        # NMT 명령 전송 시 예외 처리 및 재시도 로직 추가
        retry_count = 3
        for _ in range(retry_count):
            try:
                self.network.nmt.send_command(0x02)  # Stop
                time.sleep(0.5)
                self.network.nmt.send_command(0x82)  # Reset
                time.sleep(1)  # 재설정 후 충분한 대기 시간
                break
            except canopen.SdoCommunicationError as e:
                print(f'NMT 명령 전송 실패, 재시도 중: {str(e)}')
                time.sleep(1)

        # SDO 통신 시도 전 노드 상태 확인
        try:
            if self.node.nmt.wait_for_heartbeat(timeout=3.0):
                print("노드가 응답합니다. 계속 진행합니다.")
                self.node.sdo['Modes of operation'].raw = 0x01
            else:
                print("노드가 응답하지 않습니다.")
        except Exception as e:
            print(f"노드 통신 오류: {str(e)}")

        # node 10 profile position mode
        self.node.sdo['Modes of operation'].raw = 0x01  # write
        print(f'[write] Modes of operation: 0x01 Profile Position Mode')
        self.ModeOfOperationDisplay = self.node.sdo['Modes of operation display'].raw # read
        print(f'[read] Modes of operation display: {self.ModeOfOperationDisplay}')

        # Profile velocity
        self.node.sdo['Profile velocity'].raw = 262143
        print(f'[write] Profile velocity: 262144')

        # Profile acceleration
        self.node.sdo['Profile acceleration'].raw = 262143
        print(f'[write] Profile acceleration: 262144')

        # Profile deceleration
        self.node.sdo['Profile deceleration'].raw = 262143
        print(f'[write] Profile deceleration: 262144')

        # Disable sync
        self.network.sync.stop()

        # Communication Cycle Period
        # self.node.sdo['Communication Cycle Period'].raw = 1000
        # print(f'[write] Communication Cycle Period: 1000')

        # Read PDO configuration from node
        self.node.tpdo.read()
        self.node.rpdo.read()

        self.node.tpdo[1].clear()
        self.node.tpdo[1].add_variable('Statusword')
        self.node.tpdo[1].add_variable('Position actual value')
        self.node.tpdo[1].trans_type = 0
        self.node.tpdo[1].event_timer = 0
        self.node.tpdo[1].enabled = True



        self.node.rpdo[1].clear()
        self.node.rpdo[1].add_variable('Controlword')
        self.node.rpdo[1].add_variable('Target Position')
        self.node.rpdo[1].trans_type = 255  # 즉시 적용
        self.node.rpdo[1].event_timer = 0   # 이벤트 타이머 비활성화
        self.node.rpdo[1].enabled = True
        # self.node.rpdo[1].transmission_type = 255  # 비동기 전송 설정

        # Save new configuration (node must be in pre-operational)
        self.node.nmt.state = 'PRE-OPERATIONAL'
        self.node.tpdo.save()
        self.node.rpdo.save()



        # Start remote node
        self.node.nmt.state = 'OPERATIONAL'
        try:
            self.network.nmt.send_command(0x01)  # NMT 시작 명령 전송
            print('원격 노드 시작 명령을 전송했습니다.')
        except canopen.SdoCommunicationError as e:
            print(f'원격 노드 시작 중 오류 발생: {str(e)}')


        # Get actual position
        self.ActualPosition = self.node.sdo['Position actual value'].raw
        print(f'[read] Position actual value: {self.ActualPosition}')

        # Send sync
        #self.network.sync.start(0.01)

        self.node.rpdo[1]['Controlword'].phys = 0x80
        self.node.rpdo[1].transmit()  # start() 대신 transmit() 사용
        self.network.sync.transmit()
        time.sleep(0.1)

        self.node.rpdo[1]['Controlword'].phys = 0x26
        self.node.rpdo[1].transmit()  # start() 대신 transmit() 사용
        self.network.sync.transmit()
        time.sleep(0.1)

        self.node.rpdo[1]['Controlword'].phys = 0x27
        self.node.rpdo[1].transmit()
        self.network.sync.transmit()
        time.sleep(0.1)

        self.node.rpdo[1]['Controlword'].phys = 0x2f
        self.node.rpdo[1].transmit()
        self.network.sync.transmit()
        time.sleep(0.1)

        self.node.rpdo[1]['Controlword'].phys = 0x3f
        self.node.rpdo[1]['Target Position'].phys = self.ActualPosition
        self.node.rpdo[1].transmit()
        self.network.sync.transmit()
        time.sleep(0.1)

        self.network.subscribe(self.node.tpdo[1].cob_id, self.node.tpdo[1].on_message)

        print('5초 대기')
        time.sleep(5)

        # self.node.tpdo[1].add_callback(self.tpdo1_callback)



        # # 목표 위치 구독자 추가
        # self.target_position_sub = self.create_subscription(
        #     Int32,
        #     'target_position',
        #     self.target_position_callback,
        #     10
        # )
        print('목표 위치 구독자가 생성되었습니다.')

        target_position = 5000000
        print(f'새로운 목표 위치를 받았습니다: {target_position}')

        # 목표 위치 설정
        self.node.rpdo[1]['Controlword'].phys = 0x2f  # 위치 이동 명령
        self.node.rpdo[1].transmit()
        self.network.sync.transmit()
        time.sleep(0.1)

        self.node.rpdo[1]['Target Position'].phys = target_position
        self.node.rpdo[1]['Controlword'].phys = 0x3f  # 위치 이동 명령
        self.node.rpdo[1].transmit()
        self.network.sync.transmit()
        time.sleep(0.1)

        self.node.rpdo[1]['Controlword'].phys = 0x2f  # 위치 이동 명령
        self.node.rpdo[1].transmit()
        self.network.sync.transmit()

        
        # 모터가 목표 위치에 도달할 때까지 대기
        try:
            while True:
                print(f"Current Position: {self.node.sdo['Position actual value'].raw}")
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nCtrl+C가 감지되었습니다. 프로그램을 종료합니다.")
        finally:
            # 안전한 종료를 위한 정리 작업            
            self.network.disconnect()
            print("프로그램이 안전하게 종료되었습니다.")

    def tpdo1_callback(self, message):
        print(f'TPDO1 수신: {message.data}')

        # TPDO1 데이터 파싱
        statusword = message.data[0] | (message.data[1] << 8)
        position_actual_value = (message.data[2] | (message.data[3] << 8) |
                                (message.data[4] << 16) | (message.data[5] << 24))

        print(f'Statusword: 0x{statusword:04X}')
        print(f'Position Actual Value: {position_actual_value}')

    def target_position_callback(self, msg):
        target_position = msg.data
        print(f'새로운 목표 위치를 받았습니다: {target_position}')

        # 목표 위치 설정
        self.node.rpdo[1]['Controlword'].phys = 0x2f  # 위치 이동 명령
        self.node.rpdo[1].transmit()

        self.node.rpdo[1]['Target Position'].phys = target_position
        self.node.rpdo[1]['Controlword'].phys = 0x3f  # 위치 이동 명령
        self.node.rpdo[1].transmit()

        self.node.rpdo[1]['Controlword'].phys = 0x2f  # 위치 이동 명령
        self.node.rpdo[1].transmit()

    def __del__(self):
        # 노드가 종료될 때 CAN 버스 연결 해제
        self.network.disconnect()


if __name__ == '__main__':
    CANopenNode()
