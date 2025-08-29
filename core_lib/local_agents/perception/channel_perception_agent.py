import time
from collections import deque

from ...core.interfaces import Agent
from ...central_coordination.collaboration.message_bus import MessageBus


class ChannelPerceptionAgent(Agent):
    """
    2. 渠道感知智能体 (分布式孪生)
    将渠道本体仿真模型转化为具备自我认知、诊断、辨识和预测能力的孪生体。
    """
    def __init__(self, agent_id: str, broker: MessageBus, channel_id: str):
        super().__init__(agent_id)
        self.broker = broker
        self.channel_id = channel_id

        # 数据缓存和清洗
        self.raw_data_buffer = deque(maxlen=10)
        self.cleaned_downstream_level = None

        # 孪生模型与在线辨识 (ID 模型: y = K * u(t-T))
        self.twin_model = {
            'gain': 0.001,  # (m / m^3/s) - 初始增益估计
            'time_delay': 2, # (steps) - 初始时滞估计
            'manning_coefficient': 0.03 # 初始曼宁系数估计
        }
        self.input_history = deque(maxlen=20) # for time delay
        self.output_history = deque(maxlen=20)

        # 预测与诊断
        self.prediction = None
        self.anomaly_threshold = 0.05 # 5cm

        # 订阅原始传感器数据
        self.broker.subscribe("raw_sensor_data", self._handle_raw_data)
        self.broker.subscribe("gate_executor_status", lambda msg: self.input_history.append(msg['actual_opening'])) # Simplified input

    def _handle_raw_data(self, message):
        """处理并清洗原始传感器数据"""
        self.raw_data_buffer.append(message)
        # 数据清洗 (简单滑动平均)
        if len(self.raw_data_buffer) > 0:
            avg_downstream_level = sum(d['downstream_level'] for d in self.raw_data_buffer) / len(self.raw_data_buffer)
            self.cleaned_downstream_level = avg_downstream_level
            self.output_history.append(self.cleaned_downstream_level)


    def run_step(self, time_step: int):
        if self.cleaned_downstream_level is None or len(self.input_history) < 5 or len(self.output_history) < 5:
            # 等待足够的数据
            return

        # --- 1. 分布式孪生构建与在线辨识 ---
        # 简化的在线系统辨识 (估算增益)
        # 比较 5 步前的输入和现在的输出变化
        if len(self.input_history) > self.twin_model['time_delay'] and len(self.output_history) > 1:
            # 假设时滞为 T 步
            T = self.twin_model['time_delay']
            if len(self.input_history) > T and len(self.output_history) > T:
                # 这是一个非常简化的增益辨识
                delta_output = self.output_history[-1] - self.output_history[-1-T]
                delta_input = self.input_history[-1-T] - self.input_history[-2-T] if len(self.input_history) > T+1 else 0
                if abs(delta_input) > 0.01: # 仅在输入有显著变化时更新
                    estimated_gain = delta_output / delta_input
                    # 平滑更新
                    self.twin_model['gain'] = 0.95 * self.twin_model['gain'] + 0.05 * estimated_gain

        # --- 2. 预测, 诊断与信息发布 ---
        # a. 实时预测
        # 基于ID模型预测下一时刻的水位
        if len(self.input_history) > self.twin_model['time_delay']:
            delayed_input = self.input_history[-self.twin_model['time_delay']]
            # 这是一个简化的积分模型预测: current_level + gain * input
            self.prediction = self.cleaned_downstream_level + self.twin_model['gain'] * delayed_input

        # b. 异常诊断
        if self.prediction is not None:
            deviation = self.cleaned_downstream_level - self.output_history[-2] if len(self.output_history) > 1 else 0
            prediction_based_deviation = self.prediction - self.cleaned_downstream_level

            # 这里我们简化诊断逻辑：如果实际水位远超模型预测，可能存在异常入流
            if abs(prediction_based_deviation) > self.anomaly_threshold:
                anomaly_report = {
                    'timestamp': time.time(),
                    'channel_id': self.channel_id,
                    'type': '水量异常',
                    'message': f"检测到显著偏差！预测水位: {self.prediction:.3f}, 实际水位: {self.cleaned_downstream_level:.3f}. 可能存在偷漏水或异常入流。"
                }
                self.broker.publish("anomaly_reports", anomaly_report)
                print(f"\n!!! CHANNEL PERCEPTION ({self.agent_id}): {anomaly_report['message']} !!!\n")


        # c. 发布信息
        # 发布清洗后的数据
        clean_data = {
            'timestamp': time.time(),
            'channel_id': self.channel_id,
            'downstream_level': self.cleaned_downstream_level
        }
        self.broker.publish("channel_clean_data", clean_data)

        # 发布孪生成果
        twin_data = {
            'timestamp': time.time(),
            'channel_id': self.channel_id,
            'model_type': 'ID-Model',
            'parameters': self.twin_model
        }
        self.broker.publish("channel_twin_model", twin_data)

        if time_step % 10 == 0:
            print(f"--- Step {time_step}: CHANNEL PERCEPTION ({self.agent_id}) ---")
            print(f"  Cleaned Level: {self.cleaned_downstream_level:.3f}m | Predicted Next Level: {self.prediction or 'N/A':.3f} | Identified Gain: {self.twin_model['gain']:.4f}")
