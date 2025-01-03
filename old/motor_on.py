import time
import canopen

# Common CiA 402 states (for reference):
# 0: Start
# 1: Not Ready to Switch On
# 2: Switch On Disabled
# 3: Ready to Switch On
# 4: Switched On
# 5: Operation Enabled
# 6: Quick Stop Active
# 7: Fault Reaction Active
# 8: Fault

# Bit masks for Controlword (0x6040) commands as per CiA 402 standard (example values):
CW_ENABLE_VOLTAGE    = 0x0006   # (bit 1, 2)
CW_SWITCH_ON         = 0x0007   # (bit 0, 1, 2)
CW_ENABLE_OPERATION  = 0x000F   # (bit 0, 1, 2, 3)
CW_DISABLE_VOLTAGE   = 0x0000
CW_QUICK_STOP        = 0x0002
CW_FAULT_RESET       = 0x0080

# Statusword masks (0x6041) to detect states (may vary by device):
# Check device manual for exact bit patterns.
# Common patterns (not universal, verify with drive manual):
# ST_FAULT             = 0x0008   # bit 3 set = Fault
# ST_SWITCHED_ON       = 0x0004   # bit 2
# ST_READY_TO_SWITCH_ON= 0x0002   # bit 1
# ST_OPERATION_ENABLED = 0x0008   # combined with others means operation
# ST_VOLTAGE_ENABLED   = 0x0010   # bit 4 often used
# ST_QUICK_STOP        = 0x0020   # bit 5
# ST_SWITCH_ON_DISABLED= 0x0040   # bit 6 often used for switch on disabled

ST_READY_TO_SWITCH_ON = 0x0001  # bit0
ST_SWITCHED_ON         = 0x0002  # bit1
ST_OPERATION_ENABLED   = 0x0004  # bit2
ST_FAULT               = 0x0008  # bit3
ST_VOLTAGE_ENABLED     = 0x0010  # bit4
ST_QUICK_STOP          = 0x0020  # bit5
ST_SWITCH_ON_DISABLED  = 0x0040  # bit6


def read_statusword(node):
    return node.sdo[0x6041].raw

def write_controlword(node, value):
    node.sdo[0x6040].raw = value

