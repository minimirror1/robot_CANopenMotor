class AdmittanceController:
    def __init__(self, mass, damping, stiffness):
        self.M = mass          # 가상 질량 [kg⋅m²]
        self.B = damping       # 댐핑 계수 [N⋅m⋅s/rad]
        self.K = stiffness     # 강성 계수 [N⋅m/rad]
        
        # 엔코더 -> 라디안 변환 상수
        self.COUNTS_PER_REV = 524288
        self.COUNTS_TO_RAD = 2 * 3.141592653589793 / self.COUNTS_PER_REV
        self.RAD_TO_COUNTS = self.COUNTS_PER_REV / (2 * 3.141592653589793)
        
        self.pos_rad = 0.0     # 현재 위치 [rad]
        self.vel_rad = 0.0     # 현재 속도 [rad/s]
        self.prev_vel_rad = 0.0  # 이전 속도 [rad/s]
        
    def compute(self, force, dt, pos_counts, vel_counts):
        """
        어드미턴스 제어 계산
        :param force: 외력 [N⋅m]
        :param dt: 시간 간격 [s]
        :param pos_counts: 현재 위치 [엔코더 카운트]
        :param vel_counts: 현재 속도 [엔코더 카운트/s]
        :return: 목표 위치 [엔코더 카운트]
        """
        # 엔코더 카운트를 라디안으로 변환
        pos_rad = pos_counts * self.COUNTS_TO_RAD
        vel_rad = vel_counts * self.COUNTS_TO_RAD
        
        # 이전 상태 저장
        self.prev_vel_rad = self.vel_rad
        self.pos_rad = pos_rad
        self.vel_rad = vel_rad
        
        # 가속도를 속도의 변화율로 근사 [rad/s²]
        acc_rad = (self.vel_rad - self.prev_vel_rad) / dt
        
        # F = M*a + B*v + K*x (라디안 단위로 계산)
        # 힘의 방향을 반대로 변경 (-force)
        self.acc_rad = -force / self.M - (self.B * self.vel_rad + self.K * self.pos_rad) / self.M
        self.vel_rad += self.acc_rad * dt
        self.pos_rad += self.vel_rad * dt
        
        # 결과를 엔코더 카운트로 변환하여 반환
        target_pos_counts = int(self.pos_rad * self.RAD_TO_COUNTS)
        return target_pos_counts 