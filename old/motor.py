from abc import ABC, abstractmethod

class Motor(ABC):
    def __init__(self, node_id, channel='can0', eds_path='config/ZeroErr Driver_V1.5.eds'):
        self.node_id = node_id
        self.channel = channel
        self.eds_path = eds_path
        self.position = 0
        self.is_initialized = False
    
    @abstractmethod
    def initialize(self):
        """모터 초기화
        Returns:
            bool: 초기화 성공 여부
        """
        pass

    @abstractmethod
    def reset(self):
        """모터 리셋
        Returns:
            bool: 리셋 성공 여부
        """
        pass

    @abstractmethod
    def pdo_mapping(self):
        """PDO 맵핑 설정
        Returns:
            bool: PDO 맵핑 성공 여부
        """
        pass

    @abstractmethod
    def set_position(self, position):
        """모터 위치 설정
        Args:
            position (int): 목표 위치 값
        Returns:
            bool: 위치 설정 성공 여부
        """
        pass

    @abstractmethod
    def get_position(self):
        """현재 모터 위치 반환
        Returns:
            int: 현재 모터 위치
        """
        pass
