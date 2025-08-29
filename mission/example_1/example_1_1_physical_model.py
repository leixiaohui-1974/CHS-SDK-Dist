import math
import sys
import os

# Add the project root to the Python path
# This is necessary for the script to find the 'core_lib' module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core_lib.physical_objects.canal import Canal
from core_lib.physical_objects.gate import Gate

def run_physical_model_example():
    """
    Demonstrates the dynamic behavior of pure physical components (Canal and Gate)
    in a manually controlled simulation loop.
    """
    print("--- 示例 1.1: 本体仿真智能体（物理模型） ---")
    print("--- 演示纯物理组件（渠道和闸门）的动态行为 ---")

    # 1. 初始化物理组件
    # 渠池参数
    canal_params = {
        'bottom_width': 20.0,   # 渠底宽度 (m)
        'length': 1000.0,       # 渠道长度 (m)
        'slope': 0.001,         # 坡度
        'side_slope_z': 2.0,    # 边坡系数 (z:1)
        'manning_n': 0.025      # 曼宁糙率系数
    }
    # 初始状态
    initial_canal_state = {
        'volume': 50000,        # 初始蓄水量 (m^3)
        'water_level': 2.0,     # 初始水位 (m) - 将由蓄水量重新计算
        'outflow': 0            # 初始出流量 (m^3/s)
    }
    upstream_canal = Canal(
        name="upstream_canal",
        initial_state=initial_canal_state,
        parameters=canal_params
    )

    # 闸门参数
    gate_params = {
        'discharge_coefficient': 0.8, # 流量系数
        'width': 10.0,                # 闸门宽度 (m)
        'max_opening': 3.0,           # 最大开度 (m)
        'max_rate_of_change': 0.1     # 开度最大变化速率 (m/s)
    }
    # 初始状态
    initial_gate_state = {
        'opening': 0.2, # 初始开度，保持固定 (m) - 调整此值使系统接近初始平衡
        'outflow': 0
    }
    control_gate = Gate(
        name="control_gate",
        initial_state=initial_gate_state,
        parameters=gate_params
    )

    # 2. 仿真循环设置
    dt = 10.0  # 时间步长 (s)
    duration = 1000  # 仿真总时长 (s)
    num_steps = int(duration / dt)

    inflow = 10.0  # 初始入流量 (m^3/s)

    # 存储历史数据用于验证
    history = []

    print(f"\n开始仿真... 时长: {duration}s, 步长: {dt}s")
    print(f"初始入流: {inflow} m^3/s, 闸门开度固定为: {initial_gate_state['opening']} m")

    for i in range(num_steps):
        current_time = i * dt

        # 3. 在仿真一半时，模拟一个阶跃式入流变化
        if current_time >= duration / 2:
            inflow = 20.0

        # 4. 手动推进仿真步骤

        # a. 获取渠池当前水位作为闸门的上游水头
        canal_state = upstream_canal.get_state()
        canal_water_level = canal_state['water_level']

        # b. 调用 control_gate.step() 计算其出流量
        #    假设闸门下游直接排放到大气，下游水头为0
        #    闸门开度在此示例中是固定的，所以 control_signal 不重要
        gate_action = {
            'upstream_head': canal_water_level,
            'downstream_head': 0,
            'control_signal': initial_gate_state['opening'] # 保持开度不变
        }
        gate_state = control_gate.step(gate_action, dt)
        gate_outflow = gate_state['outflow']

        # c. 使用闸门计算出的出流量来手动更新渠池的蓄水量
        #    这是关键一步，绕过了 Canal.step() 中不准确的出流计算
        canal_volume = canal_state['volume']
        new_canal_volume = canal_volume + (inflow - gate_outflow) * dt
        new_canal_volume = max(0, new_canal_volume) # 确保水量不为负

        # d. 根据更新后的蓄水量，重新计算渠池的水位
        #    这部分逻辑复制自 Canal.step() 方法
        L = upstream_canal.length
        b = upstream_canal.bottom_width
        z = upstream_canal.side_slope_z

        # V = L * (b*y + z*y^2) -> z*y^2 + b*y - V/L = 0
        c_quad = -new_canal_volume / L if L > 0 else 0

        if z == 0: # 矩形渠道
            new_water_level = new_canal_volume / (b * L) if (b * L) > 0 else 0
        else: # 梯形渠道
            discriminant = b**2 - 4 * z * c_quad
            if discriminant >= 0:
                new_water_level = (-b + math.sqrt(discriminant)) / (2 * z)
            else:
                new_water_level = 0

        # 手动更新渠池状态
        new_canal_state = {
            'volume': new_canal_volume,
            'water_level': new_water_level,
            'outflow': gate_outflow # 渠池的实际出流等于闸门出流
        }
        upstream_canal.set_state(new_canal_state)

        # 5. 记录并打印状态
        step_data = {
            'time': current_time,
            'inflow': inflow,
            'canal_water_level': new_water_level,
            'canal_volume': new_canal_volume,
            'gate_outflow': gate_outflow
        }
        history.append(step_data)

        if i % 10 == 0:
            print(f"Time: {current_time:5.1f}s | Inflow: {inflow:5.2f} | "
                  f"Canal Level: {new_water_level:5.3f}m | Gate Outflow: {gate_outflow:5.3f} m^3/s")

    print("\n仿真结束。")

    # 6. 验证结果
    print("\n--- 结果验证 ---")
    level_before_change = history[int(num_steps / 2) - 1]['canal_water_level']
    level_after_change = history[-1]['canal_water_level']
    outflow_before_change = history[int(num_steps / 2) - 1]['gate_outflow']
    outflow_after_change = history[-1]['gate_outflow']

    print(f"入流变化前稳定水位: {level_before_change:.3f} m")
    print(f"入流变化前稳定出流: {outflow_before_change:.3f} m^3/s")
    print(f"入流变化后稳定水位: {level_after_change:.3f} m")
    print(f"入流变化后稳定出流: {outflow_after_change:.3f} m^3/s")

    # 简单断言
    assert level_after_change > level_before_change, "入流增加后，水位应该上升"
    assert outflow_after_change > outflow_before_change, "入流增加后，出流应该增加"
    print("\n验证成功：水位和出流对入流变化做出了正确响应。")


if __name__ == "__main__":
    run_physical_model_example()
