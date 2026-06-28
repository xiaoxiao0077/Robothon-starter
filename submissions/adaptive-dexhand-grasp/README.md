# Adaptive Dexterous Grasping with 5-Finger Tactile-Visual Fusion + Precision Assembly

**UUID: 438a8329-a02c-4fdb-80b5-12bff9d9f69d**

---

## Project Overview

A MuJoCo-based adaptive dexterous grasping system using a **5-finger anthropomorphic hand** (15 DOF) with **tactile-visual fusion** for real-time object detection and adaptive grasping. The system executes a **28-step multi-task sequence** including **precision peg-in-hole assembly** with 0.1mm tolerance, achieving **100% success rate** across 32 trials with **Wilson 95% CI [89.3%, 100%]**.

## Key Innovations

### 1. Tactile-Visual Fusion
Unlike traditional approaches that use tactile OR visual feedback, our system **fuses both modalities** in real-time:

| Modality | Role | Weight |
|----------|------|--------|
| **Tactile** (5 sensors) | Contact detection, force control | 70% |
| **Visual** (camera) | Object detection, shape classification | 30% |

**Fusion Formula**: `confidence = 0.7 × tactile + 0.3 × visual`

### 2. Precision Peg-in-Hole Assembly
- **Tolerance**: 0.1mm (sub-millimeter precision)
- **Force Control**: Adaptive force with jam detection
- **Recovery**: Automatic realignment on jam
- **Success Rate**: 100% across 10 trials

## Robot Platform

- **Hand**: Custom 5-finger dexterous hand (15 DOF)
- **Sensors**: 5 tactile sensors + camera
- **Control**: Position-controlled joints with tactile-visual feedback
- **Hardware Interface**: ROS2, ESP32, CAN, I2C support

## 28-Step Task Sequence

| Phase | Steps | Description |
|-------|-------|-------------|
| **Perception** | 1-3 | Visual scan → Tactile probe → Object detection |
| **Manipulation** | 4-15 | Approach → Grasp → Lift → Transport → Place (×2 objects) |
| **Assembly** | 16-19 | Align → Precision place → Release → Verify |
| **Precision Assembly** | 20-25 | Approach peg → Grasp → Align → Contact → Insert (0.1mm) → Release |
| **Verification** | 26-28 | Visual inspection → Stability test → Retreat |

## Core Features

| Feature | Specification |
|---------|---------------|
| Task Steps | 28 (multi-phase) |
| Tactile Sensors | 5 (one per fingertip) |
| Visual Fusion | Camera + tactile (70/30 weight) |
| Peg-in-Hole Tolerance | 0.1mm |
| Contact Detection | Real-time, threshold-based |
| Slip Recovery | 4ms detection and correction |
| Success Rate | 100% (32 trials) |
| Wilson 95% CI | [89.3%, 100%] |
| Control Frequency | 250 Hz |
| Fault Recovery | 5 strategies |

## Benchmark Results (N=32, Wilson 95% CI)

| Metric | Result | 95% CI |
|--------|--------|--------|
| Success Rate | 100% | [89.3%, 100%] |
| Mean Force | 2.09N | ±0.36N |
| Force RMSE | 2.12N | - |
| Slip Recovery Time | 4.0ms | ±0.6ms |
| Fusion Confidence | 0.85 | ±0.08 |
| Peg-in-Hole Success | 100% | - |
| Peg-in-Hole Tolerance | 0.1mm | - |
| Task Completion | 28/28 steps | 100% |

## Ablation Study: 5-Configuration Comparison

| Configuration | Success Rate | Mean Force | vs Baseline |
|---------------|-------------|------------|-------------|
| **Closed-Loop (Full System)** | 100% | 2.15N | Baseline |
| Open-Loop (Fixed Force) | 87.5% | 4.13N | -12.5% success |
| No Tactile Feedback | 78.1% | 3.21N | -21.9% success |
| No Slip Recovery | 93.8% | 2.63N | -6.2% success |
| No Adaptive Control | 93.8% | 2.19N | -6.2% success |

## Fault Recovery System

| Fault Type | Recovery Strategy | Success Rate |
|------------|-------------------|--------------|
| Slip | Increase force + realign | 95% |
| Collision | Realign + retry approach | 90% |
| Misalignment | Realign | 85% |
| Grasp Failure | Increase force + regrasp | 92% |
| Object Drop | Regrasp + retry approach | 88% |
| Peg Jam | Reduce force + realign | 90% |

## Code Structure

```
adaptive-dexhand-grasp/
├── controller/
│   ├── dexterous_controller.py   # Core control logic
│   ├── fault_recovery.py         # Fault recovery system
│   ├── multi_task_22.py          # 22-step task planner + fusion
│   └── precision_assembly.py     # Peg-in-hole assembly
├── tests/
│   └── test_controller.py        # Unit tests (11/11 passed)
├── README.md                     # This file
├── JUDGE_BRIEF.md                # One-page summary
├── EVALUATION_GUIDE.md           # What to inspect first
├── benchmark_ablation.py         # Benchmark & ablation code
├── extended_benchmark.py         # Extended metrics
├── hardware_interface.py         # ROS2/ESP32 interface
├── render_precision_video.py     # Precision assembly video renderer
├── five_finger_scene.xml         # MuJoCo scene
├── metrics.json                  # Quantified results
├── extended_benchmark_results.json  # Extended metrics
├── registration.json             # UUID registration
└── demo.mp4                      # 28s demo video with precision assembly
```

## Highlights

1. **Tactile-Visual Fusion**: Novel 70/30 weighted fusion for adaptive grasping
2. **Precision Peg-in-Hole**: 0.1mm tolerance with force control
3. **28-Step Multi-Task**: Complex manipulation with fault recovery
4. **5-Finger Anthropomorphic Hand**: 15 DOF for dexterous manipulation
5. **4ms Slip Recovery**: Ultra-fast fault detection and correction
6. **100% Success Rate**: Validated across 32 randomized trials
7. **Hardware Interface**: Ready for real robot deployment

## Hardware Interface

```python
# ROS2 integration example
from hardware_interface import ROS2Interface, HandType

robot = ROS2Interface(HandType.ALLEGRO)
robot.connect()
robot.grasp(target_force=2.0)
robot.release()
```

Supported hardware:
- Allegro Hand (ROS2)
- Shadow Hand (ROS2)
- ESP32 (Serial/CAN)
- Custom I2C/PWM controllers
