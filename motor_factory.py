from motor_vendor.motorVendorZeroErr import MotorVendorZeroErr
from motor_vendor.motorVenderTemplate import MotorVendorB

# 필요하다면, 제조사 정보를 바탕으로 인스턴스를 생성해주는 Factory 구현 예시
class MotorFactory:
    @staticmethod
    def create_motor(vendor, node_id, eds_path, zero_offset=0):
        if vendor == "VendorZeroErr":
            return MotorVendorZeroErr(node_id, eds_path, zero_offset)
        elif vendor == "VendorB":
            return MotorVendorB(node_id, eds_path, zero_offset)
        else:
            raise ValueError(f"Unknown vendor type: {vendor}")