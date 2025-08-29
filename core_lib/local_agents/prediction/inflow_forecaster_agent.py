"""
一个能提供“完美”预测的预测智能体，用于演示目的。
"""
from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from typing import Dict, Any, List

class InflowForecasterAgent(Agent):
    """
    一个演示用的预测智能体，它能“预知”未来的事件。

    这个智能体模拟了一个完美的预测器。它知道扰动事件（如模拟的降雨）
    何时会发生、持续多久以及强度如何。在每个时间步，它都会发布一个
    未来入流的预测序列，供MPC等前瞻性控制器使用。
    """

    def __init__(self, agent_id: str, message_bus: MessageBus, config: Dict[str, Any]):
        """
        初始化 InflowForecasterAgent.

        参数:
            agent_id: 此智能体的唯一ID。
            message_bus: 系统的消息总线。
            config: 包含预测参数的字典:
                - forecast_topic: 用于发布预测的主题。
                - disturbance_start_time: 扰动开始的仿真时间。
                - disturbance_duration: 扰动事件的持续时间（秒）。
                - disturbance_inflow_rate: 扰动期间的入流率 (m^3/s)。
                - prediction_horizon: 预测未来多少个时间步。
                - dt: 仿真的时间步长（秒）。
        """
        super().__init__(agent_id)
        self.bus = message_bus
        self.forecast_topic = config["forecast_topic"]
        self.start_time = config["disturbance_start_time"]
        self.duration = config["disturbance_duration"]
        self.inflow_rate = config["disturbance_inflow_rate"]
        self.horizon = config["prediction_horizon"]
        self.dt = config["dt"]
        self.end_time = self.start_time + self.duration

        print(f"InflowForecasterAgent '{self.agent_id}' created. Will publish perfect forecasts to '{self.forecast_topic}'.")

    def run(self, current_time: float):
        """
        生成并发布对未来入流的完美预测。
        """
        # 创建一个长度为 horizon 的预测列表
        forecast_sequence: List[float] = [0.0] * self.horizon

        # 根据当前时间填充预测序列
        for i in range(self.horizon):
            future_time = current_time + (i * self.dt)
            if self.start_time <= future_time < self.end_time:
                forecast_sequence[i] = self.inflow_rate

        # 将预测发布到消息总线
        forecast_message: Message = {'inflow_forecast': forecast_sequence}
        self.bus.publish(self.forecast_topic, forecast_message)
