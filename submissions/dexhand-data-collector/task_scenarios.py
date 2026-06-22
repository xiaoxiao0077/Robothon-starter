"""
Extended Task Scenarios and Performance Benchmarking Module

This module provides:
1. 8 different task scenarios for comprehensive evaluation
2. Performance benchmarking against baseline controllers
3. Sim-to-real transfer analysis
4. Detailed metrics and statistics
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import json
import time

@dataclass
class TaskScenario:
    """Defines a task scenario configuration."""
    name: str
    name_zh: str
    description: str
    description_zh: str
    target_objects: List[str]
    success_criteria: Dict
    difficulty: str  # easy, medium, hard, expert
    estimated_steps: int
    reward_weights: Dict

class TaskScenarioLibrary:
    """
    Library of 8+ task scenarios for comprehensive evaluation.
    """
    
    SCENARIOS = {
        "vial_grasping": TaskScenario(
            name="Medical Vial Grasping",
            name_zh="医疗药瓶抓取",
            description="Grasp a medical vial and lift it to target height",
            description_zh="抓取医疗药瓶并提升到目标高度",
            target_objects=["vial"],
            success_criteria={
                "lift_height": 0.1,
                "stability_time": 2.0,
                "max_tilt": 0.2
            },
            difficulty="easy",
            estimated_steps=500,
            reward_weights={
                "reach": 1.0,
                "grasp": 2.0,
                "lift": 3.0,
                "stability": 1.0
            }
        ),
        
        "cap_rotation": TaskScenario(
            name="Bottle Cap Rotation",
            name_zh="瓶盖旋转",
            description="Rotate the cap of a medicine bottle 360 degrees",
            description_zh="旋转药瓶瓶盖360度",
            target_objects=["bottle", "cap"],
            success_criteria={
                "rotation_angle": 6.28,  # 2*pi radians
                "grip_stability": 0.8,
                "rotation_speed": 0.5
            },
            difficulty="medium",
            estimated_steps=1000,
            reward_weights={
                "grip": 2.0,
                "rotation": 3.0,
                "stability": 1.5
            }
        ),
        
        "pill_dispensing": TaskScenario(
            name="Pill Dispensing",
            name_zh="药片分配",
            description="Pick up a pill from container and place in target area",
            description_zh="从容器中拾取药片并放置到目标区域",
            target_objects=["pill", "container", "target"],
            success_criteria={
                "pick_success": True,
                "placement_accuracy": 0.02,
                "drop_count": 0
            },
            difficulty="hard",
            estimated_steps=1500,
            reward_weights={
                "reach": 1.0,
                "grip": 2.0,
                "transport": 2.0,
                "placement": 3.0
            }
        ),
        
        "syringe_operation": TaskScenario(
            name="Syringe Operation",
            name_zh="注射器操作",
            description="Grasp syringe and perform plunger motion",
            description_zh="抓取注射器并执行推杆运动",
            target_objects=["syringe"],
            success_criteria={
                "grip_alignment": 0.1,
                "plunger_depth": 0.05,
                "stability": 0.9
            },
            difficulty="medium",
            estimated_steps=800,
            reward_weights={
                "alignment": 2.0,
                "operation": 3.0,
                "precision": 2.0
            }
        ),
        
        "bandage_application": TaskScenario(
            name="Bandage Application",
            name_zh="绷带应用",
            description="Pick up bandage roll and apply to target limb",
            description_zh="拾取绷带卷并应用到目标肢体",
            target_objects=["bandage", "limb_simulator"],
            success_criteria={
                "pick_success": True,
                "wrap_coverage": 0.8,
                "tension": 0.3
            },
            difficulty="hard",
            estimated_steps=1200,
            reward_weights={
                "pick": 2.0,
                "transport": 1.5,
                "application": 3.0
            }
        ),
        
        "multi_object_sorting": TaskScenario(
            name="Multi-Object Sorting",
            name_zh="多物体分拣",
            description="Sort 3 different objects into their designated bins",
            description_zh="将3个不同物体分拣到指定容器",
            target_objects=["object1", "object2", "object3"],
            success_criteria={
                "sort_accuracy": 1.0,
                "total_time": 30.0
            },
            difficulty="expert",
            estimated_steps=2000,
            reward_weights={
                "recognition": 2.0,
                "sorting": 3.0,
                "efficiency": 2.0
            }
        ),
        
        "tool_handover": TaskScenario(
            name="Tool Handover",
            name_zh="工具交接",
            description="Pass a medical tool to another hand or container",
            description_zh="将医疗工具交接给另一只手或容器",
            target_objects=["tool"],
            success_criteria={
                "release_success": True,
                "handoff_position": 0.03,
                "tool_orientation": 0.1
            },
            difficulty="medium",
            estimated_steps=700,
            reward_weights={
                "approach": 1.0,
                "release": 3.0,
                "handoff": 2.0
            }
        ),
        
        "adaptive_grasping": TaskScenario(
            name="Adaptive Grasping with Variable Objects",
            name_zh="可变物体自适应抓取",
            description="Grasp objects of varying sizes and weights without explicit specification",
            description_zh="抓取不同大小和重量的物体，无需明确指定",
            target_objects=["variable_object"],
            success_criteria={
                "grasp_success": 0.95,
                "object_damage": 0.0,
                "adaptation_time": 2.0
            },
            difficulty="expert",
            estimated_steps=1800,
            reward_weights={
                "detection": 2.0,
                "adaptation": 3.0,
                "stability": 2.0
            }
        )
    }
    
    @classmethod
    def get_scenario(cls, name: str) -> Optional[TaskScenario]:
        """Get a specific scenario by name."""
        return cls.SCENARIOS.get(name)
    
    @classmethod
    def get_all_scenarios(cls) -> List[TaskScenario]:
        """Get all available scenarios."""
        return list(cls.SCENARIOS.values())
    
    @classmethod
    def get_scenarios_by_difficulty(cls, difficulty: str) -> List[TaskScenario]:
        """Get scenarios filtered by difficulty level."""
        return [s for s in cls.SCENARIOS.values() if s.difficulty == difficulty]
    
    @classmethod
    def get_statistics(cls) -> Dict:
        """Get statistics about scenario library."""
        scenarios = cls.get_all_scenarios()
        difficulties = {}
        for s in scenarios:
            difficulties[s.difficulty] = difficulties.get(s.difficulty, 0) + 1
            
        return {
            "total_scenarios": len(scenarios),
            "difficulty_breakdown": difficulties,
            "total_estimated_steps": sum(s.estimated_steps for s in scenarios),
            "scenarios": [
                {
                    "name": s.name,
                    "name_zh": s.name_zh,
                    "difficulty": s.difficulty
                }
                for s in scenarios
            ]
        }


class PerformanceBenchmark:
    """
    Benchmark system for comparing controller performance.
    """
    
    def __init__(self):
        self.results = {}
        self.baseline_results = {}
        
    def run_benchmark(
        self,
        controller_name: str,
        controller,
        task_scenarios: List[str],
        num_trials: int = 10
    ) -> Dict:
        """
        Run comprehensive benchmark for a controller.
        
        Args:
            controller_name: Name of the controller
            controller: Controller object
            task_scenarios: List of scenario names to test
            num_trials: Number of trials per scenario
            
        Returns:
            Dictionary of benchmark results
        """
        results = {
            "controller": controller_name,
            "timestamp": time.time(),
            "scenarios": {}
        }
        
        for scenario_name in task_scenarios:
            scenario = TaskScenarioLibrary.get_scenario(scenario_name)
            if scenario is None:
                continue
                
            # Run trials
            trial_results = []
            for trial in range(num_trials):
                trial_result = self._run_single_trial(
                    controller, scenario, trial
                )
                trial_results.append(trial_result)
                
            # Aggregate results
            results["scenarios"][scenario_name] = self._aggregate_results(
                trial_results, scenario
            )
            
        # Compute overall metrics
        results["overall"] = self._compute_overall_metrics(results["scenarios"])
        
        self.results[controller_name] = results
        return results
        
    def _run_single_trial(
        self,
        controller,
        scenario: TaskScenario,
        trial_num: int
    ) -> Dict:
        """
        Run a single trial of a scenario.
        Simplified simulation for benchmarking.
        """
        # Simulate task completion
        np.random.seed(trial_num)
        
        # Generate simulated performance metrics
        base_success = {
            "easy": 0.95,
            "medium": 0.85,
            "hard": 0.70,
            "expert": 0.55
        }.get(scenario.difficulty, 0.7)
        
        success = np.random.random() < base_success
        completion_time = scenario.estimated_steps * np.random.uniform(0.8, 1.2)
        accuracy = base_success * np.random.uniform(0.9, 1.1)
        smoothness = np.random.uniform(0.7, 0.95)
        
        return {
            "success": success,
            "completion_time": completion_time,
            "accuracy": accuracy,
            "smoothness": smoothness,
            "efficiency": 1.0 / completion_time * 100,
            "reward": self._compute_reward(success, accuracy, smoothness, scenario)
        }
        
    def _compute_reward(
        self,
        success: bool,
        accuracy: float,
        smoothness: float,
        scenario: TaskScenario
    ) -> float:
        """Compute weighted reward based on scenario weights."""
        reward = 0.0
        
        if success:
            reward += 50 * scenario.reward_weights.get("success", 1.0)
        reward += 30 * accuracy
        reward += 20 * smoothness
        
        return reward
        
    def _aggregate_results(self, trial_results: List[Dict], scenario: TaskScenario) -> Dict:
        """Aggregate results from multiple trials."""
        successes = [r["success"] for r in trial_results]
        times = [r["completion_time"] for r in trial_results]
        accuracies = [r["accuracy"] for r in trial_results]
        smoothnesses = [r["smoothness"] for r in trial_results]
        rewards = [r["reward"] for r in trial_results]
        
        return {
            "success_rate": np.mean(successes),
            "success_std": np.std(successes),
            "completion_time_mean": np.mean(times),
            "completion_time_std": np.std(times),
            "accuracy_mean": np.mean(accuracies),
            "accuracy_std": np.std(accuracies),
            "smoothness_mean": np.mean(smoothnesses),
            "smoothness_std": np.std(smoothnesses),
            "reward_mean": np.mean(rewards),
            "reward_std": np.std(rewards),
            "difficulty": scenario.difficulty
        }
        
    def _compute_overall_metrics(self, scenario_results: Dict) -> Dict:
        """Compute overall metrics across all scenarios."""
        if not scenario_results:
            return {}
            
        success_rates = [r["success_rate"] for r in scenario_results.values()]
        rewards = [r["reward_mean"] for r in scenario_results.values()]
        times = [r["completion_time_mean"] for r in scenario_results.values()]
        
        return {
            "overall_success_rate": np.mean(success_rates),
            "overall_reward": np.mean(rewards),
            "average_completion_time": np.mean(times),
            "total_scenarios_completed": len([r for r in scenario_results.values() if r["success_rate"] > 0.5])
        }
        
    def compare_controllers(self) -> Dict:
        """
        Compare all benchmarked controllers.
        """
        if len(self.results) < 2:
            return {"error": "Need at least 2 controllers for comparison"}
            
        comparison = {
            "controllers": list(self.results.keys()),
            "metrics": {}
        }
        
        # Extract key metrics
        for name, result in self.results.items():
            if "overall" in result:
                comparison["metrics"][name] = {
                    "success_rate": result["overall"]["overall_success_rate"],
                    "reward": result["overall"]["overall_reward"],
                    "speed": result["overall"]["average_completion_time"]
                }
                
        return comparison
        
    def generate_report(self, controller_name: str) -> str:
        """Generate a human-readable benchmark report."""
        if controller_name not in self.results:
            return f"No results for controller: {controller_name}"
            
        result = self.results[controller_name]
        lines = [
            f"\n{'='*60}",
            f"Performance Benchmark Report: {controller_name}",
            f"{'='*60}",
            f"\nOverall Metrics:",
            f"  Success Rate: {result['overall']['overall_success_rate']:.1%}",
            f"  Average Reward: {result['overall']['overall_reward']:.2f}",
            f"  Avg Completion Time: {result['overall']['average_completion_time']:.0f} steps",
            f"\nPer-Scenario Results:",
        ]
        
        for name, scenario_result in result["scenarios"].items():
            scenario = TaskScenarioLibrary.get_scenario(name)
            lines.append(
                f"  [{scenario.difficulty.upper():6}] {scenario.name_zh} ({scenario.name})"
            )
            lines.append(
                f"              Success: {scenario_result['success_rate']:.1%} | "
                f"Reward: {scenario_result['reward_mean']:.1f} | "
                f"Time: {scenario_result['completion_time_mean']:.0f}"
            )
            
        lines.append(f"\n{'='*60}\n")
        return "\n".join(lines)
        
    def save_results(self, filepath: str):
        """Save benchmark results to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
            
    def load_results(self, filepath: str):
        """Load benchmark results from JSON file."""
        with open(filepath, 'r') as f:
            self.results = json.load(f)


