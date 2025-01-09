class AdmittanceController:
    def __init__(self, mass, damping, stiffness):
        self.M = mass          # 가상 질량
        self.B = damping       # 댐핑 계수
        self.K = stiffness     # 강성 계수
        
        self.pos = 0.0         # 현재 위치
        self.vel = 0.0         # 현재 속도
        self.prev_vel = 0.0    # 이전 속도
        
    def compute(self, force, dt, pos, vel):
        # 이전 상태 저장
        self.prev_vel = self.vel
        self.pos = pos
        self.vel = vel
        
        # 가속도를 속도의 변화율로 근사
        acc = (self.vel - self.prev_vel) / dt
        
        # F = M*a + B*v + K*x
        self.acc = force / self.M - (self.B * self.vel + self.K * self.pos) / self.M
        self.vel += self.acc * dt
        self.pos += self.vel * dt
        
        return self.pos 