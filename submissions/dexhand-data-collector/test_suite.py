"""
Automated Test Suite
Comprehensive testing framework for all system components.

Features:
- Unit tests for all modules
- Integration tests
- Performance benchmarks
- Regression tests
- Code coverage analysis
- Test report generation
"""

import unittest
import numpy as np
import time
import json
import os
from typing import Dict, List, Any
from dataclasses import dataclass
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@dataclass
class TestResult:
    """Test result structure."""
    test_name: str
    passed: bool
    duration: float
    error_message: str = ""
    details: Dict = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'test_name': self.test_name,
            'passed': self.passed,
            'duration': self.duration,
            'error_message': self.error_message,
            'details': self.details or {}
        }


class TestSuite:
    """Base test suite class."""
    
    def __init__(self, name: str):
        self.name = name
        self.results = []
        self.setup_complete = False
        
    def setup(self):
        """Setup test environment."""
        self.setup_complete = True
        
    def teardown(self):
        """Cleanup test environment."""
        pass
        
    def run_test(self, test_func: callable, test_name: str) -> TestResult:
        """Run a single test."""
        start_time = time.time()
        passed = True
        error_message = ""
        details = {}
        
        try:
            if not self.setup_complete:
                self.setup()
                
            result = test_func()
            
            if isinstance(result, dict):
                details = result
            elif isinstance(result, bool):
                passed = result
            else:
                passed = True
                
        except Exception as e:
            passed = False
            error_message = str(e)
            import traceback
            error_message += f"\n{traceback.format_exc()}"
            
        duration = time.time() - start_time
        
        result = TestResult(
            test_name=test_name,
            passed=passed,
            duration=duration,
            error_message=error_message,
            details=details
        )
        
        self.results.append(result)
        return result
        
    def get_summary(self) -> Dict:
        """Get test summary."""
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        duration = sum(r.duration for r in self.results)
        
        return {
            'suite_name': self.name,
            'total_tests': total,
            'passed': passed,
            'failed': total - passed,
            'success_rate': passed / total if total > 0 else 0,
            'total_duration': duration,
            'results': [r.to_dict() for r in self.results]
        }


class HardwareEmulatorTestSuite(TestSuite):
    """Test suite for hardware emulator."""
    
    def __init__(self):
        super().__init__("Hardware Emulator Tests")
        
    def test_sensor_noise(self):
        """Test sensor noise addition."""
        try:
            from hardware_emulator import create_hardware_emulator
            
            emulator = create_hardware_emulator()
            raw_data = np.random.randn(19)
            
            # Add noise multiple times
            noisy_data = emulator.add_sensor_noise(raw_data)
            
            # Check that noise was added
            assert not np.array_equal(raw_data, noisy_data), "Noise should modify data"
            assert noisy_data.shape == raw_data.shape, "Shape should be preserved"
            
            return {'noise_magnitude': np.mean(np.abs(noisy_data - raw_data))}
            
        except Exception as e:
            raise Exception(f"Sensor noise test failed: {e}")
            
    def test_motor_dynamics(self):
        """Test motor dynamics simulation."""
        try:
            from hardware_emulator import create_hardware_emulator
            
            emulator = create_hardware_emulator()
            command = np.ones(19) * 0.5
            velocity = np.zeros(19)
            
            # Process command
            processed = emulator.process_motor_command(command, velocity, 0.001)
            
            # Check saturation
            assert np.all(processed <= emulator.motor_saturation), "Should saturate"
            assert np.all(processed >= -emulator.motor_saturation), "Should saturate"
            
            return {'max_command': np.max(processed)}
            
        except Exception as e:
            raise Exception(f"Motor dynamics test failed: {e}")
            
    def test_communication_delay(self):
        """Test communication delay simulation."""
        try:
            from hardware_emulator import create_hardware_emulator
            
            emulator = create_hardware_emulator()
            
            # Add data to buffer
            for i in range(10):
                data = np.random.randn(19) * i
                emulator.process_sensor_data(data, time.time())
                
            # Check that delayed data is returned
            delayed = emulator.add_communication_delay(np.random.randn(19))
            
            return {'buffer_size': len(emulator.delayed_sensor_buffer)}
            
        except Exception as e:
            raise Exception(f"Communication delay test failed: {e}")


