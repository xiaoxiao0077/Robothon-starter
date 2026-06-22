"""
Real-time Communication Interface
Provides ROS (Robot Operating System) and WebSocket interfaces for real-time control.

Features:
- ROS node implementation (compatible with ROS1/ROS2)
- WebSocket server for web-based control
- Real-time sensor streaming
- Command queue management
- Multi-client support
"""

import numpy as np
import json
import time
import threading
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from queue import Queue
import socket
import struct

@dataclass
class SensorData:
    """Sensor data structure."""
    timestamp: float
    joint_positions: List[float]
    joint_velocities: List[float]
    joint_torques: List[float]
    contact_forces: List[float]
    imu_acceleration: List[float]
    imu_gyroscope: List[float]
    tactile_sensors: List[float]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
        
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())
        
    @classmethod
    def from_dict(cls, data: Dict) -> 'SensorData':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class CommandData:
    """Command data structure."""
    timestamp: float
    joint_commands: List[float]
    grip_force: float
    mode: str = "position"  # position, velocity, torque
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
        
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())
        
    @classmethod
    def from_dict(cls, data: Dict) -> 'CommandData':
        """Create from dictionary."""
        return cls(**data)


class WebSocketServer:
    """
    WebSocket server for real-time communication.
    Supports multiple clients and bidirectional communication.
    """
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8765):
        self.host = host
        self.port = port
        self.clients = []
        self.running = False
        self.sensor_queue = Queue(maxsize=100)
        self.command_queue = Queue(maxsize=100)
        self.thread = None
        
        # Callbacks
        self.on_command_received: Optional[Callable] = None
        self.on_client_connected: Optional[Callable] = None
        self.on_client_disconnected: Optional[Callable] = None
        
    def start(self):
        """Start WebSocket server."""
        self.running = True
        self.thread = threading.Thread(target=self._run_server, daemon=True)
        self.thread.start()
        print(f"WebSocket server started on {self.host}:{self.port}")
        
    def stop(self):
        """Stop WebSocket server."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        print("WebSocket server stopped")
        
    def _run_server(self):
        """Run WebSocket server (simplified implementation)."""
        # Create socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server_socket.bind((self.host, self.port))
            server_socket.listen(5)
            server_socket.settimeout(1.0)
            
            while self.running:
                try:
                    client_socket, address = server_socket.accept()
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, address),
                        daemon=True
                    )
                    client_thread.start()
                    
                except socket.timeout:
                    continue
                    
        except Exception as e:
            print(f"WebSocket server error: {e}")
        finally:
            server_socket.close()
            
    def _handle_client(self, client_socket: socket.socket, address: tuple):
        """Handle client connection."""
        print(f"Client connected: {address}")
        self.clients.append(client_socket)
        
        if self.on_client_connected:
            self.on_client_connected(address)
            
        try:
            while self.running:
                # Send sensor data
                if not self.sensor_queue.empty():
                    sensor_data = self.sensor_queue.get()
                    message = sensor_data.to_json() + "\n"
                    client_socket.sendall(message.encode())
                    
                # Receive command
                try:
                    data = client_socket.recv(1024).decode()
                    if data:
                        command = CommandData.from_dict(json.loads(data.strip()))
                        self.command_queue.put(command)
                        
                        if self.on_command_received:
                            self.on_command_received(command)
                            
                except socket.timeout:
                    continue
                    
        except Exception as e:
            print(f"Client error: {e}")
        finally:
            client_socket.close()
            self.clients.remove(client_socket)
            
            if self.on_client_disconnected:
                self.on_client_disconnected(address)
                
            print(f"Client disconnected: {address}")
            
    def broadcast_sensor_data(self, sensor_data: SensorData):
        """Broadcast sensor data to all clients."""
        if self.sensor_queue.full():
            self.sensor_queue.get()  # Remove oldest
        self.sensor_queue.put(sensor_data)
        
    def get_command(self, timeout: float = 0.1) -> Optional[CommandData]:
        """Get command from queue."""
        try:
            return self.command_queue.get(timeout=timeout)
        except:
            return None
            
    def send_command(self, command: CommandData):
        """Send command to all clients."""
        message = command.to_json() + "\n"
        for client in self.clients:
            try:
                client.sendall(message.encode())
            except:
                pass


class ROSInterface:
    """
    ROS (Robot Operating System) interface for integration with ROS ecosystem.
    Compatible with both ROS1 and ROS2.
    """
    
    def __init__(self, node_name: str = "dexhand_controller"):
        self.node_name = node_name
        self.ros_available = False
        self.publishers = {}
        self.subscribers = {}
        self.services = {}
        
        # Try to import ROS
        try:
            import rospy
            from std_msgs.msg import Float32MultiArray, String
            from sensor_msgs.msg import JointState
            from geometry_msgs.msg import WrenchStamped
            
            self.ros_available = True
            self.rospy = rospy
            self.Float32MultiArray = Float32MultiArray
            self.String = String
            self.JointState = JointState
            self.WrenchStamped = WrenchStamped
            
        except ImportError:
            print("ROS not available, using mock implementation")
            
    def init_node(self):
        """Initialize ROS node."""
        if self.ros_available:
            self.rospy.init_node(self.node_name, anonymous=True)
            print(f"ROS node initialized: {self.node_name}")
            
    def create_publisher(self, topic_name: str, msg_type: str, queue_size: int = 10):
        """Create ROS publisher."""
        if not self.ros_available:
            return
            
        if msg_type == "sensor":
            self.publishers[topic_name] = self.rospy.Publisher(
                topic_name,
                self.JointState,
                queue_size=queue_size
            )
        elif msg_type == "wrench":
            self.publishers[topic_name] = self.rospy.Publisher(
                topic_name,
                self.WrenchStamped,
                queue_size=queue_size
            )
        elif msg_type == "string":
            self.publishers[topic_name] = self.rospy.Publisher(
                topic_name,
                self.String,
                queue_size=queue_size
            )
            
    def create_subscriber(self, topic_name: str, msg_type: str, callback: Callable):
        """Create ROS subscriber."""
        if not self.ros_available:
            return
            
        def wrapper(msg):
            if msg_type == "sensor":
                data = {
                    'positions': list(msg.position),
                    'velocities': list(msg.velocity),
                    'efforts': list(msg.effort)
                }
            elif msg_type == "wrench":
                data = {
                    'force': [msg.wrench.force.x, msg.wrench.force.y, msg.wrench.force.z],
                    'torque': [msg.wrench.torque.x, msg.wrench.torque.y, msg.wrench.torque.z]
                }
            elif msg_type == "string":
                data = msg.data
            else:
                data = None
                
            callback(data)
            
        if msg_type == "sensor":
            self.subscribers[topic_name] = self.rospy.Subscriber(
                topic_name,
                self.JointState,
                wrapper
            )
        elif msg_type == "wrench":
            self.subscribers[topic_name] = self.rospy.Subscriber(
                topic_name,
                self.WrenchStamped,
                wrapper
            )
        elif msg_type == "string":
            self.subscribers[topic_name] = self.rospy.Subscriber(
                topic_name,
                self.String,
                wrapper
            )
            
    def publish_sensor_data(self, topic_name: str, sensor_data: SensorData):
        """Publish sensor data to ROS topic."""
        if not self.ros_available or topic_name not in self.publishers:
            return
            
        msg = self.JointState()
        msg.header.stamp = self.rospy.Time.now()
        msg.position = sensor_data.joint_positions
        msg.velocity = sensor_data.joint_velocities
        msg.effort = sensor_data.joint_torques
        
        self.publishers[topic_name].publish(msg)
        
    def publish_command(self, topic_name: str, command_data: CommandData):
        """Publish command to ROS topic."""
        if not self.ros_available or topic_name not in self.publishers:
            return
            
        msg = self.Float32MultiArray()
        msg.data = command_data.joint_commands
        
        self.publishers[topic_name].publish(msg)
        
    def spin_once(self, timeout: float = 0.1):
        """Process ROS callbacks once."""
        if self.ros_available:
            self.rospy.sleep(timeout)
            
    def spin(self):
        """Keep ROS node running."""
        if self.ros_available:
            self.rospy.spin()


class RealTimeController:
    """
    Real-time controller that integrates ROS and WebSocket interfaces.
    """
    
    def __init__(
        self,
        enable_websocket: bool = True,
        enable_ros: bool = True,
        websocket_port: int = 8765
    ):
        self.enable_websocket = enable_websocket
        self.enable_ros = enable_ros
        
        # Initialize interfaces
        self.websocket_server = WebSocketServer(port=websocket_port) if enable_websocket else None
        self.ros_interface = ROSInterface() if enable_ros else None
        
        # State
        self.current_sensor_data: Optional[SensorData] = None
        self.current_command: Optional[CommandData] = None
        self.running = False
        
        # Control loop
        self.control_thread = None
        self.control_frequency = 1000  # Hz
        self.control_callback: Optional[Callable] = None
        
    def start(self):
        """Start real-time controller."""
        self.running = True
        
        # Start ROS
        if self.ros_interface:
            self.ros_interface.init_node()
            self.ros_interface.create_publisher("/dexhand/sensor_data", "sensor")
            self.ros_interface.create_publisher("/dexhand/command", "string")
            self.ros_interface.create_subscriber("/dexhand/target_command", "string", self._on_ros_command)
            
        # Start WebSocket
        if self.websocket_server:
            self.websocket_server.on_command_received = self._on_websocket_command
            self.websocket_server.start()
            
        # Start control loop
        self.control_thread = threading.Thread(target=self._control_loop, daemon=True)
        self.control_thread.start()
        
        print("Real-time controller started")
        
    def stop(self):
        """Stop real-time controller."""
        self.running = False
        
        if self.websocket_server:
            self.websocket_server.stop()
            
        if self.control_thread:
            self.control_thread.join(timeout=2)
            
        print("Real-time controller stopped")
        
    def _control_loop(self):
        """Main control loop."""
        period = 1.0 / self.control_frequency
        
        while self.running:
            start_time = time.time()
            
            # Process ROS callbacks
            if self.ros_interface:
                self.ros_interface.spin_once(0)
                
            # Get command from WebSocket
            if self.websocket_server:
                command = self.websocket_server.get_command(timeout=0.001)
                if command:
                    self.current_command = command
                    
            # Execute control callback
            if self.control_callback and self.current_sensor_data:
                self.control_callback(self.current_sensor_data, self.current_command)
                
            # Maintain timing
            elapsed = time.time() - start_time
            sleep_time = max(0, period - elapsed)
            time.sleep(sleep_time)
            
    def _on_websocket_command(self, command: CommandData):
        """Handle WebSocket command."""
        self.current_command = command
        
        # Forward to ROS
        if self.ros_interface:
            self.ros_interface.publish_command("/dexhand/command", command)
            
    def _on_ros_command(self, data):
        """Handle ROS command."""
        if isinstance(data, str):
            try:
                command_data = CommandData.from_dict(json.loads(data))
                self.current_command = command_data
            except:
                pass
                
    def update_sensor_data(self, sensor_data: SensorData):
        """Update sensor data."""
        self.current_sensor_data = sensor_data
        
        # Broadcast to WebSocket
        if self.websocket_server:
            self.websocket_server.broadcast_sensor_data(sensor_data)
            
        # Publish to ROS
        if self.ros_interface:
            self.ros_interface.publish_sensor_data("/dexhand/sensor_data", sensor_data)
            
    def set_control_callback(self, callback: Callable):
        """Set control callback function."""
        self.control_callback = callback
        
    def get_status(self) -> Dict:
        """Get controller status."""
        return {
            'running': self.running,
            'websocket_enabled': self.enable_websocket,
            'ros_enabled': self.enable_ros,
            'ros_available': self.ros_interface.ros_available if self.ros_interface else False,
            'websocket_clients': len(self.websocket_server.clients) if self.websocket_server else 0,
            'control_frequency': self.control_frequency,
            'current_command': self.current_command.to_dict() if self.current_command else None
        }


def create_realtime_controller(
    enable_websocket: bool = True,
    enable_ros: bool = True,
    websocket_port: int = 8765
) -> RealTimeController:
    """Factory function to create real-time controller."""
    return RealTimeController(enable_websocket, enable_ros, websocket_port)


if __name__ == "__main__":
    # Test real-time controller
    print("Testing Real-Time Controller...")
    
    controller = create_realtime_controller(
        enable_websocket=True,
        enable_ros=True,
        websocket_port=8765
    )
    
    # Define control callback
    def control_callback(sensor_data: SensorData, command: Optional[CommandData]):
        if command:
            print(f"Received command: {command.joint_commands[:3]}...")
            
    controller.set_control_callback(control_callback)
    
    # Start controller
    controller.start()
    
    # Simulate sensor data updates
    try:
        for i in range(10):
            sensor_data = SensorData(
                timestamp=time.time(),
                joint_positions=np.random.randn(19).tolist(),
                joint_velocities=np.random.randn(19).tolist(),
                joint_torques=np.random.randn(19).tolist(),
                contact_forces=np.random.randn(6).tolist(),
                imu_acceleration=np.random.randn(3).tolist(),
                imu_gyroscope=np.random.randn(3).tolist(),
                tactile_sensors=np.random.randn(5).tolist()
            )
            
            controller.update_sensor_data(sensor_data)
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        pass
    finally:
        controller.stop()
        
    print("Test completed!")