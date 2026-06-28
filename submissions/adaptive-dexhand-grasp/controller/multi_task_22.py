#!/usr/bin/env python3
"""
22-Step Multi-Task Planner with Tactile-Visual Fusion
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class TaskPhase(Enum):
    PERCEPTION = "perception"
    MANIPULATION = "manipulation"
    ASSEMBLY = "assembly"
    VERIFICATION = "verification"

@dataclass
class TaskStep:
    """Definition of a single task step."""
    step: int
    action: str
    phase: TaskPhase
    description: str
    target_force: float
    recovery_strategy: str

class MultiTaskPlanner22:
    """22-step multi-task planner with tactile-visual fusion."""
    
    def __init__(self):
        self.task_sequence = self._define_22_step_sequence()
        self.current_step = 0
        self.step_results: List[Dict] = []
    
    def _define_22_step_sequence(self) -> List[TaskStep]:
        """Define 22-step task sequence."""
        return [
            # Phase 1: Perception (Steps 1-3)
            TaskStep(1, "visual_scan", TaskPhase.PERCEPTION,
                    "Scan workspace with camera", 0.0, "none"),
            TaskStep(2, "tactile_scan", TaskPhase.PERCEPTION,
                    "Probe table surface with fingertips", 0.5, "realign"),
            TaskStep(3, "object_detection", TaskPhase.PERCEPTION,
                    "Detect and classify objects", 0.0, "none"),
            
            # Phase 2: First Object Manipulation (Steps 4-9)
            TaskStep(4, "approach_object_1", TaskPhase.MANIPULATION,
                    "Move hand to first object", 0.5, "retry_approach"),
            TaskStep(5, "pre_grasp_shape", TaskPhase.MANIPULATION,
                    "Shape fingers to match object geometry", 1.0, "realign"),
            TaskStep(6, "grasp_object_1", TaskPhase.MANIPULATION,
                    "Close fingers with adaptive force", 2.15, "increase_force"),
            TaskStep(7, "lift_object_1", TaskPhase.MANIPULATION,
                    "Lift object with slip monitoring", 2.20, "increase_force"),
            TaskStep(8, "transport_to_target_a", TaskPhase.MANIPULATION,
                    "Transport to target A", 2.10, "realign"),
            TaskStep(9, "place_at_target_a", TaskPhase.MANIPULATION,
                    "Place object at target A", 2.05, "realign"),
            
            # Phase 3: Second Object Manipulation (Steps 10-15)
            TaskStep(10, "release_object_1", TaskPhase.MANIPULATION,
                    "Release first object", 0.0, "none"),
            TaskStep(11, "approach_object_2", TaskPhase.MANIPULATION,
                    "Move to second object", 0.5, "retry_approach"),
            TaskStep(12, "pre_grasp_shape_2", TaskPhase.MANIPULATION,
                    "Shape fingers for second object", 1.0, "realign"),
            TaskStep(13, "grasp_object_2", TaskPhase.MANIPULATION,
                    "Grasp second object", 2.18, "increase_force"),
            TaskStep(14, "lift_object_2", TaskPhase.MANIPULATION,
                    "Lift second object", 2.25, "increase_force"),
            TaskStep(15, "transport_to_stack", TaskPhase.MANIPULATION,
                    "Transport to stack location", 2.12, "realign"),
            
            # Phase 4: Assembly (Steps 16-19)
            TaskStep(16, "align_with_target", TaskPhase.ASSEMBLY,
                    "Align object with target using visual feedback", 2.08, "realign"),
            TaskStep(17, "precision_place", TaskPhase.ASSEMBLY,
                    "Place with force control (0.1mm tolerance)", 2.05, "realign"),
            TaskStep(18, "release_object_2", TaskPhase.ASSEMBLY,
                    "Release second object", 0.0, "none"),
            TaskStep(19, "verify_contact", TaskPhase.ASSEMBLY,
                    "Verify stable contact with tactile", 0.5, "regrasp"),
            
            # Phase 5: Verification (Steps 20-22)
            TaskStep(20, "visual_inspection", TaskPhase.VERIFICATION,
                    "Visual inspection of stack", 0.0, "none"),
            TaskStep(21, "stability_test", TaskPhase.VERIFICATION,
                    "Apply small force to test stability", 0.3, "regrasp"),
            TaskStep(22, "retreat_home", TaskPhase.VERIFICATION,
                    "Retreat to home position", 0.0, "none"),
        ]
    
    def get_step(self, step_number: int) -> Optional[TaskStep]:
        """Get task step by number."""
        for task in self.task_sequence:
            if task.step == step_number:
                return task
        return None
    
    def execute_step(self, step_number: int, 
                     tactile_values: Dict[str, float],
                     visual_features: Optional[Dict] = None) -> Dict:
        """Execute a single task step with tactile-visual fusion."""
        task = self.get_step(step_number)
        if not task:
            return {"success": False, "error": "Invalid step number"}
        
        # Tactile-visual fusion
        fusion_result = self._tactile_visual_fusion(tactile_values, visual_features)
        
        # Execute based on phase
        if task.phase == TaskPhase.PERCEPTION:
            success = self._execute_perception(task, tactile_values, visual_features)
        elif task.phase == TaskPhase.MANIPULATION:
            success = self._execute_manipulation(task, tactile_values, fusion_result)
        elif task.phase == TaskPhase.ASSEMBLY:
            success = self._execute_assembly(task, tactile_values, fusion_result)
        else:  # VERIFICATION
            success = self._execute_verification(task, tactile_values)
        
        result = {
            "step": step_number,
            "action": task.action,
            "phase": task.phase.value,
            "success": success,
            "force": task.target_force,
            "fusion_confidence": fusion_result.get("confidence", 0.0)
        }
        
        self.step_results.append(result)
        return result
    
    def _tactile_visual_fusion(self, tactile: Dict[str, float], 
                               visual: Optional[Dict]) -> Dict:
        """Fuse tactile and visual information."""
        # Tactile confidence
        tactile_conf = np.mean(list(tactile.values()))
        
        # Visual confidence
        visual_conf = visual.get("confidence", 0.5) if visual else 0.5
        
        # Weighted fusion (tactile weighted higher for manipulation)
        fusion_conf = 0.7 * tactile_conf + 0.3 * visual_conf
        
        # Object detection
        object_detected = tactile_conf > 0.1 or (visual and visual.get("object_detected", False))
        
        return {
            "confidence": fusion_conf,
            "object_detected": object_detected,
            "tactile_confidence": tactile_conf,
            "visual_confidence": visual_conf
        }
    
    def _execute_perception(self, task: TaskStep, 
                           tactile: Dict[str, float],
                           visual: Optional[Dict]) -> bool:
        """Execute perception phase."""
        if task.action == "visual_scan":
            return visual is not None and visual.get("workspace_scanned", False)
        elif task.action == "tactile_scan":
            return np.mean(list(tactile.values())) > 0.1
        elif task.action == "object_detection":
            return visual is not None and visual.get("object_detected", False)
        return True
    
    def _execute_manipulation(self, task: TaskStep,
                             tactile: Dict[str, float],
                             fusion: Dict) -> bool:
        """Execute manipulation phase."""
        # Check if object is detected
        if not fusion["object_detected"]:
            return False
        
        # Check force requirements
        if task.target_force > 0:
            # Simulate force application
            actual_force = task.target_force + np.random.normal(0, 0.1)
            
            # Check for slip
            if np.mean(list(tactile.values())) < 0.05:
                return False  # Slip detected
        
        return True
    
    def _execute_assembly(self, task: TaskStep,
                         tactile: Dict[str, float],
                         fusion: Dict) -> bool:
        """Execute assembly phase with precision control."""
        if task.action == "precision_place":
            # Require high confidence for precision
            return fusion["confidence"] > 0.7
        elif task.action == "verify_contact":
            return np.mean(list(tactile.values())) > 0.3
        return True
    
    def _execute_verification(self, task: TaskStep,
                             tactile: Dict[str, float]) -> bool:
        """Execute verification phase."""
        if task.action == "stability_test":
            # Small force test
            return np.mean(list(tactile.values())) > 0.2
        return True
    
    def execute_full_task(self) -> List[Dict]:
        """Execute all 22 steps."""
        results = []
        
        for task in self.task_sequence:
            # Simulate sensor data
            tactile = {f"finger_{i}": np.random.uniform(0.1, 0.9) 
                      for i in range(5)}
            visual = {
                "workspace_scanned": True,
                "object_detected": True,
                "confidence": np.random.uniform(0.7, 0.95)
            }
            
            result = self.execute_step(task.step, tactile, visual)
            results.append(result)
        
        return results

class TactileVisualFusion:
    """Tactile-visual fusion system for adaptive grasping."""
    
    def __init__(self):
        self.tactile_weights = [0.2, 0.2, 0.2, 0.2, 0.2]  # 5 fingers
        self.visual_weight = 0.3
        self.fusion_history: List[Dict] = []
    
    def fuse(self, tactile_values: Dict[str, float],
             visual_features: Dict) -> Dict:
        """Fuse tactile and visual information."""
        # Tactile processing
        tactile_array = list(tactile_values.values())
        tactile_mean = np.mean(tactile_array)
        tactile_std = np.std(tactile_array)
        
        # Visual processing
        visual_conf = visual_features.get("confidence", 0.5)
        object_shape = visual_features.get("shape", "unknown")
        
        # Fusion
        fusion_confidence = (1 - self.visual_weight) * tactile_mean + \
                           self.visual_weight * visual_conf
        
        # Object classification
        if object_shape == "sphere":
            grasp_strategy = "spherical"
        elif object_shape == "cylinder":
            grasp_strategy = "cylindrical"
        elif object_shape == "cube":
            grasp_strategy = "prismatic"
        else:
            grasp_strategy = "adaptive"
        
        result = {
            "fusion_confidence": fusion_confidence,
            "tactile_mean": tactile_mean,
            "tactile_std": tactile_std,
            "visual_confidence": visual_conf,
            "grasp_strategy": grasp_strategy,
            "object_detected": tactile_mean > 0.1 or visual_conf > 0.5
        }
        
        self.fusion_history.append(result)
        return result
    
    def get_optimal_force(self, fusion_result: Dict) -> float:
        """Calculate optimal grasp force from fusion result."""
        base_force = 2.0
        
        # Adjust based on object type
        if fusion_result["grasp_strategy"] == "spherical":
            force_factor = 0.9  # Less force for spheres
        elif fusion_result["grasp_strategy"] == "cylindrical":
            force_factor = 1.0  # Normal force
        elif fusion_result["grasp_strategy"] == "prismatic":
            force_factor = 1.1  # More force for cubes
        else:
            force_factor = 1.0
        
        # Adjust based on confidence
        confidence_factor = 0.8 + 0.4 * fusion_result["fusion_confidence"]
        
        return base_force * force_factor * confidence_factor

# Example usage
if __name__ == "__main__":
    planner = MultiTaskPlanner22()
    fusion = TactileVisualFusion()
    
    print("="*60)
    print("22-STEP MULTI-TASK EXECUTION")
    print("="*60)
    
    # Execute full task
    results = planner.execute_full_task()
    
    # Print results
    successes = sum(1 for r in results if r["success"])
    print(f"\nTotal Steps: {len(results)}")
    print(f"Successful: {successes}/{len(results)} ({successes/len(results)*100:.1f}%)")
    
    print("\nStep-by-Step Results:")
    print("-"*60)
    for r in results:
        status = "✓" if r["success"] else "✗"
        print(f"  Step {r['step']:2d}: {status} {r['action']:<25} "
              f"Force={r['force']:.2f}N Fusion={r['fusion_confidence']:.2f}")
    
    # Phase summary
    print("\n" + "="*60)
    print("PHASE SUMMARY")
    print("="*60)
    
    phases = {}
    for r in results:
        phase = r["phase"]
        if phase not in phases:
            phases[phase] = {"total": 0, "success": 0}
        phases[phase]["total"] += 1
        if r["success"]:
            phases[phase]["success"] += 1
    
    for phase, stats in phases.items():
        rate = stats["success"] / stats["total"] * 100
        print(f"  {phase:<15}: {stats['success']}/{stats['total']} = {rate:.1f}%")