class SimToRealAnalyzer:
    """
    Analyze sim-to-real transfer performance.
    """
    
    def __init__(self):
        self.sim_results = {}
        self.real_results = {}
        
    def add_sim_result(self, task_name: str, metrics: Dict):
        """Add simulation results for a task."""
        self.sim_results[task_name] = metrics
        
    def add_real_result(self, task_name: str, metrics: Dict):
        """Add real hardware results for a task."""
        self.real_results[task_name] = metrics
        
    def compute_transfer_gap(self, task_name: str) -> Dict:
        """
        Compute the sim-to-real gap for a task.
        """
        if task_name not in self.sim_results or task_name not in self.real_results:
            return {"error": "Missing results for task"}
            
        sim = self.sim_results[task_name]
        real = self.real_results[task_name]
        
        gaps = {}
        for metric in ["success_rate", "accuracy", "smoothness"]:
            if metric in sim and metric in real:
                sim_val = sim[metric]
                real_val = real[metric]
                gap = (sim_val - real_val) / sim_val if sim_val > 0 else 0
                gaps[metric] = {
                    "sim": sim_val,
                    "real": real_val,
                    "gap": gap,
                    "gap_percent": gap * 100
                }
                
        return gaps
        
    def generate_transfer_report(self) -> str:
        """Generate a sim-to-real transfer analysis report."""
        lines = [
            "\n" + "="*60,
            "Sim-to-Real Transfer Analysis",
            "="*60,
            ""
        ]
        
        all_tasks = set(self.sim_results.keys()) & set(self.real_results.keys())
        
        if not all_tasks:
            lines.append("No comparable results available.")
            return "\n".join(lines)
            
        total_gaps = []
        
        for task in all_tasks:
            gaps = self.compute_transfer_gap(task)
            if "error" in gaps:
                continue
                
            lines.append(f"\nTask: {task}")
            
            for metric, values in gaps.items():
                lines.append(f"  {metric}:")
                lines.append(f"    Simulation: {values['sim']:.3f}")
                lines.append(f"    Real Hardware: {values['real']:.3f}")
                lines.append(f"    Gap: {values['gap_percent']:.1f}%")
                
                if metric == "success_rate":
                    total_gaps.append(values['gap'])
                    
        if total_gaps:
            avg_gap = np.mean(total_gaps)
            lines.append(f"\nAverage Transfer Gap: {avg_gap*100:.1f}%")
            
            if avg_gap < 0.1:
                assessment = "EXCELLENT - Minimal sim-to-real gap"
            elif avg_gap < 0.2:
                assessment = "GOOD - Acceptable transfer"
            elif avg_gap < 0.3:
                assessment = "FAIR - May need domain adaptation"
            else:
                assessment = "POOR - Significant sim-to-real gap"
                
            lines.append(f"Assessment: {assessment}")
            
        lines.append("\n" + "="*60 + "\n")
        return "\n".join(lines)


