"""
一个先进的中央调度智能体，使用模型预测控制（MPC）来优化整个系统的操作。
"""
import numpy as np
from scipy.optimize import minimize
from core_lib.core.interfaces import Agent, State
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from typing import Dict, Any, List

class CentralMPCAgent(Agent):
    """
    一个中央调度智能体，它使用MPC来计算最优的水位设定点，以进行分层控制。

    该智能体负责系统的全局优化。它接收来自多个物理组件的状态更新和
    来自预测智能体的扰动预测。然后，它运行一个优化程序来确定一系列
    最优设定点，以发送给本地PID控制器。
    """

    def __init__(self, agent_id: str, message_bus: MessageBus, config: Dict[str, Any]):
        super().__init__(agent_id)
        self.bus = message_bus
        self.config = config

        # MPC 参数
        self.horizon = config["prediction_horizon"]
        self.dt = config["dt"]
        self.q_weight = config["q_weight"]
        self.r_weight = config["r_weight"]
        self.state_keys = config["state_keys"] # e.g., ['upstream_level', 'downstream_level']
        self.command_topics = config["command_topics"] # e.g., {'upstream_cmd': 'topic1', 'downstream_cmd': 'topic2'}
        self.normal_setpoints = np.array(config["normal_setpoints"])
        self.emergency_setpoint = config["emergency_setpoint"]
        self.flood_thresholds = np.array(config["flood_thresholds"])

        # 简化的内部系统模型参数
        self.canal_areas = np.array(config["canal_surface_areas"])
        self.outflow_coeff = config["outflow_coefficient"] # 简化：outflow = C * level

        # 订阅状态和预测
        self.latest_states = {}
        self.latest_forecast = [0.0] * self.horizon
        for key, topic in config["state_subscriptions"].items():
            self.bus.subscribe(topic, lambda msg, k=key: self._handle_state_message(msg, k))
        self.bus.subscribe(config["forecast_subscription"], self._handle_forecast_message)

    def _handle_state_message(self, message: Message, name: str):
        self.latest_states[name] = message.get('water_level', 0)

    def _handle_forecast_message(self, message: Message):
        self.latest_forecast = message.get('inflow_forecast', [0.0] * self.horizon)

    def _objective_function(self, setpoints_sequence: np.ndarray, initial_levels: np.ndarray, forecast: List[float], target_setpoints: np.ndarray) -> float:
        cost = 0.0

        # 将扁平化的设定点序列重塑为 (horizon, num_canals)
        num_canals = len(self.state_keys)
        setpoints = setpoints_sequence.reshape((self.horizon, num_canals))

        predicted_levels = np.copy(initial_levels)

        for i in range(self.horizon):
            # 简化模型：level_change = (inflow - outflow) * dt / area
            inflow_upstream = forecast[i]

            # **修复**: 出流量应与设定点成反比。
            # 设定点越低，PID需要让越多的水流出，因此闸门开度越大/出流量越大。
            # 我们使用一个简化的反比关系。
            outflow_upstream = self.outflow_coeff * (1 / (setpoints[i][0] + 1e-6))

            # 计算上游水位变化
            level_change_upstream = (inflow_upstream - outflow_upstream) * self.dt / self.canal_areas[0]

            # 中游入流是上游出流
            inflow_downstream = outflow_upstream
            outflow_downstream = self.outflow_coeff * (1 / (setpoints[i][1] + 1e-6))

            # 计算中游水位变化
            level_change_downstream = (inflow_downstream - outflow_downstream) * self.dt / self.canal_areas[1]

            predicted_levels += np.array([level_change_upstream, level_change_downstream])

            # 1. 惩罚与 *目标* 设定点的偏差（可以是正常的或紧急的）
            cost += self.q_weight * np.sum((setpoints[i] - target_setpoints)**2)

            # 2. 惩罚控制动作的变化（设定点变化）
            if i > 0:
                cost += self.r_weight * np.sum((setpoints[i] - setpoints[i-1])**2)

            # 3. 严厉惩罚超过洪水阈值的情况
            for j in range(num_canals):
                if predicted_levels[j] > self.flood_thresholds[j]:
                    cost += 1e6 * (predicted_levels[j] - self.flood_thresholds[j])

        return cost

    def run(self, current_time: float):
        if len(self.latest_states) < len(self.state_keys):
            return # 等待所有状态更新

        initial_levels = np.array([self.latest_states[key] for key in self.state_keys])

        # 如果预测显示有大量入流，则激活紧急设定点
        use_emergency_setpoint = any(f > 0 for f in self.latest_forecast)
        target_setpoints = self.normal_setpoints if not use_emergency_setpoint else np.array([self.emergency_setpoint] * len(self.state_keys))

        num_canals = len(self.state_keys)
        # 初始猜测：保持目标设定点不变
        initial_guess = np.tile(target_setpoints, self.horizon)

        # 设定点边界（例如，在2米到6米之间）
        bounds = [(2.0, 6.0)] * len(initial_guess)

        result = minimize(
            self._objective_function,
            initial_guess,
            args=(initial_levels, self.latest_forecast, target_setpoints),
            method='SLSQP',
            bounds=bounds
        )

        if result.success:
            optimal_setpoints_sequence = result.x.reshape((self.horizon, num_canals))
            # 应用序列中的第一个设定点
            first_optimal_setpoints = optimal_setpoints_sequence[0]

            i = 0
            for cmd_topic in self.command_topics.values():
                self.bus.publish(cmd_topic, {'new_setpoint': float(first_optimal_setpoints[i])})
                i += 1
        else:
            # 如果优化失败，则回退到安全/默认行为
            i = 0
            for cmd_topic in self.command_topics.values():
                self.bus.publish(cmd_topic, {'new_setpoint': float(target_setpoints[i])})
                i += 1