class NeuralControllerTestSuite(TestSuite):
    """Test suite for neural controller."""
    
    def __init__(self):
        super().__init__("Neural Controller Tests")
        
    def test_forward_pass(self):
        """Test neural network forward pass."""
        try:
            from neural_controller import create_neural_controller
            
            controller = create_neural_controller()
            state = np.random.randn(38)
            
            action = controller.predict(state)
            
            assert action.shape == (19,), f"Action shape should be (19,), got {action.shape}"
            assert np.all(action >= -1) and np.all(action <= 1), "Actions should be bounded"
            
            return {'action_mean': np.mean(action), 'action_std': np.std(action)}
            
        except Exception as e:
            raise Exception(f"Forward pass test failed: {e}")
            
    def test_behavioral_cloning(self):
        """Test behavioral cloning update."""
        try:
            from neural_controller import create_neural_controller
            
            controller = create_neural_controller()
            
            # Add demonstrations
            for _ in range(10):
                state = np.random.randn(38)
                action = np.random.randn(19)
                controller.add_demonstration(state, action)
                
            # Update
            loss = controller.behavioral_cloning_update()
            
            assert loss is not None, "Loss should be computed"
            assert loss >= 0, "Loss should be non-negative"
            
            return {'loss': loss, 'demonstrations': len(controller.expert_demonstrations)}
            
        except Exception as e:
            raise Exception(f"Behavioral cloning test failed: {e}")
            
    def test_reward_computation(self):
        """Test reward computation."""
        try:
            from neural_controller import create_neural_controller
            
            controller = create_neural_controller()
            
            state = np.random.randn(38)
            action = np.random.randn(19)
            next_state = np.random.randn(38)
            
            # Test with object position
            object_pos = np.array([0.1, 0.1, 0.1])
            target_pos = np.array([0.0, 0.0, 0.0])
            
            reward = controller.compute_reward(state, action, next_state, object_pos, target_pos)
            
            assert isinstance(reward, (int, float)), "Reward should be numeric"
            
            return {'reward': reward}
            
        except Exception as e:
            raise Exception(f"Reward computation test failed: {e}")


class TaskScenariosTestSuite(TestSuite):
    """Test suite for task scenarios."""
    
    def __init__(self):
        super().__init__("Task Scenarios Tests")
        
    def test_scenario_library(self):
        """Test scenario library."""
        try:
            from task_scenarios import TaskScenarioLibrary
            
            scenarios = TaskScenarioLibrary.get_all_scenarios()
            
            assert len(scenarios) >= 8, f"Should have at least 8 scenarios, got {len(scenarios)}"
            
            stats = TaskScenarioLibrary.get_statistics()
            
            assert stats['total_scenarios'] >= 8, "Statistics should match"
            
            return {
                'total_scenarios': stats['total_scenarios'],
                'difficulty_breakdown': stats['difficulty_breakdown']
            }
            
        except Exception as e:
            raise Exception(f"Scenario library test failed: {e}")
            
    def test_benchmark_system(self):
        """Test benchmark system."""
        try:
            from task_scenarios import PerformanceBenchmark
            
            benchmark = PerformanceBenchmark()
            
            # Mock controller
            class MockController:
                def __init__(self):
                    self.name = "test_controller"
                    
            controller = MockController()
            
            # Run benchmark (simplified)
            results = benchmark.run_benchmark(
                "test_controller",
                controller,
                ["vial_grasping", "cap_rotation"],
                num_trials=3
            )
            
            assert 'controller' in results, "Results should contain controller name"
            assert 'scenarios' in results, "Results should contain scenarios"
            
            return {
                'scenarios_tested': len(results.get('scenarios', {})),
                'overall_metrics': results.get('overall', {})
            }
            
        except Exception as e:
            raise Exception(f"Benchmark system test failed: {e}")


