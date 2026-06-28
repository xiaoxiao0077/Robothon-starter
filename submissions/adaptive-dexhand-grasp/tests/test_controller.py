#!/usr/bin/env python3
"""
Unit tests for Dexterous Hand Controller
"""

import sys
import os
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from controller.dexterous_controller import DexterousHandController, GraspPhase, MultiStepTaskPlanner
from controller.fault_recovery import FaultRecoverySystem, FaultType, RecoveryStrategy

def test_controller_initialization():
    """Test controller initialization."""
    controller = DexterousHandController()
    
    assert controller.n_fingers == 5
    assert controller.n_joints_per_finger == 3
    assert len(controller.fingers) == 5
    assert controller.current_phase == GraspPhase.APPROACH
    assert controller.recovery_attempts == 0
    
    print("✓ Controller initialization test passed")

def test_finger_states():
    """Test finger state management."""
    controller = DexterousHandController()
    
    # Check initial finger states
    for name, finger in controller.fingers.items():
        assert finger.name == name
        assert finger.tactile_value == 0.0
        assert finger.force == 0.0
        assert finger.contact == False
    
    # Update tactile values
    tactile_values = {
        "thumb": 0.5,
        "index": 0.3,
        "middle": 0.4,
        "ring": 0.2,
        "pinky": 0.1
    }
    controller.update_tactile(tactile_values)
    
    for name, value in tactile_values.items():
        assert controller.fingers[name].tactile_value == value
        assert controller.fingers[name].contact == (value > 0.1)
    
    print("✓ Finger states test passed")

def test_contact_detection():
    """Test contact detection."""
    controller = DexterousHandController()
    
    # No contact initially
    assert controller.check_all_contact() == False
    
    # Update all fingers with contact
    tactile_values = {
        "thumb": 0.5,
        "index": 0.3,
        "middle": 0.4,
        "ring": 0.2,
        "pinky": 0.15  # Above threshold 0.1
    }
    controller.update_tactile(tactile_values)
    
    # All fingers should have contact
    assert controller.check_all_contact() == True
    
    # One finger loses contact
    controller.fingers["pinky"].tactile_value = 0.05
    controller.fingers["pinky"].contact = False
    assert controller.check_all_contact() == False
    
    print("✓ Contact detection test passed")

def test_adaptive_force():
    """Test adaptive force calculation."""
    controller = DexterousHandController()
    
    # No contact - increase force
    controller.update_tactile({"thumb": 0.0, "index": 0.0})
    force = controller.calculate_adaptive_force(2.0)
    assert force > 2.0  # Should increase
    
    # Full contact with even force
    controller.update_tactile({
        "thumb": 0.5, "index": 0.5, "middle": 0.5,
        "ring": 0.5, "pinky": 0.5
    })
    for finger in controller.fingers.values():
        finger.force = 2.0
    force = controller.calculate_adaptive_force(2.0)
    assert force == 2.0  # Should maintain
    
    print("✓ Adaptive force test passed")

def test_slip_detection():
    """Test slip detection."""
    controller = DexterousHandController()
    
    # No slip (good contact)
    controller.update_tactile({
        "thumb": 0.5, "index": 0.5, "middle": 0.5,
        "ring": 0.5, "pinky": 0.5
    })
    assert controller.detect_slip() == False
    
    # Slip detected (contact lost)
    controller.fingers["thumb"].contact = True
    controller.fingers["thumb"].tactile_value = 0.02
    assert controller.detect_slip() == True
    
    print("✓ Slip detection test passed")

def test_grasp_sequence():
    """Test complete grasp sequence."""
    controller = DexterousHandController()
    
    # Successful grasp
    result = controller.grasp(target_force=2.0)
    
    assert result.success == True
    assert result.phase == GraspPhase.RELEASE
    assert result.force > 0
    assert result.recovery_attempts == 0
    
    print("✓ Grasp sequence test passed")

def test_multi_step_task():
    """Test multi-step task execution."""
    controller = DexterousHandController()
    planner = MultiStepTaskPlanner(controller)
    
    results = planner.execute_task()
    
    assert len(results) == 15  # 15 steps
    
    # Check all steps completed
    successes = sum(1 for r in results if r["success"])
    assert successes == 15  # All should succeed in simulation
    
    print("✓ Multi-step task test passed")

def test_fault_recovery():
    """Test fault recovery system."""
    recovery = FaultRecoverySystem(max_recovery_attempts=3)
    
    # Test slip detection
    tactile_values = {"thumb": 0.02, "index": 0.05, "middle": 0.03}
    current_forces = {"thumb": 2.0, "index": 2.0, "middle": 2.0}
    
    fault = recovery.detect_fault(tactile_values, current_forces)
    assert fault == FaultType.SLIP
    
    # Test recovery
    success, new_forces = recovery.handle_fault(fault, current_forces)
    assert success == True
    assert all(f > 0 for f in new_forces.values())  # Forces should be positive
    
    print("✓ Fault recovery test passed")

def test_recovery_strategies():
    """Test different recovery strategies."""
    recovery = FaultRecoverySystem()
    
    # Test each fault type
    for fault_type in FaultType:
        strategy = recovery.select_recovery_strategy(fault_type)
        assert isinstance(strategy, RecoveryStrategy)
        
        # Test strategy execution
        current_forces = {"thumb": 2.0, "index": 2.0}
        new_forces = recovery.execute_recovery(strategy, current_forces)
        
        assert isinstance(new_forces, dict)
        assert all(isinstance(f, float) for f in new_forces.values())
    
    print("✓ Recovery strategies test passed")

def test_recovery_stats():
    """Test recovery statistics."""
    recovery = FaultRecoverySystem()
    
    # Simulate some faults
    for i in range(5):
        tactile_values = {"thumb": 0.02, "index": 0.05}
        current_forces = {"thumb": 2.0, "index": 2.0}
        
        fault = recovery.detect_fault(tactile_values, current_forces)
        if fault:
            recovery.handle_fault(fault, current_forces)
    
    stats = recovery.get_recovery_stats()
    
    assert "total_faults" in stats
    assert "successful_recoveries" in stats
    assert "recovery_rate" in stats
    assert stats["total_faults"] == 5
    
    print("✓ Recovery stats test passed")

def test_force_controller():
    """Test adaptive force controller."""
    from controller.fault_recovery import AdaptiveForceController
    
    controller = AdaptiveForceController(target_force=2.0)
    
    # Simulate control loop
    current_forces = {"thumb": 2.0, "index": 2.0, "middle": 2.0}
    
    # Good contact
    tactile_values = {"thumb": 0.5, "index": 0.5, "middle": 0.5}
    new_forces = controller.update_force(tactile_values, current_forces)
    
    assert isinstance(new_forces, dict)
    assert all(f > 0 for f in new_forces.values())
    
    # Get stats
    stats = controller.get_force_stats()
    assert "mean_force" in stats
    assert "std_force" in stats
    
    print("✓ Force controller test passed")

def run_all_tests():
    """Run all tests."""
    print("="*60)
    print("RUNNING UNIT TESTS")
    print("="*60)
    
    tests = [
        test_controller_initialization,
        test_finger_states,
        test_contact_detection,
        test_adaptive_force,
        test_slip_detection,
        test_grasp_sequence,
        test_multi_step_task,
        test_fault_recovery,
        test_recovery_strategies,
        test_recovery_stats,
        test_force_controller
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"TEST RESULTS: {passed}/{passed+failed} passed")
    print("="*60)
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