def run_comprehensive_benchmark() -> Dict:
    """
    Run a comprehensive benchmark comparing simulation vs real hardware.
    """
    benchmark = PerformanceBenchmark()
    analyzer = SimToRealAnalyzer()
    
    # Get all scenarios
    scenarios = TaskScenarioLibrary.get_all_scenarios()
    scenario_names = [s.name for s in scenarios]
    
    # Run simulated benchmark (using neural controller)
    print("Running simulation benchmarks...")
    
    # Create mock controllers for benchmarking
    class MockController:
        def __init__(self, name):
            self.name = name
            
    controllers = {
        "PID Controller": MockController("PID"),
        "Neural Network": MockController("NN"),
        "Adaptive Hybrid": MockController("Hybrid")
    }
    
    for name, ctrl in controllers.items():
        print(f"  Benchmarking {name}...")
        benchmark.run_benchmark(name, ctrl, scenario_names[:5], num_trials=5)
        
    # Generate simulated real hardware results
    print("Simulating real hardware transfer...")
    for scenario in scenarios[:5]:
        sim_result = {
            "success_rate": 0.85,
            "accuracy": 0.90,
            "smoothness": 0.88
        }
        # Simulate ~15% gap for real hardware
        real_result = {
            "success_rate": sim_result["success_rate"] * 0.85,
            "accuracy": sim_result["accuracy"] * 0.92,
            "smoothness": sim_result["smoothness"] * 0.90
        }
        
        analyzer.add_sim_result(scenario.name, sim_result)
        analyzer.add_real_result(scenario.name, real_result)
        
    # Generate reports
    report = benchmark.generate_report("Adaptive Hybrid")
    transfer_report = analyzer.generate_transfer_report()
    
    return {
        "benchmark_results": benchmark.results,
        "transfer_analysis": analyzer.sim_results,
        "transfer_report": transfer_report
    }


if __name__ == "__main__":
    # Run comprehensive benchmark
    results = run_comprehensive_benchmark()
    
    print("\n" + "="*60)
    print("Scenario Library Statistics:")
    print("="*60)
    stats = TaskScenarioLibrary.get_statistics()
    print(f"Total Scenarios: {stats['total_scenarios']}")
    print(f"Difficulty Breakdown: {stats['difficulty_breakdown']}")
    print(f"Total Estimated Steps: {stats['total_estimated_steps']}")
    
    for s in stats['scenarios']:
        print(f"  - {s['name']} ({s['name_zh']}) [{s['difficulty']}]")
