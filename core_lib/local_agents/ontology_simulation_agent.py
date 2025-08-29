import random
import time
from ..core.interfaces import Agent
from ..central_coordination.collaboration.message_bus import MessageBus


class OntologySimulationAgent(Agent):
    """
    1. 本体仿真智能体
    作为高保真的虚拟物理世界，为其他智能体提供“真实”的仿真环境。
    """
    def __init__(self, agent_id: str, broker: MessageBus, initial_state: dict):
        super().__init__(agent_id)
        self.broker = broker
        # 物理状态
        self.upstream_level = initial_state.get('upstream_level', 5.0)  # m
        self.downstream_level = initial_state.get('downstream_level', 4.5) # m
        self.channel_surface_area = 10000  # m^2
        self.inflow = initial_state.get('inflow', 10)  # m^3/s, 上游入流

        # 闸门执行器状态
        self.gate_opening = 0.5  # 0 to 1 (0% to 100%)
        self.gate_flow = 0
        self.target_gate_opening = self.gate_opening
        self.max_gate_speed = 0.05  # 5% per second
        self.gate_flow_coefficient = 20 # 流量系数

        # 订阅控制指令
        self.broker.subscribe("gate_control_command", self._handle_gate_command)

        # 扰动注入
        self.side_inflow = 0

    def _handle_gate_command(self, message):
        """处理来自控制智能体的闸门开度指令。"""
        self.target_gate_opening = message.get('target_opening', self.target_gate_opening)
        # print(f"SIMULATOR: Received new target gate opening: {self.target_gate_opening:.2f}")

    def run_step(self, time_step: int):
        # --- 1. 执行器仿真 ---
        # 模拟闸门开度的变化，考虑最大速度限制
        error = self.target_gate_opening - self.gate_opening
        delta = min(abs(error), self.max_gate_speed * 1) # dt=1s
        if error > 0:
            self.gate_opening += delta
        else:
            self.gate_opening -= delta
        self.gate_opening = max(0, min(1, self.gate_opening)) # 限制在[0, 1]

        # --- 2. 水动力学仿真 ---
        # 简化水动力学模型
        # a. 计算过闸流量 (简化的堰流公式)
        head_diff = self.upstream_level - self.downstream_level
        if head_diff > 0 and self.gate_opening > 0:
            self.gate_flow = self.gate_flow_coefficient * self.gate_opening * (head_diff ** 0.5)
        else:
            self.gate_flow = 0

        # b. 更新上下游水位 (质量平衡)
        # 假设上游水位受总入流和过闸流量影响，下游水位受过闸流量和某个固定出流影响
        self.upstream_level += (self.inflow - self.gate_flow) * 1 / self.channel_surface_area
        # 为了简化，我们让下游渠道也有一个恒定的出流，使其水位也能动态变化
        downstream_outflow = 8
        self.downstream_level += (self.gate_flow + self.side_inflow - downstream_outflow) * 1 / self.channel_surface_area

        # 注入扰动 (例如，在第50步时发生侧向入流)
        if time_step == 50:
            print("\n!!! SIMULATOR: Disturbance injected: side inflow of 5 m^3/s !!!\n")
            self.side_inflow = 5
        if time_step == 100:
            self.side_inflow = 0

        # --- 3. 传感器仿真 ---
        # 为“真实”数据添加噪声
        noise_level = 0.01 # 传感器噪声水平
        simulated_upstream_level = self.upstream_level + random.uniform(-noise_level, noise_level)
        simulated_downstream_level = self.downstream_level + random.uniform(-noise_level, noise_level)
        simulated_inflow = self.inflow + random.uniform(-0.1, 0.1)

        # --- 4. 发布输出 ---
        # 发布原始传感器数据
        sensor_data = {
            'timestamp': time.time(),
            'upstream_level': simulated_upstream_level,
            'downstream_level': simulated_downstream_level,
            'inflow': simulated_inflow
        }
        self.broker.publish("raw_sensor_data", sensor_data)

        # 发布执行器状态
        executor_status = {
            'timestamp': time.time(),
            'actual_opening': self.gate_opening
        }
        self.broker.publish("gate_executor_status", executor_status)

        # 打印真实状态用于验证
        if time_step % 10 == 0:
            print(f"--- Step {time_step}: SIMULATOR STATE ---")
            print(f"  Levels (U/D): {self.upstream_level:.3f}m / {self.downstream_level:.3f}m | Gate Opening: {self.gate_opening:.2%} | Gate Flow: {self.gate_flow:.2f} m^3/s")
