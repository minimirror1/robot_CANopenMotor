import canopen
import time
from abc import ABC, abstractmethod

class AbstractMotor(ABC):
    """모든 모터가 공통으로 가져야 할 인터페이스 정의(추상 클래스)."""

    def __init__(self, node_id, eds_path):
        self.node_id = node_id
        self.eds_path = eds_path
        self.node = None  # canopen에서 로드되는 노드 객체 (초기에는 None)
        self.network = None  # network 객체 추가
        # 목표 위치와 현재 위치를 저장하는 변수 추가
        self.target_position = 0  # 목표 위치값 저장용 변수
        self.current_position = 0  # 현재 위치값 저장용 변수

    @abstractmethod
    def init(self):
        """모터 초기화 절차"""
        pass

    @abstractmethod
    def reset(self):
        """모터 리셋(에러 클리어 등)"""
        pass

    @abstractmethod
    def pdo_mapping(self):
        """PDO 매핑 설정"""
        pass

    @abstractmethod
    def set_switchOn(self):
        """Switch On 명령"""
        pass

    @abstractmethod
    def set_position(self, value):
        """모터 위치 명령"""
        pass

    @abstractmethod
    def get_position(self):
        """모터 위치 확인"""
        pass

    @abstractmethod
    def tpdo1_callback(self, message):
        """TPDO1 콜백 함수"""
        pass


class MotorVendorZeroErr(AbstractMotor):
    """제조사 A 모터에 대한 구체 구현."""
    def __init__(self, node_id, eds_path):
        super().__init__(node_id, eds_path)

    def init(self):
        # 모터 초기화
        print(f"[MotorVendorZeroErr] Init motor node: {self.node_id}")
        # node 10 profile position mode
        self.node.sdo['Modes of operation'].raw = 0x01  # write
        print(f'[write] Modes of operation: 0x01 Profile Position Mode')
        self.ModeOfOperationDisplay = self.node.sdo['Modes of operation display'].raw # read
        print(f'[read] Modes of operation display: {self.ModeOfOperationDisplay}')

        # Profile velocity
        self.node.sdo['Profile velocity'].raw = 100000
        print(f'[write] Profile velocity: 262144')

        # Profile acceleration
        self.node.sdo['Profile acceleration'].raw = 100000
        print(f'[write] Profile acceleration: 262144')

        # Profile deceleration
        self.node.sdo['Profile deceleration'].raw = 100000
        print(f'[write] Profile deceleration: 262144')

        # Disable sync
        self.network.sync.stop()
        pass

    def reset(self):
        print(f"[MotorVendorZeroErr] Reset motor node: {self.node_id}")
        self.node.sdo[0x6040].raw = 0x27
        self.node.sdo[0x6040].raw = 0x26    
        self.node.sdo[0x6040].raw = 0x80  # 에러 클리어
        pass

    def pdo_mapping(self):
        print(f"[MotorVendorZeroErr] PDO mapping for node: {self.node_id}")
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
        self.node.rpdo[1].trans_type = 0  # 즉시 적용
        #self.node.rpdo[1].event_timer = 255   # 이벤트 타이머 비활성화
        self.node.rpdo[1].enabled = True
        
        # Save new configuration (node must be in pre-operational)
        self.node.nmt.state = 'PRE-OPERATIONAL'
        self.node.tpdo.save()
        self.node.rpdo.save()

        #self.node.rpdo[1].period = 0.1  # 100ms
        #self.node.rpdo[1].start()
        # Start remote node
        self.node.nmt.state = 'OPERATIONAL'


        self.node.sdo[0x1400][2].raw = 0x01
        self.node.sdo[0x1401][2].raw = 0x01
        self.node.sdo[0x1402][2].raw = 0x01
        self.node.sdo[0x1403][2].raw = 0x01
        pass

    def set_switchOn(self):
        print(f"[MotorVendorZeroErr] Set switch on, node: {self.node_id}")
        self.node.rpdo[1]['Controlword'].phys = 0x26
        self.node.rpdo[1].transmit()  # start() 대신 transmit() 사용    
        self.network.sync.transmit()

        self.node.rpdo[1]['Controlword'].phys = 0x27
        self.node.rpdo[1].transmit()
        self.network.sync.transmit()

        self.node.rpdo[1]['Controlword'].phys = 0x2f
        self.node.rpdo[1].transmit()
        self.network.sync.transmit()

        self.node.rpdo[1]['Controlword'].phys = 0x3f
        self.node.rpdo[1]['Target Position'].phys = self.get_position()
        self.node.rpdo[1].transmit()
        self.network.sync.transmit()        

        self.network.subscribe(self.node.tpdo[1].cob_id, self.node.tpdo[1].on_message)
        self.node.tpdo[1].add_callback(self.tpdo1_callback)
        pass

    def set_position(self, value):
        print(f"[MotorVendorZeroErr] Set position to {value}, node: {self.node_id}")
        self.node.rpdo[1]['Controlword'].phys = 0x2f
        self.node.rpdo[1]['Target Position'].phys = value
        self.node.rpdo[1].transmit()
        #self.network.sync.transmit()
        

        self.node.rpdo[1]['Controlword'].phys = 0x3f
        self.node.rpdo[1].transmit()
        #self.network.sync.transmit()
        pass

    def get_position(self):
        print(f"get Transmission 1 type {self.node.sdo[0x1400][2].raw}")
        print(f"get Transmission 2 type {self.node.sdo[0x1401][2].raw}")
        print(f"get Transmission 3 type {self.node.sdo[0x1402][2].raw}")
        print(f"get Transmission 4 type {self.node.sdo[0x1403][2].raw}")
        self.current_position = self.node.sdo['Position actual value'].raw
        print(f"[MotorVendorZeroErr] Get position, node: {self.node_id}, position: {self.current_position}")
        return self.current_position

    def tpdo1_callback(self, message):
        position = message.data[2] | (message.data[3] << 8) | (message.data[4] << 16) | (message.data[5] << 24)
        if position & 0x80000000:  # 최상위 비트가 1이면 음수
            position = -((~position + 1) & 0xFFFFFFFF)  # 2의 보수 처리
        self.current_position = position
        print(f'TPDO1 Position actual value: {position}')


