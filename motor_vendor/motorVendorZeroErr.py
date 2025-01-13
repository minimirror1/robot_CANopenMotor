from abstract_motor import AbstractMotor
import time
class MotorVendorZeroErr(AbstractMotor):
    """제조사 A 모터에 대한 구체 구현."""
    def __init__(self, node_id, eds_path, zero_offset=0):
        super().__init__(node_id, eds_path, zero_offset)
        
    def init(self):
        # 모터 초기화
        print(f"[MotorVendorZeroErr] Init motor node: {self.node_id}")
        # node 10 profile position mode
        self.node.sdo['Modes of operation'].raw = 0x01  # write
        print(f'[write] Modes of operation: 0x01 Profile Position Mode')
        self.ModeOfOperationDisplay = self.node.sdo['Modes of operation display'].raw # read
        print(f'[read] Modes of operation display: {self.ModeOfOperationDisplay}')

        # Profile velocity
        self.node.sdo['Profile velocity'].raw = 262144
        print(f'[write] Profile velocity: 262144')

        # Profile acceleration
        self.node.sdo['Profile acceleration'].raw = 262144
        print(f'[write] Profile acceleration: 262144')

        # Profile deceleration
        self.node.sdo['Profile deceleration'].raw = 262144
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
        position = message.data[2] | (message.data[3] << 8) | (message.data[4] << 16) | (message.data[5] << 24)
        if position & 0x80000000:  # 최상위 비트가 1이면 음수
            position = -((~position + 1) & 0xFFFFFFFF)  # 2의 보수 처리
        self.current_position = position - self.zero_offset
        #print(f'TPDO1 Position actual value: {position}')