import canopen
import time
from abstract_motor import AbstractMotor

class MotorController:
    """
    하나의 CAN Bus 상에서 여러 모터(Node)를 관리하는 컨트롤러.
    예시: USB-CAN 장치와 연결하고, 제조사별 Motor 객체 등록/호출 등.
    """
    def __init__(self, channel='can0', bustype='socketcan', bitrate=1000000):
        """
        :param channel: 예) 'can0', 'pcan0', 'usb0' 등
        :param bustype: canopen 또는 python-can에서 사용하는 bustype 설정
        :param bitrate: CAN Bus 속도
        """
        self.network = canopen.Network()
        self.network.connect(channel=channel, bustype=bustype, bitrate=bitrate)
        # 등록된 모터 리스트/딕셔너리
        self.motors = {}

    def add_motor(self, motor: AbstractMotor):
        """MotorController가 관리할 모터를 추가한다."""
        node = self.network.add_node(motor.node_id, motor.eds_path)
        motor.node = node
        motor.network = self.network
        # SDO 타임아웃 값 설정
        node.sdo.RESPONSE_TIMEOUT = 2.0  # 2초로 변경
        # 재시도 횟수 설정
        node.sdo.MAX_RETRIES = 3
        # 요청 전 대기 시간 설정
        # node.sdo.PAUSE_BEFORE_SEND = 5
        self.motors[motor.node_id] = motor

    def init_all(self):
        """등록된 모든 모터를 초기화"""
        for node_id, motor in self.motors.items():
            motor.init()

    def reset_all(self):
        """등록된 모든 모터를 리셋"""
        for node_id, motor in self.motors.items():
            motor.reset()            

        self.network.nmt.send_command(0x02)  # Stop
        time.sleep(0.5)
        self.network.nmt.send_command(0x82)  # Reset
        time.sleep(1)  # 재설정 후 충분한 대기 시간

    def pdo_mapping_all(self):
        """등록된 모든 모터에 대해 PDO 매핑 설정"""
        for node_id, motor in self.motors.items():
            motor.pdo_mapping()

        # Start remote node
        try:
            self.network.nmt.send_command(0x01)  # NMT 시작 명령 전송
            print('원격 노드 시작 명령을 전송했습니다.')
        except canopen.SdoCommunicationError as e:
            print(f'원격 노드 시작 중 오류 발생: {str(e)}')

    def set_switchOn_all(self):
        for node_id, motor in self.motors.items():
            motor.set_switchOn()

    def pdo_callback_register_all(self):
        for node_id, motor in self.motors.items():
            motor.pdo_callback_register()

    def sync_start(self):
        self.network.sync.start(0.5) # 10ms

    def set_position_all(self, value):
        """등록된 모든 모터에 동일 위치를 세팅"""
        for node_id, motor in self.motors.items():
            motor.set_position(value)            
    
    def set_position(self, node_id, value):
        if node_id in self.motors:
            self.motors[node_id].set_position(value)
        else:
            print(f"Node {node_id} not found in motors dictionary.")

    def get_positions(self):
        """등록된 모든 모터의 위치를 dict로 반환"""        
        positions = {}
        for node_id, motor in self.motors.items():
            positions[node_id] = motor.get_position()
        return positions

    def disconnect(self):
        """네트워크 해제"""
        self.network.sync.stop()
        self.network.disconnect()