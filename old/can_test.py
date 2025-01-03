import can
import time

def test_can_communication(channel='can0', bitrate=1000000, timeout=0.5):
    """
    1~10까지 tx 메시지를 송신하고, 각 메시지 전송 후 대응 rx 메시지 수신 여부를 확인하는 함수.
    
    Parameters:
        channel (str): 사용 CAN 채널 (예: 'can0')
        bitrate (int): CAN bitrate
        timeout (float): 각 rx 대기 시간 (초)
    """
    # CAN 버스 연결
    bus = can.interface.Bus(bustype='socketcan', channel=channel, bitrate=bitrate)

    # 예: i=1 일 때 tx_id=0x641, rx_id=0x5C1
    # i=2 일 때 tx_id=0x642, rx_id=0x5C2 ... i=10 일 때 tx_id=0x64A, rx_id=0x5CA
    for i in range(1, 11):
        tx_id = 0x640 + i
        rx_id = 0x5C0 + i
        
        # 송신 데이터: 예제에서는 [0x00, 0x8A] 고정
        # 필요하다면 i값에 따라 데이터 변경 가능
        tx_msg = can.Message(arbitration_id=tx_id, data=[0x00, 0x8A], is_extended_id=False)
        
        # 송신
        print(f"TX (ID: 0x{tx_id:X}) → [0x00, 0x8A]")
        bus.send(tx_msg)
        
        # 수신 대기
        rx_msg = bus.recv(timeout=timeout)
        
        if rx_msg is not None and rx_msg.arbitration_id == rx_id:
            # 예상된 rx_id로 메시지 수신
            print(f"RX (ID: 0x{rx_msg.arbitration_id:X}, DLC: {rx_msg.dlc}) → {rx_msg.data}")
        else:
            # 타임아웃 혹은 다른 ID 메시지를 받았거나, 아예 못 받은 경우
            print(f"RX 타임아웃 또는 기대한 메시지(0x{rx_id:X})가 오지 않음")

    # 필요한 경우 종료 처리
    # (socketcan의 경우 explicit disconnect 필요 없음, 하지만 다른 버스타입 사용시 필요할 수 있음)
    # bus.shutdown()

if __name__ == "__main__":
    test_can_communication()
