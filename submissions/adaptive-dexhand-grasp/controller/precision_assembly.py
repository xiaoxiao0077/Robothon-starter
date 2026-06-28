#!/usr/bin/env python3
"""
Precision Assembly Module - Peg-in-hole task with force control
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class AssemblyPhase(Enum):
    APPROACH = "approach"
    CONTACT = "contact"
    INSERTION = "insertion"
    COMPLETION = "completion"

@dataclass
class PegInHoleResult:
    """Result of peg-in-hole assembly attempt."""
    success: bool
    insertion_depth: float
    force_rmse: float
    alignment_error: float
    time_taken: float
    recovery_attempts: int

class PrecisionAssembly:
    """Precision assembly with peg-in-hole task."""
    
    def __init__(self, peg_diameter: float = 0.02, hole_diameter: float = 0.022,
                 tolerance: float = 0.001):
        self.peg_diameter = peg_diameter
        self.hole_diameter = hole_diameter
        self.tolerance = tolerance
        self.current_phase = AssemblyPhase.APPROACH
        self.recovery_attempts = 0
        self.max_recovery_attempts = 3
        
    def reset(self):
        """Reset assembly state."""
        self.current_phase = AssemblyPhase.APPROACH
        self.recovery_attempts = 0
    
    def calculate_alignment_error(self, peg_position: np.ndarray, 
                                 hole_position: np.ndarray) -> float:
        """Calculate alignment error between peg and hole."""
        return np.linalg.norm(peg_position - hole_position)
    
    def check_contact(self, force_z: float, threshold: float = 0.5) -> bool:
        """Check if peg has contacted hole surface."""
        return force_z > threshold
    
    def execute_insertion(self, initial_force: float = 2.0,
                         max_force: float = 5.0,
                         insertion_depth: float = 0.05) -> PegInHoleResult:
        """Execute peg-in-hole insertion with force control."""
        self.reset()
        
        # Simulate insertion process
        current_depth = 0.0
        forces = []
        alignment_errors = []
        start_time = 0.0
        
        # Phase 1: Approach
        self.current_phase = AssemblyPhase.APPROACH
        peg_position = np.array([0.0, 0.0, 0.1])
        hole_position = np.array([0.0, 0.0, 0.0])
        
        # Simulate alignment
        alignment_error = self.calculate_alignment_error(peg_position, hole_position)
        alignment_errors.append(alignment_error)
        
        # Phase 2: Contact
        self.current_phase = AssemblyPhase.CONTACT
        contact_force = initial_force + np.random.normal(0, 0.1)
        forces.append(contact_force)
        
        # Phase 3: Insertion
        self.current_phase = AssemblyPhase.INSERTION
        
        # Simulate insertion with force control
        while current_depth < insertion_depth:
            # Apply force
            force = initial_force + np.random.normal(0, 0.2)
            
            # Check for jamming
            if force > max_force:
                # Jam detected - attempt recovery
                if self.recovery_attempts < self.max_recovery_attempts:
                    self.recovery_attempts += 1
                    # Reduce force and realign
                    force = initial_force * 0.5
                    alignment_error *= 0.8  # Improve alignment
                else:
                    # Max recovery attempts exceeded
                    return PegInHoleResult(
                        success=False,
                        insertion_depth=current_depth,
                        force_rmse=np.sqrt(np.mean(np.array(forces)**2)),
                        alignment_error=alignment_error,
                        time_taken=1.0,
                        recovery_attempts=self.recovery_attempts
                    )
            
            forces.append(force)
            alignment_errors.append(alignment_error)
            
            # Update depth
            current_depth += 0.001 + np.random.normal(0, 0.0001)
            
            # Simulate time
            start_time += 0.01
        
        # Phase 4: Completion
        self.current_phase = AssemblyPhase.COMPLETION
        
        # Calculate metrics
        force_rmse = np.sqrt(np.mean(np.array(forces)**2))
        final_alignment = alignment_errors[-1]
        
        return PegInHoleResult(
            success=True,
            insertion_depth=current_depth,
            force_rmse=force_rmse,
            alignment_error=final_alignment,
            time_taken=start_time,
            recovery_attempts=self.recovery_attempts
        )
    
    def run_benchmark(self, n_trials: int = 10) -> Dict:
        """Run peg-in-hole benchmark."""
        results = []
        
        for i in range(n_trials):
            # Vary parameters for each trial
            initial_force = 2.0 + np.random.normal(0, 0.2)
            result = self.execute_insertion(initial_force=initial_force)
            results.append(result)
        
        # Calculate statistics
        successes = sum(1 for r in results if r.success)
        insertion_depths = [r.insertion_depth for r in results]
        force_rmses = [r.force_rmse for r in results]
        alignment_errors = [r.alignment_error for r in results]
        
        return {
            "n_trials": n_trials,
            "successes": successes,
            "success_rate": successes / n_trials,
            "mean_insertion_depth": float(np.mean(insertion_depths)),
            "std_insertion_depth": float(np.std(insertion_depths)),
            "mean_force_rmse": float(np.mean(force_rmses)),
            "std_force_rmse": float(np.std(force_rmses)),
            "mean_alignment_error": float(np.mean(alignment_errors)),
            "std_alignment_error": float(np.std(alignment_errors)),
            "tolerance": self.tolerance
        }

class MultiTaskWithAssembly:
    """Extended multi-task planner with precision assembly."""
    
    def __init__(self):
        self.assembly = PrecisionAssembly()
        self.task_sequence = self._define_extended_sequence()
    
    def _define_extended_sequence(self) -> List[Dict]:
        """Define extended task sequence with assembly."""
        return [
            # Phase 1: Perception (Steps 1-3)
            {"step": 1, "action": "visual_scan", "phase": "Perception", "force": 0.0},
            {"step": 2, "action": "tactile_scan", "phase": "Perception", "force": 0.5},
            {"step": 3, "action": "object_detection", "phase": "Perception", "force": 0.0},
            
            # Phase 2: First Object Manipulation (Steps 4-9)
            {"step": 4, "action": "approach_object_1", "phase": "Manipulation", "force": 0.5},
            {"step": 5, "action": "pre_grasp_shape", "phase": "Manipulation", "force": 1.0},
            {"step": 6, "action": "grasp_object_1", "phase": "Manipulation", "force": 2.15},
            {"step": 7, "action": "lift_object_1", "phase": "Manipulation", "force": 2.20},
            {"step": 8, "action": "transport_to_target_a", "phase": "Manipulation", "force": 2.10},
            {"step": 9, "action": "place_at_target_a", "phase": "Manipulation", "force": 2.05},
            
            # Phase 3: Second Object Manipulation (Steps 10-15)
            {"step": 10, "action": "release_object_1", "phase": "Manipulation", "force": 0.0},
            {"step": 11, "action": "approach_object_2", "phase": "Manipulation", "force": 0.5},
            {"step": 12, "action": "pre_grasp_shape_2", "phase": "Manipulation", "force": 1.0},
            {"step": 13, "action": "grasp_object_2", "phase": "Manipulation", "force": 2.18},
            {"step": 14, "action": "lift_object_2", "phase": "Manipulation", "force": 2.25},
            {"step": 15, "action": "transport_to_stack", "phase": "Manipulation", "force": 2.12},
            
            # Phase 4: Assembly (Steps 16-19)
            {"step": 16, "action": "align_with_target", "phase": "Assembly", "force": 2.08},
            {"step": 17, "action": "precision_place", "phase": "Assembly", "force": 2.05},
            {"step": 18, "action": "release_object_2", "phase": "Assembly", "force": 0.0},
            {"step": 19, "action": "verify_contact", "phase": "Assembly", "force": 0.5},
            
            # Phase 5: Precision Assembly - Peg in Hole (Steps 20-25)
            {"step": 20, "action": "approach_peg", "phase": "PrecisionAssembly", "force": 0.5},
            {"step": 21, "action": "grasp_peg", "phase": "PrecisionAssembly", "force": 2.0},
            {"step": 22, "action": "align_peg_with_hole", "phase": "PrecisionAssembly", "force": 1.5},
            {"step": 23, "action": "contact_hole_surface", "phase": "PrecisionAssembly", "force": 2.0},
            {"step": 24, "action": "insert_peg", "phase": "PrecisionAssembly", "force": 2.5},
            {"step": 25, "action": "release_peg", "phase": "PrecisionAssembly", "force": 0.0},
            
            # Phase 6: Verification (Steps 26-28)
            {"step": 26, "action": "visual_inspection", "phase": "Verification", "force": 0.0},
            {"step": 27, "action": "stability_test", "phase": "Verification", "force": 0.3},
            {"step": 28, "action": "retreat_home", "phase": "Verification", "force": 0.0},
        ]
    
    def execute_full_task(self) -> List[Dict]:
        """Execute full 28-step task sequence."""
        results = []
        
        for task in self.task_sequence:
            step = task["step"]
            action = task["action"]
            phase = task["phase"]
            force = task["force"]
            
            # Execute precision assembly steps
            if phase == "PrecisionAssembly" and action == "insert_peg":
                assembly_result = self.assembly.execute_insertion(
                    initial_force=force,
                    insertion_depth=0.05
                )
                
                task_result = {
                    "step": step,
                    "action": action,
                    "phase": phase,
                    "success": assembly_result.success,
                    "force": force,
                    "insertion_depth": assembly_result.insertion_depth,
                    "force_rmse": assembly_result.force_rmse,
                    "alignment_error": assembly_result.alignment_error,
                    "recovery_attempts": assembly_result.recovery_attempts
                }
            else:
                # Simulate other steps
                success = np.random.random() < 0.98  # 98% success rate
                task_result = {
                    "step": step,
                    "action": action,
                    "phase": phase,
                    "success": success,
                    "force": force,
                    "insertion_depth": 0.0,
                    "force_rmse": 0.0,
                    "alignment_error": 0.0,
                    "recovery_attempts": 0
                }
            
            results.append(task_result)
        
        return results
    
    def run_benchmark(self, n_trials: int = 10) -> Dict:
        """Run benchmark for full task sequence."""
        all_results = []
        
        for trial in range(n_trials):
            results = self.execute_full_task()
            all_results.append(results)
        
        # Calculate statistics
        total_steps = len(self.task_sequence)
        trial_successes = []
        
        for trial_results in all_results:
            successes = sum(1 for r in trial_results if r["success"])
            trial_successes.append(successes / total_steps)
        
        return {
            "n_trials": n_trials,
            "total_steps": total_steps,
            "mean_success_rate": float(np.mean(trial_successes)),
            "std_success_rate": float(np.std(trial_successes)),
            "min_success_rate": float(np.min(trial_successes)),
            "max_success_rate": float(np.max(trial_successes))
        }

# Example usage
if __name__ == "__main__":
    print("="*60)
    print("PRECISION ASSEMBLY - PEG-IN-HOLE BENCHMARK")
    print("="*60)
    
    # Test peg-in-hole
    assembly = PrecisionAssembly()
    assembly_results = assembly.run_benchmark(n_trials=10)
    
    print("\nPeg-in-Hole Results:")
    print(f"  Success Rate: {assembly_results['success_rate']*100:.1f}%")
    print(f"  Mean Insertion Depth: {assembly_results['mean_insertion_depth']*1000:.2f}mm")
    print(f"  Mean Force RMSE: {assembly_results['mean_force_rmse']:.2f}N")
    print(f"  Mean Alignment Error: {assembly_results['mean_alignment_error']*1000:.2f}mm")
    print(f"  Tolerance: {assembly_results['tolerance']*1000:.1f}mm")
    
    # Test full task
    print("\n" + "="*60)
    print("FULL TASK WITH PRECISION ASSEMBLY")
    print("="*60)
    
    planner = MultiTaskWithAssembly()
    task_results = planner.run_benchmark(n_trials=10)
    
    print(f"\nFull Task Results:")
    print(f"  Total Steps: {task_results['total_steps']}")
    print(f"  Mean Success Rate: {task_results['mean_success_rate']*100:.1f}%")
    print(f"  Std Success Rate: {task_results['std_success_rate']*100:.1f}%")
