from abstract_motor import AbstractMotor
import time
class MotorVendorZeroErr(AbstractMotor):
    """제조사 A 모터에 대한 구체 구현."""
    def __init__(self, node_id, eds_path, zero_offset=0):
        super().__init__(node_id, eds_path, zero_offset)
        # 토크 필터링을 위한 변수 추가
        self.torque_buffer_size = 20  # 100ms 동안의 데이터 (10ms * 10)
        self.torque_buffer = []
        self.Q = 0.01   # 0.02에서 0.01로 감소 (더욱 안정적인 추정)
        self.R = 8.0    # 4.0에서 8.0으로 증가 (스파이크 제거 강화)
        self.P = 1.0    # 유지
        self.filtered_torque = 0
        
        # 데이터 로깅을 위한 변수 추가
        self.logging_enabled = False
        self.log_counter = 0
        self.log_interval = 100  # 로깅 주기 (100번의 데이터마다 출력)
        
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

        self.node.tpdo[2].clear()
        self.node.tpdo[2].add_variable('Torque sensor')
        self.node.tpdo[2].add_variable('Velocity actual value')
        self.node.tpdo[2].cob_id = 0x300 + self.node_id
        self.node.tpdo[2].trans_type = 1
        self.node.tpdo[2].event_timer = 0
        self.node.tpdo[2].enabled = True

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
    
    def get_torque(self):
        """모터 토크 확인"""
        #return self.node.sdo['Torque sensor'].raw
        return self.current_torque
    def get_velocity(self):
        """모터 속도 확인"""
        #return self.node.sdo['Velocity actual value'].raw
        return self.current_velocity

    def tpdo1_callback(self, message):
        position = message.data[2] | (message.data[3] << 8) | (message.data[4] << 16) | (message.data[5] << 24)
        if position & 0x80000000:  # 최상위 비트가 1이면 음수
            position = -((~position + 1) & 0xFFFFFFFF)  # 2의 보수 처리
        self.current_position = position - self.zero_offset
        #print(f'TPDO1 Position actual value: {position}')

    def filter_torque(self, new_torque):
        """토크 값에 대한 이동 평균 필터 적용"""
        self.torque_buffer.append(new_torque)
        if len(self.torque_buffer) > self.torque_buffer_size:
            self.torque_buffer.pop(0)
        self.filtered_torque = sum(self.torque_buffer) / len(self.torque_buffer)
        return self.filtered_torque

    def filter_torque_kalman(self, new_torque):
        """칼만 필터 적용"""
        # Prediction
        P_pred = self.P + self.Q
        
        # Update
        K = P_pred / (P_pred + self.R)  # Kalman gain
        self.filtered_torque = self.filtered_torque + K * (new_torque - self.filtered_torque)
        self.P = (1 - K) * P_pred
        
        return self.filtered_torque

    def enable_torque_logging(self, enable=True):
        """토크 데이터 로깅 활성화/비활성화"""
        self.logging_enabled = enable
        print("토크 데이터 로깅이 시작되었습니다." if enable else "토크 데이터 로깅이 중지되었습니다.")

    def log_torque_data(self, raw_torque):
        """토크 데이터 로깅"""
        if not self.logging_enabled:
            return
        
        self.log_counter += 1
        if self.log_counter >= self.log_interval:
            print(f"Raw: {raw_torque:8.2f}, Filtered: {self.filtered_torque:8.2f}, "
                  f"Diff: {raw_torque - self.filtered_torque:8.2f}, "
                  f"P: {self.P:8.4f}, Q: {self.Q:8.4f}, R: {self.R:8.4f}")
            self.log_counter = 0

    def tpdo2_callback(self, message):
        # Torque sensor 값 처리
        torque = message.data[0] | (message.data[1] << 8) | (message.data[2] << 16) | (message.data[3] << 24)
        if torque & 0x80000000:
            torque = -((~torque + 1) & 0xFFFFFFFF)
        
        # 필터링 전 원본 데이터 로깅
        filtered_torque = self.filter_torque_kalman(torque)
        self.log_torque_data(torque)
        self.current_torque = filtered_torque

        # Velocity actual value 처리 (다음 4바이트)
        velocity = message.data[4] | (message.data[5] << 8) | (message.data[6] << 16) | (message.data[7] << 24)
        if velocity & 0x80000000:  # 음수 처리
            velocity = -((~velocity + 1) & 0xFFFFFFFF)
        self.current_velocity = velocity

        #print(f'TPDO2 Torque sensor: {torque}, Velocity actual value: {velocity}')

        
        