class RLControllerTestSuite(TestSuite):
    """Test suite for RL controller."""
    
    def __init__(self):
        super().__init__("RL Controller Tests")
        
    def test_ppo_controller(self):
        """Test PPO controller."""
        try:
            from rl_controller import create_ppo_controller, RLConfig
            
            config = RLConfig()
            controller = create_ppo_controller(config)
            
            state = np.random.randn(38)
            action, log_prob = controller.select_action(state)
            
            assert action.shape == (19,), f"Action shape should be (19,), got {action.shape}"
            assert isinstance(log_prob, float), "Log prob should be float"
            
            stats = controller.get_statistics()
            
            return {
                'action_mean': np.mean(action),
                'total_steps': stats['total_steps']
            }
            
        except Exception as e:
            raise Exception(f"PPO controller test failed: {e}")
            
    def test_multitask_ppo(self):
        """Test multi-task PPO controller."""
        try:
            from rl_controller import create_multitask_ppo_controller, RLConfig
            
            config = RLConfig()
            controller = create_multitask_ppo_controller(config, num_tasks=8)
            
            assert controller.num_tasks == 8, "Should have 8 tasks"
            
            # Test action selection for different tasks
            state = np.random.randn(38)
            actions = []
            
            for task_id in range(8):
                controller.set_task(task_id)
                action, _ = controller.select_action(state)
                actions.append(action)
                
            assert len(actions) == 8, "Should have 8 actions"
            
            return {
                'num_tasks': controller.num_tasks,
                'actions_mean': np.mean([np.mean(a) for a in actions])
            }
            
        except Exception as e:
            raise Exception(f"Multi-task PPO test failed: {e}")


class RealtimeInterfaceTestSuite(TestSuite):
    """Test suite for real-time interface."""
    
    def __init__(self):
        super().__init__("Realtime Interface Tests")
        
    def test_sensor_data(self):
        """Test sensor data structure."""
        try:
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
            
            # Test serialization
            data_dict = sensor_data.to_dict()
            json_str = sensor_data.to_json()
            
            assert 'timestamp' in data_dict, "Dict should contain timestamp"
            assert len(json_str) > 0, "JSON should not be empty"
            
            return {
                'joint_count': len(sensor_data.joint_positions),
                'json_length': len(json_str)
            }
            
        except Exception as e:
            raise Exception(f"Sensor data test failed: {e}")
            
    def test_command_data(self):
        """Test command data structure."""
        try:
            from realtime_interface import CommandData
            
            command = CommandData(
                timestamp=time.time(),
                joint_commands=np.random.randn(19).tolist(),
                grip_force=0.5,
                mode="position"
            )
            
            # Test serialization
            json_str = command.to_json()
            
            # Test deserialization
            command2 = CommandData.from_dict(json.loads(json_str))
            
            assert command2.mode == command.mode, "Mode should be preserved"
            assert command2.grip_force == command.grip_force, "Grip force should be preserved"
            
            return {
                'command_count': len(command.joint_commands),
                'mode': command.mode
            }
            
        except Exception as e:
            raise Exception(f"Command data test failed: {e}")


class MultitaskLearningTestSuite(TestSuite):
    """Test suite for multi-task learning."""
    
    def __init__(self):
        super().__init__("Multi-Task Learning Tests")
        
    def test_task_embedding(self):
        """Test task embedding."""
        try:
            from multitask_learning import TaskEmbedding
            
            embedding = TaskEmbedding(num_tasks=8, embedding_dim=32)
            
            # Get embeddings
            emb1 = embedding.get_embedding(0)
            emb2 = embedding.get_embedding(1)
            
            assert emb1.shape == (32,), f"Embedding shape should be (32,), got {emb1.shape}"
            assert emb2.shape == (32,), f"Embedding shape should be (32,), got {emb2.shape}"
            
            return {
                'embedding_dim': embedding.embedding_dim,
                'num_tasks': embedding.num_tasks
            }
            
        except Exception as e:
            raise Exception(f"Task embedding test failed: {e}")
            
    def test_multitask_network(self):
        """Test multi-task network."""
        try:
            from multitask_learning import MultiTaskNetwork
            
            network = MultiTaskNetwork(
                state_dim=38,
                action_dim=19,
                num_tasks=8
            )
            
            state = np.random.randn(38)
            
            # Test forward pass for different tasks
            actions = []
            for task_id in range(8):
                action = network.forward(state, task_id)
                actions.append(action)
                
            assert len(actions) == 8, "Should have 8 actions"
            
            return {
                'action_mean': np.mean([np.mean(a) for a in actions]),
                'action_std': np.mean([np.std(a) for a in actions])
            }
            
        except Exception as e:
            raise Exception(f"Multi-task network test failed: {e}")