def wait_for_status(node, condition_func, timeout=5, poll_interval=0.1):
    """Wait until condition_func(statusword) returns True or timeout occurs."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        sw = read_statusword(node)
        if condition_func(sw):
            return True
        time.sleep(poll_interval)
    raise TimeoutError("Timeout waiting for device state.")

def fault_reset(node):
    # Attempt to reset faults
    write_controlword(node, CW_FAULT_RESET)
    time.sleep(0.5)
    # After writing reset, the drive should move to 'Switch on Disabled' if fault was cleared.
    # Wait for that state pattern
    wait_for_status(node, lambda sw: (sw & ST_SWITCH_ON_DISABLED) == ST_SWITCH_ON_DISABLED)

def transition_to_switch_on_disabled(node):
    # 현재 상태워드 읽기
    current_status = read_statusword(node)
    
    # 이미 Switch On Disabled 상태인지 확인
    if (current_status & ST_SWITCH_ON_DISABLED) == ST_SWITCH_ON_DISABLED:
        return
    
    # Fault 상태인 경우 먼저 해결
    if (current_status & ST_FAULT) == ST_FAULT:
        fault_reset(node)
        
    # 전압 비활성화 명령으로 Switch On Disabled 상태로 전환
    write_controlword(node, CW_DISABLE_VOLTAGE)
    
    # Switch On Disabled 상태가 될 때까지 대기
    wait_for_status(node, lambda sw: (sw & ST_SWITCH_ON_DISABLED) == ST_SWITCH_ON_DISABLED)

def transition_to_ready_to_switch_on(node):
    # Enable voltage (bit1)
    write_controlword(node, CW_ENABLE_VOLTAGE)
    # Wait for ready to switch on
    wait_for_status(node, lambda sw: (sw & ST_READY_TO_SWITCH_ON) == ST_READY_TO_SWITCH_ON)

def transition_to_switched_on(node):
    # Switch on (bit0,1,2)
    write_controlword(node, CW_SWITCH_ON)
    # Wait for switched on
    wait_for_status(node, lambda sw: (sw & ST_SWITCHED_ON) == ST_SWITCHED_ON)

def transition_to_operation_enabled(node):
    # Enable operation (bit0,1,2,3)
    write_controlword(node, CW_ENABLE_OPERATION)
    # Wait for operation enabled
    def is_op_enabled(sw):
        # Typically operation enabled state is indicated by a combination of bits
        # For many drives, operation enabled means bits: ReadyToSwitchOn, SwitchedOn, and OperationEnabled are set.
        # Check your drive’s manual. For example (just a guess):
        # Operation Enabled state often sets ReadyToSwitchOn(0x0021), SwitchedOn(0x0023), and OperationEnabled bit as well.
        # Here we just assume the drive sets a known pattern, or you can decode it precisely.
        # A common pattern: statusword & 0x6F == 0x27 (for example) or check dedicated Operation Enabled bit pattern.
        # Adjust the check as needed.
        # Let's say operation enabled is indicated if both ReadyToSwitchOn and SwitchedOn bits are set and no fault:
        return ((sw & ST_READY_TO_SWITCH_ON) and (sw & ST_SWITCHED_ON) and not (sw & ST_FAULT))
    wait_for_status(node, is_op_enabled)

def switch_to_operational(network, timeout=5):
    """
    주어진 CANopen 네트워크를 NMT Operational 상태로 전이시키는 함수.
    1. 네트워크가 이미 Operational이면 바로 리턴
    2. Operational이 아니라면 Pre-Operational로 전환 (필요한 경우)
    3. Operational로 전환 명령 전송 (0x01)
    4. 상태 변경 확인 후 반환

    Parameters:
        network (canopen.Network): CANopen 네트워크 객체
        timeout (float): 상태 전이 확인용 타임아웃 (초 단위)

    Raises:
        TimeoutError: 상태 전이가 제한 시간 내에 완료되지 않은 경우
    """


    # 현재 상태 확인
    current_state = network.nmt.state
    print(f"Current NMT state: {current_state}")

    # 이미 Operational이면 그냥 반환
    if current_state == "OPERATIONAL":
        print("Already in OPERATIONAL state.")
        return

    # Pre-Operational 상태가 아니라면 Pre-Operational로 전환
    # 대부분 Operational 가기 전 Pre-Operational 상태를 거치는 것이 일반적
    if current_state != "PRE-OPERATIONAL":
        print("Switching to PRE-OPERATIONAL...")
        network.nmt.send_command(0x80)  # 0x80: Switch to PRE-OP
        # 상태 변화를 기다림
        start_time = time.time()
        while time.time() - start_time < timeout:
            if network.nmt.state == "PRE-OPERATIONAL":
                break
            time.sleep(0.1)
        else:
            raise TimeoutError("Failed to switch to PRE-OPERATIONAL within timeout.")

    # 이제 Operational로 전환
    print("Switching to OPERATIONAL...")
    network.nmt.send_command(0x01)  # 0x01: Switch to OPERATIONAL

    # 상태 변화를 기다림
    start_time = time.time()
    while time.time() - start_time < timeout:
        if network.nmt.state == "OPERATIONAL":
            print("Now in OPERATIONAL state.")
            return
        time.sleep(0.1)

    # 시간 내 상태 전이 실패 시 예외 발생
    raise TimeoutError("Failed to switch to OPERATIONAL within timeout.")


def main():
    network = None
    try:
        # 네트워크 연결
        network = canopen.Network()
        network.connect(bustype='socketcan', channel='can0', bitrate=1000000)
        
        # 노드 추가
        node_id = 2
        node = network.add_node(node_id, 'config/ZeroErr Driver_V1.5.eds')

        
        # Switch to STOP
        network.nmt.send_command(0x02)
        time.sleep(0.1)

        # Reset communication
        network.nmt.send_command(0x82)
        time.sleep(0.1)


        



        #########################################################
        # 0x6060 00h Modes of operation
        node.sdo['Modes of operation'].raw = 0x01  # Profile Position Mode
        print(f"[write] Modes of operation: 0x01 Profile Position Mode")
        # 읽기만 수행
        display_mode = node.sdo['Modes of operation display'].raw
        print(f"[read] Modes of operation display: {display_mode}")

        # 0x6060 01h Profile velocity
        node.sdo['Profile velocity'].raw = 262144
        print(f"[write] Profile velocity: 262144")        
        print(f"[read] Profile velocity display: {node.sdo['Profile velocity'].raw}")

        # 0x6060 02h Profile acceleration
        node.sdo['Profile acceleration'].raw = 262144
        print(f"[write] Profile acceleration: 262144")
        print(f"[read] Profile acceleration display: {node.sdo['Profile acceleration'].raw}")

        # 0x6060 03h Profile deceleration
        node.sdo['Profile deceleration'].raw = 262144
        print(f"[write] Profile deceleration: 262144")
        print(f"[read] Profile deceleration display: {node.sdo['Profile deceleration'].raw}")

        node.network.sync.stop()

        # Operational 상태로 전환
        switch_to_operational(network)
        time.sleep(0.1)  # 상태 전환 안정화 대기



        # 초기 상태 확인
        initial_sw = read_statusword(node)
        print(f"초기 상태워드: 0x{initial_sw:04X}")

        # Fault 상태 확인 및 리셋
        if (initial_sw & ST_FAULT) == ST_FAULT:
            print("Fault 감지됨, 리셋 시도 중...")
            fault_reset(node)
            print("Fault 리셋 완료")



        
        # 상태 머신 전이
        # print("'Switch On Disabled' 상태로 전환 중...")
        # transition_to_switch_on_disabled(node)

        print("'Shutdown' 상태로 전환 중...")
        node.sdo['Controlword'].phys = 0x06
        
        print("'Ready to Switch On' 상태로 전환 중...")
        transition_to_ready_to_switch_on(node)
        
        print("'Switched On' 상태로 전환 중...")
        transition_to_switched_on(node)
        
        print("'Operation Enabled' 상태로 전환 중...")
        transition_to_operation_enabled(node)
        print("'Operation Enabled' 상태 도달. 드라이브 준비 완료.")

        # 현재 nmt 상태 출력
        print(f"현재 NMT 상태: {network.nmt.state}")

        # 현재 상태워드 출력
        print(f"현재 상태워드: 0x{read_statusword(node):04X}")



        # 목표 위치 설정
        """
                
        node.sdo['Controlword'].phys = 0x2f  # 위치 이동 명령
        node.sdo['Target Position'].phys = 1000000
        node.sdo['Controlword'].phys = 0x3f  # 위치 이동 명령

        node.sdo['Controlword'].phys = 0x2f  # 위치 이동 명령
        node.sdo['Target Position'].phys = 1000000
        node.sdo['Controlword'].phys = 0x3f  # 위치 이동 명령
        """

        # 5초 동안 1초 간격으로 상태워드 체크
        for i in range(5):
           #print(f"현재 상태워드: 0x{read_statusword(node):04X}")
            time.sleep(1)

        node.sdo['Controlword'].phys = 0x2f  # 위치 이동 명령
        node.sdo['Target Position'].phys = 1000000
        node.sdo['Controlword'].phys = 0x3f  # 위치 이동 명령

        # 5초 동안 1초 간격으로 상태워드 체크
        for i in range(5):
            #print(f"현재 상태워드: 0x{read_statusword(node):04X}")
            time.sleep(1)


    except TimeoutError as e:
        print(f"타임아웃 발생: {e}")
        raise
    except Exception as e:
        print(f"예상치 못한 에러 발생: {e}")
        raise
    finally:
        if network:
            network.disconnect()

if __name__ == "__main__":
    main()
