import rclpy
from rclpy.node import Node
import canopen
import os
from ament_index_python.packages import get_package_share_directory
from std_msgs.msg import Int32

class CANopenNode(Node):
    def __init__(self):
        super().__init__('canopen_node')
        self.get_logger().info('CANopen ROS2 노드가 시작되었습니다.')

        # CANopen 네트워크 설정
        self.network = canopen.Network()
        package_share_dir = get_package_share_directory('canopen_python_pkg')
        eds_path = os.path.join(package_share_dir, 'config', 'ZeroErr Driver_V1.5.eds')

        self.node = canopen.RemoteNode(10, eds_path)

        self.network.add_node(self.node)

        # CAN 버스 연결
        self.network.connect(bustype='socketcan', channel='can0')
        # self.network.sync.start(10)



        # Stop remote node
        try:
            self.network.nmt.send_command(0x02)  # NMT 정지 명령 전송
            self.get_logger().info('원격 노드 정지 명령을 전송했습니다.')
        except canopen.SdoCommunicationError as e:
            self.get_logger().error(f'원격 노드 정지 중 오류 발생: {str(e)}')
        # Reset remote node
        try:
            self.network.nmt.send_command(0x82)  # NMT 재설정 명령 전송
            self.get_logger().info('원격 노드 재설정 명령을 전송했습니다.')
        except canopen.SdoCommunicationError as e:
            self.get_logger().error(f'원격 노드 재설정 중 오류 발생: {str(e)}')

        # node 10 profile position mode
        self.node.sdo['Modes of operation'].raw = 0x01  # write
        self.get_logger().info(f'[write] Modes of operation: 0x01 Profile Position Mode')
        self.ModeOfOperationDisplay = self.node.sdo['Modes of operation display'].raw # read
        self.get_logger().info(f'[read] Modes of operation display: {self.ModeOfOperationDisplay}')

        # Profile velocity
        self.node.sdo['Profile velocity'].raw = 262144
        self.get_logger().info(f'[write] Profile velocity: 262144')

        # Profile acceleration
        self.node.sdo['Profile acceleration'].raw = 262144
        self.get_logger().info(f'[write] Profile acceleration: 262144')

        # Profile deceleration
        self.node.sdo['Profile deceleration'].raw = 262144
        self.get_logger().info(f'[write] Profile deceleration: 262144')

        # Disable sync
        self.network.sync.stop()

        # Communication Cycle Period
        # self.node.sdo['Communication Cycle Period'].raw = 1000
        # self.get_logger().info(f'[write] Communication Cycle Period: 1000')

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
            self.get_logger().info('원격 노드 시작 명령을 전송했습니다.')
        except canopen.SdoCommunicationError as e:
            self.get_logger().error(f'원격 노드 시작 중 오류 발생: {str(e)}')


        # Get actual position
        self.ActualPosition = self.node.sdo['Position actual value'].raw
        self.get_logger().info(f'[read] Position actual value: {self.ActualPosition}')

        # Send sync
        #self.network.sync.start(0.01)

        self.node.rpdo[1]['Controlword'].phys = 0x26
        self.node.rpdo[1].transmit()  # start() 대신 transmit() 사용

        self.node.rpdo[1]['Controlword'].phys = 0x27
        self.node.rpdo[1].transmit()

        self.node.rpdo[1]['Controlword'].phys = 0x2f
        self.node.rpdo[1].transmit()

        self.node.rpdo[1]['Controlword'].phys = 0x3f
        self.node.rpdo[1]['Target Position'].phys = 0#524288 * 10
        self.node.rpdo[1].transmit()

        self.network.subscribe(self.node.tpdo[1].cob_id, self.node.tpdo[1].on_message)

        # self.node.tpdo[1].add_callback(self.tpdo1_callback)



        # 목표 위치 구독자 추가
        self.target_position_sub = self.create_subscription(
            Int32,
            'target_position',
            self.target_position_callback,
            10
        )
        self.get_logger().info('목표 위치 구독자가 생성되었습니다.')

    def tpdo1_callback(self, message):
        self.get_logger().info(f'TPDO1 수신: {message.data}')

        # TPDO1 데이터 파싱
        statusword = message.data[0] | (message.data[1] << 8)
        position_actual_value = (message.data[2] | (message.data[3] << 8) |
                                (message.data[4] << 16) | (message.data[5] << 24))

        self.get_logger().info(f'Statusword: 0x{statusword:04X}')
        self.get_logger().info(f'Position Actual Value: {position_actual_value}')

    def target_position_callback(self, msg):
        target_position = msg.data
        self.get_logger().info(f'새로운 목표 위치를 받았습니다: {target_position}')

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

def main(args=None):
    rclpy.init(args=args)
    node = CANopenNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
