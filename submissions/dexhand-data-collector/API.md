# API Reference

Complete API documentation for DexHand Data Collector.

## Table of Contents

1. [Hardware Emulator](#hardware-emulator)
2. [Neural Controller](#neural-controller)
3. [Task Scenarios](#task-scenarios)
4. [RL Controller](#rl-controller)
5. [Real-time Interface](#real-time-interface)
6. [Multi-task Learning](#multi-task-learning)
7. [Test Suite](#test-suite)

---

## Hardware Emulator

### `HardwareEmulator`

Main class for simulating real hardware characteristics.

#### Constructor

```python
HardwareEmulator(
    sensor_noise_std: float = 0.01,
    communication_delay: float = 0.005,
    motor_saturation: float = 1.5,
    dead_zone: float = 0.02,
    temperature_drift: float = 0.001,
    quantization_bits: int = 12,
    motor_time_constant: float = 0.01,
    sensor_bias: float = 0.001,
    friction_compensation: float = 0.05
)
```

**Parameters:**
- `sensor_noise_std`: Standard deviation of sensor noise (default: 0.01)
- `communication_delay`: Communication delay in seconds (default: 0.005)
- `motor_saturation`: Maximum motor command (default: 1.5)
- `dead_zone`: Motor dead zone (default: 0.02)
- `temperature_drift`: Temperature drift coefficient (default: 0.001)
- `quantization_bits`: ADC quantization bits (default: 12)
- `motor_time_constant`: Motor time constant (default: 0.01)
- `sensor_bias`: Sensor bias (default: 0.001)
- `friction_compensation`: Friction compensation coefficient (default: 0.05)

#### Methods

##### `process_sensor_data(raw_data: np.ndarray, timestamp: float) -> np.ndarray`

Process raw sensor data through hardware emulation pipeline.

**Parameters:**
- `raw_data`: Raw sensor readings from simulation
- `timestamp`: Current simulation timestamp

**Returns:**
- Processed sensor data with hardware effects

**Example:**
```python
from hardware_emulator import create_hardware_emulator

emulator = create_hardware_emulator()
raw_data = np.random.randn(19)
processed = emulator.process_sensor_data(raw_data, time.time())
```

##### `process_motor_command(command: np.ndarray, current_velocity: np.ndarray, dt: float) -> np.ndarray`

Process motor command through hardware emulation pipeline.

**Parameters:**
- `command`: Desired motor commands
- `current_velocity`: Current joint velocities
- `dt`: Time step

**Returns:**
- Processed motor commands with hardware effects

**Example:**
```python
command = np.ones(19) * 0.5
velocity = np.zeros(19)
processed = emulator.process_motor_command(command, velocity, 0.001)
```

##### `get_characteristics_report() -> Dict`

Get current hardware characteristics.

**Returns:**
- Dictionary of hardware characteristics

**Example:**
```python
report = emulator.get_characteristics_report()
print(f"Temperature: {report['current_temperature_C']}°C")
print(f"Delay: {report['communication_delay_ms']}ms")
```

---

## Neural Controller

### `NeuralNetworkController`

Neural network based controller for dexterous hand manipulation.

#### Constructor

```python
NeuralNetworkController(
    state_dim: int = 38,
    action_dim: int = 19,
    hidden_sizes: List[int] = [256, 256, 128],
    learning_rate: float = 0.0003,
    device: str = "cpu"
)
```

#### Methods

##### `predict(state: np.ndarray) -> np.ndarray`

Predict action from state.

**Parameters:**
- `state`: Current state vector

**Returns:**
- Action vector bounded to [-1, 1]

**Example:**
```python
from neural_controller import create_neural_controller

controller = create_neural_controller()
state = np.random.randn(38)
action = controller.predict(state)
```

##### `add_demonstration(state: np.ndarray, action: np.ndarray)`

Add expert demonstration for behavioral cloning.

**Parameters:**
- `state`: Expert state
- `action`: Expert action

**Example:**
```python
controller.add_demonstration(state, action)
controller.behavioral_cloning_update()
```

##### `compute_reward(state, action, next_state, object_pos=None, target_pos=None) -> float`

Compute reinforcement learning reward.

**Parameters:**
- `state`: Current state
- `action`: Action taken
- `next_state`: Next state
- `object_pos`: Current object position (optional)
- `target_pos`: Target object position (optional)

**Returns:**
- Reward value

**Example:**
```python
reward = controller.compute_reward(
    state, action, next_state,
    object_pos=np.array([0.1, 0.1, 0.1]),
    target_pos=np.array([0.0, 0.0, 0.0])
)
```

---

## Task Scenarios

### `TaskScenarioLibrary`

Library of task scenarios for evaluation.

#### Methods

##### `get_scenario(name: str) -> Optional[TaskScenario]`

Get a specific scenario by name.

**Parameters:**
- `name`: Scenario name (e.g., "vial_grasping")

**Returns:**
- TaskScenario object or None

**Example:**
```python
from task_scenarios import TaskScenarioLibrary

scenario = TaskScenarioLibrary.get_scenario("vial_grasping")
print(f"Difficulty: {scenario.difficulty}")
print(f"Estimated steps: {scenario.estimated_steps}")
```

##### `get_all_scenarios() -> List[TaskScenario]`

Get all available scenarios.

**Returns:**
- List of TaskScenario objects

**Example:**
```python
scenarios = TaskScenarioLibrary.get_all_scenarios()
for scenario in scenarios:
    print(f"{scenario.name}: {scenario.difficulty}")
```

### `PerformanceBenchmark`

Benchmark system for comparing controller performance.

#### Methods

##### `run_benchmark(controller_name: str, controller, task_scenarios: List[str], num_trials: int = 10) -> Dict`

Run comprehensive benchmark for a controller.

**Parameters:**
- `controller_name`: Name of the controller
- `controller`: Controller object
- `task_scenarios`: List of scenario names to test
- `num_trials`: Number of trials per scenario

**Returns:**
- Dictionary of benchmark results

**Example:**
```python
from task_scenarios import PerformanceBenchmark

benchmark = PerformanceBenchmark()
results = benchmark.run_benchmark(
    "my_controller",
    my_controller,
    ["vial_grasping", "cap_rotation"],
    num_trials=10
)
print(benchmark.generate_report("my_controller"))
```

---

## RL Controller

### `PPOController`

PPO (Proximal Policy Optimization) controller.

#### Constructor

```python
PPOController(config: Optional[RLConfig] = None)
```

#### Methods

##### `select_action(state: np.ndarray, deterministic: bool = False) -> Tuple[np.ndarray, float]`

Select action using current policy.

**Parameters:**
- `state`: Current state
- `deterministic`: Whether to use deterministic policy

**Returns:**
- Tuple of (action, log_prob)

**Example:**
```python
from rl_controller import create_ppo_controller

controller = create_ppo_controller()
action, log_prob = controller.select_action(state)
```

##### `train_episode(env, max_steps: int = 1000) -> Dict`

Train for one episode.

**Parameters:**
- `env`: Environment
- `max_steps`: Maximum steps per episode

**Returns:**
- Training statistics

**Example:**
```python
stats = controller.train_episode(env, max_steps=1000)
print(f"Episode reward: {stats['episode_reward']}")
```

---

## Real-time Interface

### `RealTimeController`

Real-time controller with ROS and WebSocket interfaces.

#### Constructor

```python
RealTimeController(
    enable_websocket: bool = True,
    enable_ros: bool = True,
    websocket_port: int = 8765
)
```

#### Methods

##### `start()`

Start real-time controller.

**Example:**
```python
from realtime_interface import create_realtime_controller

controller = create_realtime_controller()
controller.start()
```

##### `update_sensor_data(sensor_data: SensorData)`

Update sensor data.

**Parameters:**
- `sensor_data`: SensorData object

**Example:**
```python
from realtime_interface import SensorData

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
```

##### `get_status() -> Dict`

Get controller status.

**Returns:**
- Dictionary of status information

**Example:**
```python
status = controller.get_status()
print(f"Running: {status['running']}")
print(f"Clients: {status['websocket_clients']}")
```

---

## Multi-task Learning

### `MultiTaskLearningFramework`

Complete multi-task learning framework.

#### Constructor

```python
MultiTaskLearningFramework(
    task_configs: List[TaskConfig],
    learning_rate: float = 0.0003,
    gamma: float = 0.99
)
```

#### Methods

##### `train_episode(task_id: int, env, max_steps: int = 1000) -> Dict`

Train for one episode on specific task.

**Parameters:**
- `task_id`: Task identifier
- `env`: Environment
- `max_steps`: Maximum steps per episode

**Returns:**
- Training statistics

**Example:**
```python
from multitask_learning import create_multitask_framework, TaskConfig

task_configs = [
    TaskConfig(
        task_id=0,
        task_name="vial_grasping",
        state_dim=38,
        action_dim=19,
        difficulty="easy",
        reward_weights={"reach": 1.0, "grasp": 2.0},
        success_criteria={"lift_height": 0.1}
    )
]

framework = create_multitask_framework(task_configs)
stats = framework.train_episode(0, env)
```

##### `evaluate_all_tasks(env, num_episodes: int = 10) -> Dict`

Evaluate performance on all tasks.

**Parameters:**
- `env`: Environment
- `num_episodes`: Number of evaluation episodes

**Returns:**
- Dictionary of evaluation results

**Example:**
```python
results = framework.evaluate_all_tasks(env, num_episodes=10)
for task_name, result in results.items():
    print(f"{task_name}: {result['success_rate']:.1%}")
```

---

## Test Suite

### `TestRunner`

Main test runner for automated testing.

#### Methods

##### `run_all() -> Dict`

Run all test suites.

**Returns:**
- Test report dictionary

**Example:**
```python
from test_suite import run_all_tests

report = run_all_tests()
print(f"Success rate: {report['overall_success_rate']*100:.1f}%")
```

---

## Usage Examples

### Complete Workflow

```python
# 1. Initialize hardware emulator
from hardware_emulator import create_hardware_emulator
emulator = create_hardware_emulator()

# 2. Create neural controller
from neural_controller import create_neural_controller
controller = create_neural_controller()

# 3. Set up real-time interface
from realtime_interface import create_realtime_controller
rt_controller = create_realtime_controller()
rt_controller.start()

# 4. Run benchmark
from task_scenarios import PerformanceBenchmark
benchmark = PerformanceBenchmark()
results = benchmark.run_benchmark("neural_controller", controller, ["vial_grasping"])

# 5. Save results
benchmark.save_results("benchmark_results.json")
```

### Multi-task Training

```python
from multitask_learning import create_multitask_framework, TaskConfig

# Define tasks
task_configs = [
    TaskConfig(
        task_id=0,
        task_name="vial_grasping",
        state_dim=38,
        action_dim=19,
        difficulty="easy",
        reward_weights={"reach": 1.0, "grasp": 2.0},
        success_criteria={"lift_height": 0.1}
    ),
    TaskConfig(
        task_id=1,
        task_name="cap_rotation",
        state_dim=38,
        action_dim=19,
        difficulty="medium",
        reward_weights={"grip": 2.0, "rotation": 3.0},
        success_criteria={"rotation_angle": 6.28}
    )
]

# Create framework
framework = create_multitask_framework(task_configs)

# Train with curriculum
curriculum_stats = framework.train_curriculum(env, episodes_per_task=10)

# Evaluate
results = framework.evaluate_all_tasks(env, num_episodes=10)
```

---

## Error Handling

```python
try:
    # Create controller
    controller = create_neural_controller()
    
    # Predict action
    action = controller.predict(state)
    
except ValueError as e:
    print(f"Invalid state: {e}")
except RuntimeError as e:
    print(f"Controller error: {e}")
```

---

## Performance Tips

1. **Use hardware emulation sparingly**: Only enable when needed for sim-to-real transfer
2. **Batch processing**: Process multiple states together when possible
3. **Caching**: Cache frequently used computations
4. **Parallel execution**: Use multiprocessing for independent tasks
5. **Memory management**: Clear buffers periodically to prevent memory leaks

---

## Troubleshooting

### Common Issues

**Issue**: `ImportError: No module named 'mujoco'`
**Solution**: Install MuJoCo: `pip install mujoco`

**Issue**: `OSError: DLL load failed`
**Solution**: Install Visual C++ Redistributable

**Issue**: WebSocket connection refused
**Solution**: Check if port 8765 is available

**Issue**: Training is slow
**Solution**: Reduce batch size or use GPU acceleration

---

## Support

For issues and questions:
- Check the [README.md](README.md) for general information
- Run `python test_suite.py` to verify installation
- Check logs in the `logs/` directory

---

## License

See [LICENSE](LICENSE) for details.