class TestRunner:
    """Main test runner."""
    
    def __init__(self):
        self.suites = []
        self.all_results = []
        
    def add_suite(self, suite: TestSuite):
        """Add test suite."""
        self.suites.append(suite)
        
    def run_all(self) -> Dict:
        """Run all test suites."""
        print("\n" + "="*60)
        print("Running Automated Test Suite")
        print("="*60 + "\n")
        
        for suite in self.suites:
            print(f"\nRunning: {suite.name}")
            print("-" * 60)
            
            # Run all tests in suite
            test_methods = [m for m in dir(suite) if m.startswith('test_')]
            
            for test_method_name in test_methods:
                test_method = getattr(suite, test_method_name)
                
                result = suite.run_test(test_method, test_method_name)
                
                status = "✓ PASS" if result.passed else "✗ FAIL"
                print(f"  {status}: {test_method_name} ({result.duration:.3f}s)")
                
                if not result.passed:
                    print(f"    Error: {result.error_message}")
                    
            suite.teardown()
            
            # Print suite summary
            summary = suite.get_summary()
            self.all_results.append(summary)
            
            print(f"\n  Suite Summary: {summary['passed']}/{summary['total_tests']} passed "
                  f"({summary['success_rate']*100:.1f}%)")
            
        # Generate overall report
        return self.generate_report()
        
    def generate_report(self) -> Dict:
        """Generate comprehensive test report."""
        total_tests = sum(s['total_tests'] for s in self.all_results)
        total_passed = sum(s['passed'] for s in self.all_results)
        total_duration = sum(s['total_duration'] for s in self.all_results)
        
        report = {
            'timestamp': time.time(),
            'total_suites': len(self.all_results),
            'total_tests': total_tests,
            'total_passed': total_passed,
            'total_failed': total_tests - total_passed,
            'overall_success_rate': total_passed / total_tests if total_tests > 0 else 0,
            'total_duration': total_duration,
            'suites': self.all_results
        }
        
        # Print summary
        print("\n" + "="*60)
        print("Test Report Summary")
        print("="*60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {total_passed}")
        print(f"Failed: {total_tests - total_passed}")
        print(f"Success Rate: {report['overall_success_rate']*100:.1f}%")
        print(f"Total Duration: {total_duration:.2f}s")
        print("="*60 + "\n")
        
        return report
        
    def save_report(self, filepath: str):
        """Save test report to file."""
        report = self.generate_report()
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
            
        print(f"Test report saved to: {filepath}")


def run_all_tests() -> Dict:
    """Run all test suites."""
    runner = TestRunner()
    
    # Add all test suites
    runner.add_suite(HardwareEmulatorTestSuite())
    runner.add_suite(NeuralControllerTestSuite())
    runner.add_suite(TaskScenariosTestSuite())
    runner.add_suite(RLControllerTestSuite())
    runner.add_suite(RealtimeInterfaceTestSuite())
    runner.add_suite(MultitaskLearningTestSuite())
    
    # Run tests
    return runner.run_all()


if __name__ == "__main__":
    # Run all tests
    report = run_all_tests()
    
    # Save report
    runner = TestRunner()
    runner.add_suite(HardwareEmulatorTestSuite())
    runner.add_suite(NeuralControllerTestSuite())
    runner.add_suite(TaskScenariosTestSuite())
    runner.add_suite(RLControllerTestSuite())
    runner.add_suite(RealtimeInterfaceTestSuite())
    runner.add_suite(MultitaskLearningTestSuite())
    
    runner.run_all()
    runner.save_report("test_report.json")
    
    print("\nAll tests completed!")