class MotorVendorB(AbstractMotor):
    """제조사 B 모터에 대한 구체 구현."""
    def __init__(self, node_id, eds_path):
        super().__init__(node_id, eds_path)

    def init(self):
        print(f"[VendorB] Init motor node: {self.node_id}")
        pass

    def reset(self):
        print(f"[VendorB] Reset motor node: {self.node_id}")
        pass

    def pdo_mapping(self):
        print(f"[VendorB] PDO mapping for node: {self.node_id}")
        pass

    def set_position(self, value):
        print(f"[VendorB] Set position to {value}, node: {self.node_id}")
        pass

    def get_position(self):
        print(f"[VendorB] Get position, node: {self.node_id}")
        return 0


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
        motor.network = self.network  # network 객체 전달
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

    def set_position_all(self, value):
        """등록된 모든 모터에 동일 위치를 세팅"""
        for node_id, motor in self.motors.items():
            motor.set_position(value)
            time.sleep(2)

        for i in range(10):
            print(f'countdown: {i}')
            time.sleep(1)
        #self.network.sync.transmit()    

    def get_positions(self):

        
        """등록된 모든 모터의 위치를 dict로 반환"""
        positions = {}
        for node_id, motor in self.motors.items():
            positions[node_id] = motor.get_position()
        return positions

    def disconnect(self):
        """네트워크 해제"""
        self.network.disconnect()


# 필요하다면, 제조사 정보를 바탕으로 인스턴스를 생성해주는 Factory 구현 예시
class MotorFactory:
    @staticmethod
    def create_motor(vendor, node_id, eds_path):
        if vendor == "VendorZeroErr":
            return MotorVendorZeroErr(node_id, eds_path)
        elif vendor == "VendorB":
            return MotorVendorB(node_id, eds_path)
        else:
            raise ValueError(f"Unknown vendor type: {vendor}")


def main():
    # 예시: CAN Bus controller 생성
    controller = MotorController(channel='can0', bustype='socketcan', bitrate=1000000)

    # 예시: 모터 생성(제조사별)
    motorA = MotorFactory.create_motor("VendorZeroErr", 1, "config/ZeroErr Driver_V1.5.eds")
    motorB = MotorFactory.create_motor("VendorZeroErr", 2, "config/ZeroErr Driver_V1.5.eds")
    motorC = MotorFactory.create_motor("VendorZeroErr", 3, "config/ZeroErr Driver_V1.5.eds")
    motorD = MotorFactory.create_motor("VendorZeroErr", 4, "config/ZeroErr Driver_V1.5.eds")
    #motorB = MotorFactory.create_motor("VendorB", 2, "vendorB.eds")

    # 컨트롤러에 모터 등록
    controller.add_motor(motorA)
    #controller.add_motor(motorB)
    #controller.add_motor(motorC)
    #controller.add_motor(motorD)
    #time.sleep(3) 
    # 리셋
    controller.reset_all()
    #time.sleep(3) 
    # 모터 전체 초기화
    controller.init_all()
    #time.sleep(3) 
    # PDO 매핑
    controller.pdo_mapping_all()
    
    time.sleep(3) 
    print("wait 3 sec")
    # 위치 설정
    controller.set_position_all(50000)
    controller.set_position_all(0)
    #time.sleep(3) 
    # 위치 읽기
    time.sleep(3) 
    positions = controller.get_positions()
    print("Current positions:", positions)



    # 종료 전 네트워크 해제
    controller.disconnect()

if __name__ == "__main__":
    main()
