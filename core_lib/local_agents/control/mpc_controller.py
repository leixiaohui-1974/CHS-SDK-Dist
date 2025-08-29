"""
一个模型预测控制（MPC）控制器。
"""
import numpy as np
from scipy.optimize import minimize
from typing import Dict, Any, List
from collections import deque
from core_lib.core.interfaces import Controller, State

class MPCController(Controller):
    """
    一个增强的模型预测控制器，使用积分-时滞（ID）模型进行系统预测，
    依据“现地MPC”的设计文档进行实现。
    """

    def __init__(self, horizon: int, dt: float, config: Dict[str, Any]):
        """
        初始化MPC控制器。

        参数:
            horizon: 向前看的时间步数（预测时域）。
            dt: 仿真时间步长（秒）。
            config: 包含MPC参数的字典：
                - target_level: 期望的水位。
                - q_weight: 偏离目标水位的权重（成本）。
                - r_weight: 控制动作大小/变化的权重（成本）。
                - bounds: 控制动作的元组（最小值, 最大值）。
                - id_model_gain (K): 积分-时滞模型的增益。
                - id_model_delay_steps (tau): 以离散步数表示的时间延迟。
        """
        self.horizon = horizon
        self.dt = dt
        self.target_level = config["target_level"]
        self.q_weight = config.get("q_weight", 1.0)
        self.r_weight = config.get("r_weight", 0.1)
        self.bounds = config.get("bounds", (0, 1))

        # ID模型参数
        self.K = config["id_model_gain"]
        self.tau = int(config["id_model_delay_steps"]) # 以步数表示的延迟

        # 存储控制动作历史以处理延迟
        self.control_history = deque([0.0] * self.tau, maxlen=self.tau)

    def _objective_function(self, control_sequence: np.ndarray,
                            current_level: float,
                            disturbance_forecast: List[float],
                            past_controls: List[float]) -> float:
        """
        要最小化的函数。使用ID模型计算给定控制序列的总成本。
        """
        cost = 0.0
        predicted_level = current_level

        # 用于预测的完整控制输入序列包括历史动作和新的候选序列。
        full_control_input = past_controls + list(control_sequence)

        num_steps = min(len(control_sequence), len(disturbance_forecast))

        for i in range(num_steps):
            # 影响当前步骤'i'的控制动作是在'tau'个步骤前执行的。
            # 索引是 i + tau (对于past_controls) - tau = i
            effective_control_action = full_control_input[i]

            # ID模型：水位的变化与延迟的控制动作成正比，减去任何外部扰动（例如，预测的出流量/需求）。
            change_in_level = self.K * effective_control_action - disturbance_forecast[i]

            predicted_level += change_in_level * self.dt

            # 成本计算
            # 1. 偏离目标水位的成本
            cost += self.q_weight * ((predicted_level - self.target_level) ** 2)

            # 2. 控制动作大小的成本
            cost += self.r_weight * (control_sequence[i] ** 2)

        return cost

    def compute_control_action(self, observation: State, dt: float) -> Any:
        """
        使用带有ID模型的MPC计算最优控制动作。
        """
        current_level = observation.get("water_level")
        # 'disturbance_forecast'可以是净入流量（入流量 - 基础出流量）或类似值
        disturbance_forecast = observation.get("disturbance_forecast", [0.0] * self.horizon)

        if current_level is None:
            raise ValueError("观测值必须包含'water_level'。")

        # 确保预测与时域长度匹配
        if len(disturbance_forecast) < self.horizon:
            last_value = disturbance_forecast[-1] if disturbance_forecast else 0
            disturbance_forecast.extend([last_value] * (self.horizon - len(disturbance_forecast)))

        initial_guess = np.zeros(self.horizon)
        bnds = [self.bounds] * self.horizon

        # 传递模拟延迟所需的控制历史
        past_controls_for_prediction = list(self.control_history)

        result = minimize(
            self._objective_function,
            initial_guess,
            args=(current_level, disturbance_forecast, past_controls_for_prediction),
            method='SLSQP',
            bounds=bnds
        )

        optimal_action = result.x[0] if result.success else initial_guess[0]

        # 用选择的动作更新控制历史
        self.control_history.append(optimal_action)

        return {'opening': float(optimal_action)}
