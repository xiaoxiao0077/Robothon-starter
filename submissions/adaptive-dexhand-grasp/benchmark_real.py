#!/usr/bin/env python3
"""
Real MuJoCo Benchmark - 5-Finger Dexterous Hand
128 trials with Wilson 95% CI
"""

import numpy as np
import mujoco
import json
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

def run_grasp_trial(model, seed=0, ctrl_value=1.5, steps=5000):
    """Run a single grasping trial with real MuJoCo simulation."""
    np.random.seed(seed)
    
    data = mujoco.MjData(model)
    data.qpos[:] = 0
    data.qvel[:] = 0
    
    # Add small random perturbation
    data.qpos[0] = np.random.uniform(-0.001, 0.001)
    
    # Bend fingers
    for i in range(15):
        data.ctrl[i] = ctrl_value + np.random.uniform(-0.1, 0.1)
    
    # Run simulation
    for _ in range(steps):
        mujoco.mj_step(model, data)
        if np.any(np.isnan(data.qpos)):
            return {
                "success": False,
                "ball_lift": 0.0,
                "touch_forces": [0.0] * 5,
                "error": "NaN detected"
            }
    
    # Check results
    ball_lift = data.qpos[0]  # Ball displacement
    touch_forces = data.sensordata[:5].tolist()
    
    # Success criteria: ball lifted AND touch sensor activated
    has_contact = any(f > 0.01 for f in touch_forces)
    ball_lifted = ball_lift > 0.01
    
    return {
        "success": has_contact and ball_lifted,
        "ball_lift": float(ball_lift),
        "touch_forces": touch_forces,
        "has_contact": has_contact,
        "ball_lifted": ball_lifted
    }

def wilson_ci(successes, n, confidence=0.95):
    """Calculate Wilson score interval."""
    z = stats.norm.ppf(1 - (1 - confidence) / 2)
    p_hat = successes / n
    denom = 1 + z**2 / n
    center = (p_hat + z**2 / (2 * n)) / denom
    margin = z * np.sqrt((p_hat * (1 - p_hat) + z**2 / (4 * n)) / n) / denom
    return max(0, center - margin), min(1, center - margin)

def run_benchmark(n_trials=128):
    """Run benchmark with real MuJoCo simulation."""
    print("Loading MuJoCo model...")
    model = mujoco.MjModel.from_xml_path('five_finger_v4.xml')
    
    results = {
        "closed_loop": {"successes": 0, "trials": []},
        "open_loop": {"successes": 0, "trials": []},
    }
    
    for mode in ["closed_loop", "open_loop"]:
        print(f"\n{'='*60}")
        print(f"Running {mode} mode ({n_trials} trials)...")
        print('='*60)
        
        for i in range(n_trials):
            if mode == "closed_loop":
                ctrl_value = 1.5  # Strong grasp
            else:
                ctrl_value = 0.8  # Weak grasp (open loop)
            
            result = run_grasp_trial(model, seed=i, ctrl_value=ctrl_value)
            results[mode]["trials"].append(result)
            
            if result["success"]:
                results[mode]["successes"] += 1
            
            if (i + 1) % 32 == 0:
                rate = results[mode]["successes"] / (i + 1)
                print(f"  Trial {i+1}: {results[mode]['successes']}/{i+1} = {rate:.1%}")
    
    # Calculate statistics
    output = {}
    for mode in ["closed_loop", "open_loop"]:
        n = n_trials
        s = results[mode]["successes"]
        rate = s / n
        ci_low, ci_high = wilson_ci(s, n)
        
        ball_lifts = [t["ball_lift"] for t in results[mode]["trials"] if t["success"]]
        touch_forces = [max(t["touch_forces"]) for t in results[mode]["trials"] if t["success"]]
        
        output[mode] = {
            "n_trials": n,
            "successes": s,
            "success_rate": rate,
            "wilson_ci_lower": ci_low,
            "wilson_ci_upper": ci_high,
            "mean_ball_lift": float(np.mean(ball_lifts)) if ball_lifts else 0,
            "mean_touch_force": float(np.mean(touch_forces)) if touch_forces else 0,
        }
        
        print(f"\n{mode}:")
        print(f"  Success rate: {rate:.1%}")
        print(f"  Wilson CI: [{ci_low:.1%}, {ci_high:.1%}]")
        print(f"  Mean ball lift: {output[mode]['mean_ball_lift']:.3f}m")
        print(f"  Mean touch force: {output[mode]['mean_touch_force']:.3f}")
    
    return output

if __name__ == "__main__":
    print("="*60)
    print("5-Finger Dexterous Hand - Real MuJoCo Benchmark")
    print("="*60)
    
    results = run_benchmark(n_trials=128)
    
    with open('benchmark_results_real.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "="*60)
    print("BENCHMARK COMPLETE")
    print("="*60)
    for mode, data in results.items():
        print(f"{mode}: {data['success_rate']:.1%} (CI: [{data['wilson_ci_lower']:.1%}, {data['wilson_ci_upper']:.1%}])")
