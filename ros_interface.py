#!/usr/bin/env python3
"""
ROS 2 接口 - ROS 2 Interface for DexHand
支持 ROS 2 Humble / Iron
"""
import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer
from rclpy.action.server import ServerGoalHandle
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
import numpy as np
import threading


class DexHandROS2Node(Node):
    """DexHand ROS 2 节点"""
    
    def __init__(self):
        super().__init__('dexhand_node')
        
        # 参数声明
        self.declare_parameter('control_rate', 1000.0)  # Hz
        self.declare_parameter('joint_count', 19)
        self.declare_parameter('hand_side', 'right')  # right/left
        
        self.control_rate = self.get_parameter('control_rate').value
        self.joint_count = self.get_parameter('joint_count').value
        
        # 回调组
        self.callback_group = ReentrantCallbackGroup()
        
        # 关节状态
        self.joint_positions = np.zeros(self.joint_count)
        self.joint_velocities = np.zeros(self.joint_count)
        self.joint_torques = np.zeros(self.joint_count)
        self.touch_sensors = np.zeros(5)
        
        # 控制目标
        self.target_positions = np.zeros(self.joint_count)
        self.target_torques = np.zeros(self.joint_count)
        
        # 状态锁
        self.state_lock = threading.Lock()
        
        # 创建ROS 2 接口
        self._create_publishers()
        self._create_subscribers()
        self._create_services()
        self._create_action_servers()
        
        # 定时器
        self.timer = self.create_timer(
            1.0 / self.control_rate,
            self._control_loop,
            callback_group=self.callback_group
        )
        
        self.get_logger().info('DexHand ROS 2 Node initialized')
        self.get_logger().info(f'Control rate: {self.control_rate} Hz')
        self.get_logger().info(f'Joint count: {self.joint_count}')
    
    def _create_publishers(self):
        """创建发布者"""
        from sensor_msgs.msg import JointState
        from geometry_msgs.msg import WrenchStamped
        
        # 关节状态发布者
        self.joint_state_pub = self.create_publisher(
            JointState,
            '/dexhand/joint_states',
            10
        )
        
        # 触觉数据发布者
        self.touch_pub = self.create_publisher(
            Float32MultiArray,
            '/dexhand/touch',
            10
        )
    
    def _create_subscribers(self):
        """创建订阅者"""
        from sensor_msgs.msg import JointState
        
        # 位置命令订阅者
        self.position_sub = self.create_subscription(
            JointState,
            '/dexhand/command/position',
            self._position_command_callback,
            10,
            callback_group=self.callback_group
        )
        
        # 力矩命令订阅者
        self.torque_sub = self.create_subscription(
            JointState,
            '/dexhand/command/torque',
            self._torque_command_callback,
            10,
            callback_group=self.callback_group
        )
    
    def _create_services(self):
        """创建服务"""
        from std_srvs.srv import Trigger
        
        # 归零服务
        self.calibrate_srv = self.create_service(
            Trigger,
            '/dexhand/calibrate',
            self._calibrate_callback,
            callback_group=self.callback_group
        )
        
        # 停止服务
        self.stop_srv = self.create_service(
            Trigger,
            '/dexhand/stop',
            self._stop_callback,
            callback_group=self.callback_group
        )
    
    def _create_action_servers(self):
        """创建动作服务器"""
        from control_msgs.action import GripperCommand
        from action_msgs.msg import GoalStatus
        
        # 抓取动作服务器
        self.grasp_action_server = ActionServer(
            GripperCommand,
            '/dexhand/grasp',
            self._grasp_execute_callback,
            callback_group=self.callback_group
        )
    
    def _position_command_callback(self, msg):
        """处理位置命令"""
        with self.state_lock:
            if len(msg.position) <= self.joint_count:
                self.target_positions[:len(msg.position)] = msg.position
                self.get_logger().debug(f'Position command received: {msg.position}')
    
    def _torque_command_callback(self, msg):
        """处理力矩命令"""
        with self.state_lock:
            if len(msg.effort) <= self.joint_count:
                self.target_torques[:len(msg.effort)] = msg.effort
                self.get_logger().debug(f'Torque command received: {msg.effort}')
    
    def _calibrate_callback(self, request, response):
        """校准服务"""
        self.get_logger().info('Starting calibration...')
        
        with self.state_lock:
            self.joint_positions = np.zeros(self.joint_count)
            self.joint_velocities = np.zeros(self.joint_count)
            self.joint_torques = np.zeros(self.joint_count)
        
        response.success = True
        response.message = 'Calibration complete'
        return response
    
    def _stop_callback(self, request, response):
        """停止服务"""
        self.get_logger().info('Emergency stop activated')
        
        with self.state_lock:
            self.target_positions = self.joint_positions.copy()
            self.target_torques = np.zeros(self.joint_count)
        
        response.success = True
        response.message = 'Emergency stop activated'
        return response
    
    def _grasp_execute_callback(self, goal_handle: ServerGoalHandle):
        """执行抓取动作"""
        from control_msgs.action import GripperCommand
        
        goal = goal_handle.request
        target_position = goal.command.position
        max_effort = goal.command.max_effort
        
        self.get_logger().info(f'Grasp action: position={target_position}, max_effort={max_effort}')
        
        # 执行抓取
        steps = 100
        for i in range(steps):
            # 平滑过渡到目标位置
            progress = i / steps
            current_target = self.joint_positions * (1 - progress) + target_position * progress
            
            with self.state_lock:
                self.target_positions[:] = current_target
            
            goal_handle.publish_feedback_wrapper({
                'position': float(current_target[0]),
                'effort': float(max_effort * progress)
            })
        
        # 返回结果
        result = GripperCommand.Result()
        result.position = float(target_position)
        result.reached_goal = True
        
        goal_handle.succeed()
        return result
    
    def _control_loop(self):
        """控制循环"""
        with self.state_lock:
            # 简单的位置控制
            position_error = self.target_positions - self.joint_positions
            
            # 更新状态 (实际需要与硬件通信)
            self.joint_positions += position_error * 0.1
            self.joint_velocities = position_error * 100
            self.joint_torques = self.target_torques
            
            # 模拟触觉数据
            self.touch_sensors = np.random.uniform(0, 1, 5)
        
        # 发布状态
        self._publish_states()
    
    def _publish_states(self):
        """发布状态消息"""
        from sensor_msgs.msg import JointState
        
        # 关节状态
        joint_state_msg = JointState()
        joint_state_msg.header.stamp = self.get_clock().now().to_msg()
        joint_state_msg.name = [f'joint_{i}' for i in range(self.joint_count)]
        joint_state_msg.position = self.joint_positions.tolist()
        joint_state_msg.velocity = self.joint_velocities.tolist()
        joint_state_msg.effort = self.joint_torques.tolist()
        self.joint_state_pub.publish(joint_state_msg)
        
        # 触觉数据
        from std_msgs.msg import Float32MultiArray
        touch_msg = Float32MultiArray()
        touch_msg.data = self.touch_sensors.tolist()
        self.touch_pub.publish(touch_msg)


def main(args=None):
    """ROS 2 节点入口"""
    rclpy.init(args=args)
    
    node = DexHandROS2Node()
    
    executor = MultiThreadedExecutor(num_threads=4)
    executor.add_node(node)
    
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
