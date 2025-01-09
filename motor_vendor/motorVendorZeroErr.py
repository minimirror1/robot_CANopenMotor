from abstract_motor import AbstractMotor
import time
class MotorVendorZeroErr(AbstractMotor):
    """제조사 A 모터에 대한 구체 구현."""
    def __init__(self, node_id, eds_path, zero_offset=0):
        super().__init__(node_id, eds_path, zero_offset)
        self.control_mode = 'position'  # 'position' 또는 'torque' 모드
        
    def init(self):
        # 모터 초기화
        print(f"[MotorVendorZeroErr] Init motor node: {self.node_id}")
        # node 10 profile position mode
        self.node.sdo['Modes of operation'].raw = 0x04  # write
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
        time.sleep(0.1)
        self.node.sdo[0x6040].raw = 0x26    
        time.sleep(0.1)
        self.node.sdo[0x6040].raw = 0x80  # 에러 클리어
        time.sleep(0.1)
        pass

    def pdo_mapping(self):
        print(f"[MotorVendorZeroErr] PDO mapping for node: {self.node_id}")
        # Read PDO configuration from node
        self.node.tpdo.read()
        self.node.rpdo.read()

        self.node.tpdo[1].clear()
        self.node.tpdo[1].add_variable('Statusword')
        self.node.tpdo[1].add_variable('Position actual value')
        self.node.tpdo[1].cob_id = 0x180 + self.node_id
        self.node.tpdo[1].trans_type = 1
        self.node.tpdo[1].event_timer = 0
        self.node.tpdo[1].enabled = True

        self.node.rpdo[1].clear()
        self.node.rpdo[1].add_variable('Controlword')
        self.node.rpdo[1].add_variable('Target Position')
        self.node.rpdo[1].cob_id = 0x200 + self.node_id
        self.node.rpdo[1].trans_type = 0  # 즉시 적용
        #self.node.rpdo[1].event_timer = 255   # 이벤트 타이머 비활성화
        self.node.rpdo[1].enabled = True
        
        # Save new configuration (node must be in pre-operational)
        self.node.nmt.state = 'PRE-OPERATIONAL'
        self.node.tpdo.save()
        self.node.rpdo.save()

        # 토크 피드백을 위한 TPDO2 설정 추가
        self.node.tpdo[2].clear()
        self.node.tpdo[2].add_variable('Torque actual value')
        self.node.tpdo[2].cob_id = 0x280 + self.node_id
        self.node.tpdo[2].trans_type = 1
        self.node.tpdo[2].event_timer = 0
        self.node.tpdo[2].enabled = True

        # 토크 명령을 위한 RPDO2 설정
        self.node.rpdo[2].clear()
        self.node.rpdo[2].add_variable('Target Torque')
        self.node.rpdo[2].cob_id = 0x300 + self.node_id
        self.node.rpdo[2].trans_type = 0
        self.node.rpdo[2].enabled = True

        #self.node.rpdo[1].period = 0.1  # 100ms
        #self.node.rpdo[1].start()
        # Start remote node
        self.node.nmt.state = 'OPERATIONAL'

        pass

    def set_switchOn(self):
        print(f"[MotorVendorZeroErr] Set switch on, node: {self.node_id}")
        """self.node.rpdo[1]['Controlword'].phys = 0x26
        self.node.rpdo[1].transmit()  # start() 대신 transmit() 사용    
        self.network.sync.transmit()

        self.node.rpdo[1]['Controlword'].phys = 0x27
        self.node.rpdo[1].transmit()
        self.network.sync.transmit()

        self.node.rpdo[1]['Controlword'].phys = 0x2f
        self.node.rpdo[1].transmit()
        self.network.sync.transmit()"""
        
        time.sleep(0.001)
        self.node.rpdo[1]['Controlword'].phys = 0x2f
        self.node.rpdo[1]['Target Position'].phys = self.node.sdo['Position actual value'].raw
        self.node.rpdo[1].transmit()
        time.sleep(0.001)

        self.node.rpdo[1]['Controlword'].phys = 0x3f
        self.node.rpdo[1].transmit()        
        time.sleep(0.001)

        pass

    def pdo_callback_register(self):
        self.network.subscribe(self.node.tpdo[1].cob_id, self.node.tpdo[1].on_message)
        self.node.tpdo[1].add_callback(self.tpdo1_callback)
        
        # 토크 피드백을 위한 TPDO2 콜백 등록
        self.network.subscribe(self.node.tpdo[2].cob_id, self.node.tpdo[2].on_message)
        self.node.tpdo[2].add_callback(self.tpdo2_callback)

    def set_position(self, value):
        print(f"[MotorVendorZeroErr] Set position to {value}, node: {self.node_id}")
        self.node.rpdo[1]['Controlword'].phys = 0x2f
        self.target_position = value + self.zero_offset
        self.node.rpdo[1]['Target Position'].phys = self.target_position
        self.node.rpdo[1].transmit()

        print(f"myzero_offset {self.zero_offset} , target_position {self.target_position}")

        self.node.rpdo[1]['Controlword'].phys = 0x3f
        self.node.rpdo[1].transmit()        
        pass

    def get_position(self):        
        # self.current_position = self.node.sdo['Position actual value'].raw
        # print(f"[MotorVendorZeroErr] Get position, node: {self.node_id}, position: {self.current_position}")
        return self.current_position

    def tpdo1_callback(self, message):
        """TPDO1 콜백 함수 (위치 피드백 처리)"""
        position = message.data[2] | (message.data[3] << 8) | (message.data[4] << 16) | (message.data[5] << 24)
        if position & 0x80000000:  # 최상위 비트가 1이면 음수
            position = -((~position + 1) & 0xFFFFFFFF)  # 2의 보수 처리
        self.current_position = position - self.zero_offset
        
        # 임피던스 제어 모드일 때 토크 계산 및 명령
        if self.control_mode == 'torque':
            commanded_torque = self.calculate_impedance_torque()
            self.set_torque(commanded_torque)

    def enable_impedance_mode(self):
        """임피던스 제어 모드 활성화 (토크 제어 모드로 변경)"""
        print(f"[MotorVendorZeroErr] Enable impedance mode, node: {self.node_id}")
        # 토크 제어 모드(Mode of operation = 4)로 변경
        self.node.sdo['Modes of operation'].raw = 0x04
        time.sleep(0.1)
        mode = self.node.sdo['Modes of operation display'].raw
        print(f'[read] Current mode of operation: {mode}')
        self.control_mode = 'torque'

    def set_impedance(self, stiffness, damping):
        """임피던스 제어 파라미터 설정 (소프트웨어적으로 처리)"""
        print(f"[MotorVendorZeroErr] Set impedance parameters - stiffness: {stiffness}, damping: {damping}, node: {self.node_id}")
        self.stiffness = stiffness
        self.damping = damping

    def calculate_impedance_torque(self):
        """임피던스 제어 알고리즘에 따른 토크 계산"""
        if self.control_mode != 'torque':
            return 0
            
        # 위치 오차 계산
        position_error = self.target_position - self.current_position
        
        # 속도 계산 (간단한 미분)
        current_time = time.time()
        dt = current_time - self.last_time if hasattr(self, 'last_time') else 0.001
        self.last_time = current_time
        
        current_velocity = (self.current_position - self.last_position) / dt if hasattr(self, 'last_position') else 0
        self.last_position = self.current_position

        # 임피던스 제어 수식: τ = K(x_d - x) + D(-ẋ)
        spring_torque = self.stiffness * position_error
        damping_torque = -self.damping * current_velocity
        
        commanded_torque = spring_torque + damping_torque
        
        # 토크 제한 (하드웨어 보호)
        MAX_TORQUE = 1000  # 적절한 값으로 설정
        commanded_torque = max(min(commanded_torque, MAX_TORQUE), -MAX_TORQUE)
        
        return commanded_torque

    def set_torque(self, torque):
        """토크 명령"""
        if self.control_mode != 'torque':
            return
            
        print(f"[MotorVendorZeroErr] Set torque to {torque}, node: {self.node_id}")
        self.target_torque = torque
        self.node.rpdo[2]['Target Torque'].phys = torque
        self.node.rpdo[2].transmit()

    def get_torque(self):
        """현재 토크값 확인"""
        return self.current_torque

    def tpdo2_callback(self, message):
        """TPDO2 콜백 함수 (토크 피드백 처리)"""
        torque = message.data[0] | (message.data[1] << 8)  # 16비트 토크값 처리
        if torque & 0x8000:  # 최상위 비트가 1이면 음수
            torque = -((~torque + 1) & 0xFFFF)
        self.current_torque = torque