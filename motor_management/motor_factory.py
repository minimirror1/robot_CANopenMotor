from ..motor_vendor.motorVendorZeroErr import MotorVendorZeroErr
from ..motor_vendor.motorVenderTemplate import MotorVendorB

# 필요하다면, 제조사 정보를 바탕으로 인스턴스를 생성해주는 Factory 구현 예시
class MotorFactory:
    @staticmethod
    def create_motor(vendor_type, node_id, eds_path, zero_offset=0, operation_mode='PROFILE_POSITION'):
        """모터 객체 생성 팩토리 메서드
        :param vendor_type: 제조사 타입 (예: "VendorZeroErr")
        :param node_id: CAN 노드 ID
        :param eds_path: EDS 파일 경로
        :param zero_offset: 영점 오프셋
        :param operation_mode: 동작 모드 ('PROFILE_POSITION', 'PROFILE_TORQUE' 등)
        """
        if vendor_type == "VendorZeroErr":
            return MotorVendorZeroErr(node_id, eds_path, zero_offset, operation_mode)
        elif vendor_type == "VendorB":
            return MotorVendorB(node_id, eds_path, zero_offset, operation_mode)
        else:
            raise ValueError(f"Unknown vendor type: {vendor_type}")