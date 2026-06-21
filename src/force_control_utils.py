#!/usr/bin/env python3
"""
Force Feedback Visualization and Robustness Test Suite
力反馈可视化和鲁棒性测试套件
"""

import numpy as np
import time


def draw_sensor_overlay(frame, force_data: np.ndarray, task_info: dict = None):
    """
    将力数据实时绘制在渲染图像上

    Args:
        frame: 输入视频帧
        force_data: 力传感器数据 (magnitude in N)
        task_info: 任务信息字典

    Returns:
        绘制了力反馈可视化数据的帧
    """
    try:
        import cv2
    except ImportError:
        return frame

    height, width = frame.shape[:2]
    overlay = frame.copy()

    # 力大小可视化
    force_magnitude = np.linalg.norm(force_data) if hasattr(force_data, '__len__') else abs(force_data)

    # 力条颜色：绿色(正常) -> 黄色(警告) -> 红色(过载)
    if force_magnitude < 3.0:
        bar_color = (0, 255, 0)  # 绿色
    elif force_magnitude < 6.0:
        bar_color = (0, 255, 255)  # 黄色
    else:
        bar_color = (0, 0, 255)  # 红色

    # 力反馈条
    bar_length = int(np.clip(force_magnitude * 15, 0, width - 20))
    cv2.rectangle(overlay, (10, 10), (10 + bar_length, 30), bar_color, -1)
    cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)

    # 力反馈标签
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(frame, f"Force: {force_magnitude:.2f}N", (15, 50),
                font, 0.5, (255, 255, 255), 1)

    # 绘制力向量指示器
    center_x, center_y = width // 2, height // 2
    arrow_length = int(np.clip(force_magnitude * 3, 0, 100))

    if hasattr(force_data, '__len__') and len(force_data) >= 2:
        dx = int(force_data[0] * 10)
        dy = int(force_data[1] * 10)
        cv2.arrowedLine(frame, (center_x, center_y),
                       (center_x + dx, center_y + dy),
                       bar_color, 2)

    # 阈值线
    cv2.putText(frame, f"Threshold: 3.0N", (15, 75),
                font, 0.4, (200, 200, 200), 1)

    # 如果有力干扰，显示警告
    if force_magnitude > 3.0:
        warning_text = "DISTURBANCE DETECTED - CORRECTING"
        cv2.rectangle(frame, (width // 2 - 150, height - 80),
                     (width // 2 + 150, height - 40), (0, 0, 0), -1)
        cv2.putText(frame, warning_text, (width // 2 - 140, height - 55),
                   font, 0.5, (0, 0, 255), 1)

    # 任务信息（如果提供）
    if task_info:
        y_offset = height - 120
        for key, value in task_info.items():
            text = f"{key}: {value}"
            cv2.putText(frame, text, (width - 200, y_offset),
                       font, 0.4, (255, 255, 255), 1)
            y_offset -= 20

    return frame


def test_robustness_with_perturbation(env, model, data, steps: int = 100,
                                       perturbation_force: float = 3.0,
                                       perturbation_step: int = 50):
    """
    模拟外部扰动测试

    Args:
        env: MuJoCo环境
        model: MuJoCo模型
        data: MuJoCo数据
        steps: 测试步数
        perturbation_force: 扰动力大小 (N)
        perturbation_step: 在哪一步施加扰动

    Returns:
        dict: 测试结果统计
    """
    print("\n" + "=" * 60)
    print(f"鲁棒性测试 - 扰动力: {perturbation_force}N @ step {perturbation_step}")
    print("=" * 60)

    success_count = 0
    disturbance_detected = False
    recovery_time = None
    start_time = data.time

    for i in range(steps):
        # 在指定步数施加扰动
        if i == perturbation_step:
            # 在X方向施加侧向扰动力
            if hasattr(data, 'qfrc_applied'):
                data.qfrc_applied[6:9] = [perturbation_force, 0.0, 0.0]
            disturbance_detected = True
            print(f"[Step {i}] 施加扰动力: {perturbation_force}N")

        # 物理仿真步骤
        try:
            import mujoco
            mujoco.mj_step(model, data)
        except:
            pass

        # 检查物体稳定性
        if disturbance_detected:
            # 计算与目标位置的偏差
            if hasattr(data, 'qpos'):
                pos_error = np.linalg.norm(data.qpos[:3])
                if pos_error < 0.05:  # 5cm阈值内认为恢复
                    if recovery_time is None:
                        recovery_time = data.time - start_time - (perturbation_step * model.opt.timestep)
                        success_count += 1
                        print(f"[Step {i}] 恢复成功! 恢复时间: {recovery_time:.3f}s")

    # 计算最终统计
    total_time = (data.time - start_time)
    success_rate = (success_count / max(1, disturbance_detected)) * 100

    print("-" * 60)
    print(f"测试完成:")
    print(f"  扰动检测: {'是' if disturbance_detected else '否'}")
    print(f"  成功恢复: {success_count}")
    print(f"  成功率: {success_rate:.1f}%")
    if recovery_time is not None:
        print(f"  恢复时间: {recovery_time:.3f}s")
    print("=" * 60)

    return {
        'success_count': success_count,
        'success_rate': success_rate,
        'recovery_time': recovery_time if recovery_time else 0.0,
        'disturbance_detected': disturbance_detected
    }


def run_force_control_demo(model, data, duration: float = 10.0):
    """
    运行力反馈闭环控制演示

    Args:
        model: MuJoCo模型
        data: MuJoCo数据
        duration: 演示时长 (秒)

    Returns:
        dict: 性能统计
    """
    from src.controller import ForceFeedbackClosedLoopController

    print("\n" + "=" * 60)
    print("力反馈闭环控制演示")
    print("=" * 60)

    # 初始化控制器
    controller = ForceFeedbackClosedLoopController(model, data)

    start_time = time.time()
    step_count = 0
    disturbance_count = 0
    force_readings = []

    print("开始力反馈闭环控制...")

    while (time.time() - start_time) < duration:
        # 更新控制器
        result = controller.update(dt=0.001)

        # 记录数据
        force_readings.append(result['force_magnitude'])

        if result['disturbance_detected']:
            disturbance_count += 1

        # 打印进度
        if step_count % 1000 == 0:
            elapsed = time.time() - start_time
            print(f"  时间: {elapsed:.1f}s | "
                  f"力: {result['force_magnitude']:.2f}N | "
                  f"门控: {'闭合' if result['all_gates_closed'] else '开启'}")

        step_count += 1

        # 每50秒模拟一次干扰
        if step_count == 50000:
            print(f"\n[{time.time() - start_time:.1f}s] 模拟干扰测试...")
            # 模拟外部干扰
            if hasattr(data, 'qfrc_applied'):
                data.qfrc_applied[6:9] = [5.0, 0.0, 0.0]

    # 获取性能摘要
    summary = controller.get_performance_summary()

    print("\n" + "=" * 60)
    print("力反馈闭环控制演示完成")
    print("=" * 60)
    print(f"总步数: {step_count}")
    print(f"总干扰次数: {disturbance_count}")
    print(f"控制器检测干扰: {summary['total_disturbances']}")
    print(f"任务成功率: {summary['success_rate']:.1f}%")
    print(f"平均恢复时间: {summary['avg_recovery_time']:.4f}s")
    print(f"峰值力: {max(force_readings):.2f}N")
    print(f"平均力: {np.mean(force_readings):.2f}N")
    print("=" * 60)

    return {
        'step_count': step_count,
        'disturbance_count': disturbance_count,
        'success_rate': summary['success_rate'],
        'avg_recovery_time': summary['avg_recovery_time'],
        'peak_force': max(force_readings),
        'avg_force': np.mean(force_readings)
    }


def create_force_logger():
    """创建力反馈日志记录器"""
    log_entries = []

    def log_event(event_type: str, data: dict):
        entry = {
            'timestamp': time.time(),
            'type': event_type,
            'data': data
        }
        log_entries.append(entry)

    def get_summary():
        if not log_entries:
            return "无日志记录"

        disturbance_events = [e for e in log_entries if e['type'] == 'disturbance']
        recovery_events = [e for e in log_entries if e['type'] == 'recovery']

        summary = f"日志摘要:\n"
        summary += f"  总事件数: {len(log_entries)}\n"
        summary += f"  干扰事件: {len(disturbance_events)}\n"
        summary += f"  恢复事件: {len(recovery_events)}\n"

        if recovery_events:
            recovery_times = [e['data'].get('recovery_time', 0) for e in recovery_events]
            summary += f"  平均恢复时间: {np.mean(recovery_times):.4f}s\n"

        return summary

    return log_event, get_summary


if __name__ == '__main__':
    # 测试代码
    print("力反馈可视化和鲁棒性测试套件")
    print("使用说明:")
    print("  1. from src.force_control_utils import draw_sensor_overlay")
    print("  2. 在渲染循环中调用: frame = draw_sensor_overlay(frame, force_data)")
    print("  3. 使用 test_robustness_with_perturbation() 进行鲁棒性测试")
    print("  4. 使用 run_force_control_demo() 运行力反馈演示")