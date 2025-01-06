from abc import ABC, abstractmethod

class AbstractMotor(ABC):
    """모든 모터가 공통으로 가져야 할 인터페이스 정의(추상 클래스)."""

    def __init__(self, node_id, eds_path, zero_offset=0):
        self.node_id = node_id
        self.eds_path = eds_path
        self.node = None  # canopen에서 로드되는 노드 객체 (초기에는 None)
        self.network = None  # network 객체 추가
        # 목표 위치와 현재 위치를 저장하는 변수 추가
        self.zero_offset = zero_offset
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

    def set_zero_offset(self, value):
        """Zero Offset 변경"""
        self.zero_offset = value
        pass

    def get_zero_offset(self):
        """Zero Offset 조회"""
        return self.zero_offset
    
    @abstractmethod
    def pdo_callback_register(self):
        """PDO 콜백 등록"""
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

