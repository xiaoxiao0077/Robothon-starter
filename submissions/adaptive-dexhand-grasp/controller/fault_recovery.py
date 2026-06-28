#!/usr/bin/env python3
"""
Fault Recovery Module - Handles grasp failures and recovery strategies
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class FaultType(Enum):
    SLIP = "slip"
    COLLISION = "collision"
    MISALIGNMENT = "misalignment"
    GRASP_FAILURE = "grasp_failure"
    OBJECT_DROP = "object_drop"

class RecoveryStrategy(Enum):
    INCREASE_FORCE = "increase_force"
    REALIGN = "realign"
    REGRASP = "regrasp"
    RETRY_APPROACH = "retry_approach"
    ABORT = "abort"

@dataclass
class FaultEvent:
    """Record of a fault event."""
    fault_type: FaultType
    timestamp: float
    finger_name: Optional[str]
    force_at_fault: float
    recovery_strategy: RecoveryStrategy
    recovery_success: bool

class FaultRecoverySystem:
    """Manages fault detection and recovery strategies."""
    
    def __init__(self, max_recovery_attempts: int = 3):
        self.max_recovery_attempts = max_recovery_attempts
        self.recovery_attempts = 0
        self.fault_history: List[FaultEvent] = []
        self.recovery_strategies = self._init_recovery_strategies()
    
    def _init_recovery_strategies(self) -> Dict[FaultType, List[RecoveryStrategy]]:
        """Initialize recovery strategies for each fault type."""
        return {
            FaultType.SLIP: [
                RecoveryStrategy.INCREASE_FORCE,
                RecoveryStrategy.REALIGN,
                RecoveryStrategy.REGRASP
            ],
            FaultType.COLLISION: [
                RecoveryStrategy.REALIGN,
                RecoveryStrategy.RETRY_APPROACH,
                RecoveryStrategy.ABORT
            ],
            FaultType.MISALIGNMENT: [
                RecoveryStrategy.REALIGN,
                RecoveryStrategy.RETRY_APPROACH,
                RecoveryStrategy.ABORT
            ],
            FaultType.GRASP_FAILURE: [
                RecoveryStrategy.INCREASE_FORCE,
                RecoveryStrategy.REGRASP,
                RecoveryStrategy.ABORT
            ],
            FaultType.OBJECT_DROP: [
                RecoveryStrategy.REGRASP,
                RecoveryStrategy.RETRY_APPROACH,
                RecoveryStrategy.ABORT
            ]
        }
    
    def detect_fault(self, tactile_values: Dict[str, float], 
                     expected_forces: Dict[str, float]) -> Optional[FaultType]:
        """Detect fault from sensor readings."""
        # Check for slip (sudden drop in tactile)
        for finger, value in tactile_values.items():
            if value < 0.05 and expected_forces.get(finger, 0) > 0.1:
                return FaultType.SLIP
        
        # Check for collision (sudden spike in force)
        for finger, force in expected_forces.items():
            if force > 5.0:  # Force threshold
                return FaultType.COLLISION
        
        # Check for misalignment (uneven force distribution)
        forces = list(expected_forces.values())
        if len(forces) > 1:
            force_std = np.std(forces)
            if force_std > 1.0:  # High variance
                return FaultType.MISALIGNMENT
        
        return None
    
    def select_recovery_strategy(self, fault_type: FaultType) -> RecoveryStrategy:
        """Select appropriate recovery strategy."""
        if self.recovery_attempts >= self.max_recovery_attempts:
            return RecoveryStrategy.ABORT
        
        strategies = self.recovery_strategies.get(fault_type, [])
        if not strategies:
            return RecoveryStrategy.ABORT
        
        # Select strategy based on recovery attempts
        strategy_idx = min(self.recovery_attempts, len(strategies) - 1)
        return strategies[strategy_idx]
    
    def execute_recovery(self, strategy: RecoveryStrategy, 
                         current_forces: Dict[str, float]) -> Dict[str, float]:
        """Execute recovery strategy and return new forces."""
        self.recovery_attempts += 1
        
        if strategy == RecoveryStrategy.INCREASE_FORCE:
            # Increase force by 20%
            return {k: v * 1.2 for k, v in current_forces.items()}
        
        elif strategy == RecoveryStrategy.REALIGN:
            # Reduce force and re-approach
            return {k: v * 0.5 for k, v in current_forces.items()}
        
        elif strategy == RecoveryStrategy.REGRASP:
            # Release and re-grasp
            return {k: 0.0 for k in current_forces.keys()}
        
        elif strategy == RecoveryStrategy.RETRY_APPROACH:
            # Reset to approach position
            return {k: 0.0 for k in current_forces.keys()}
        
        else:  # ABORT
            return {k: 0.0 for k in current_forces.keys()}
    
    def handle_fault(self, fault_type: FaultType, 
                     current_forces: Dict[str, float],
                     finger_name: Optional[str] = None) -> Tuple[bool, Dict[str, float]]:
        """Handle fault with recovery."""
        # Record fault event
        event = FaultEvent(
            fault_type=fault_type,
            timestamp=0.0,  # Would use time.time() in real implementation
            finger_name=finger_name,
            force_at_fault=sum(current_forces.values()),
            recovery_strategy=RecoveryStrategy.ABORT,  # Will be updated
            recovery_success=False
        )
        
        # Select recovery strategy
        strategy = self.select_recovery_strategy(fault_type)
        event.recovery_strategy = strategy
        
        # Execute recovery
        new_forces = self.execute_recovery(strategy, current_forces)
        
        # Check if recovery was successful
        recovery_success = strategy != RecoveryStrategy.ABORT
        event.recovery_success = recovery_success
        
        # Record event
        self.fault_history.append(event)
        
        return recovery_success, new_forces
    
    def reset(self):
        """Reset recovery system."""
        self.recovery_attempts = 0
        self.fault_history = []
    
    def get_recovery_stats(self) -> Dict:
        """Get recovery statistics."""
        if not self.fault_history:
            return {"total_faults": 0, "recovery_rate": 0.0}
        
        total_faults = len(self.fault_history)
        successful_recoveries = sum(1 for e in self.fault_history if e.recovery_success)
        
        return {
            "total_faults": total_faults,
            "successful_recoveries": successful_recoveries,
            "recovery_rate": successful_recoveries / total_faults,
            "fault_types": {ft.value: sum(1 for e in self.fault_history if e.fault_type == ft) 
                           for ft in FaultType}
        }

class AdaptiveForceController:
    """Adaptive force control with fault recovery."""
    
    def __init__(self, target_force: float = 2.0):
        self.target_force = target_force
        self.current_force = target_force
        self.fault_recovery = FaultRecoverySystem()
        self.force_history: List[float] = []
    
    def update_force(self, tactile_values: Dict[str, float], 
                     current_forces: Dict[str, float]) -> Dict[str, float]:
        """Update forces based on tactile feedback."""
        # Detect faults
        fault = self.fault_recovery.detect_fault(tactile_values, current_forces)
        
        if fault:
            # Handle fault
            success, new_forces = self.fault_recovery.handle_fault(
                fault, current_forces
            )
            
            if not success:
                # Recovery failed, use safe forces
                return {k: self.target_force * 0.5 for k in current_forces.keys()}
            
            return new_forces
        
        # No fault, apply adaptive control
        adaptive_forces = {}
        for finger, force in current_forces.items():
            tactile = tactile_values.get(finger, 0.0)
            
            if tactile < 0.1:  # No contact
                # Increase force to find contact
                adaptive_forces[finger] = force * 1.1
            elif tactile > 0.8:  # Too much contact
                # Reduce force to prevent damage
                adaptive_forces[finger] = force * 0.9
            else:
                # Good contact, maintain force
                adaptive_forces[finger] = force
        
        self.force_history.append(np.mean(list(adaptive_forces.values())))
        return adaptive_forces
    
    def get_force_stats(self) -> Dict:
        """Get force control statistics."""
        if not self.force_history:
            return {"mean_force": 0.0, "std_force": 0.0}
        
        return {
            "mean_force": float(np.mean(self.force_history)),
            "std_force": float(np.std(self.force_history)),
            "min_force": float(np.min(self.force_history)),
            "max_force": float(np.max(self.force_history))
        }

# Example usage
if __name__ == "__main__":
    # Test fault recovery
    recovery = FaultRecoverySystem(max_recovery_attempts=3)
    
    # Simulate slip detection
    tactile_values = {"thumb": 0.02, "index": 0.05, "middle": 0.03}
    current_forces = {"thumb": 2.0, "index": 2.0, "middle": 2.0}
    
    fault = recovery.detect_fault(tactile_values, current_forces)
    print(f"Detected fault: {fault}")
    
    if fault:
        success, new_forces = recovery.handle_fault(fault, current_forces)
        print(f"Recovery success: {success}")
        print(f"New forces: {new_forces}")
    
    # Print stats
    stats = recovery.get_recovery_stats()
    print(f"\nRecovery stats: {stats}")
