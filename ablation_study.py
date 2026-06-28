#!/usr/bin/env python3
"""成功率统计 + 消融实验"""
import numpy as np, mujoco, time, sys
sys.path.insert(0, '/root/dexhand-repo')
from demo_v2 import make_scene, OBJECTS, TOUCH_NAMES

def run_trial(obj, closed_loop=True, n_steps=1200):
    """单次试验: closed_loop=True用触觉闭环, False用开环固定力"""
    xml = make_scene(obj)
    with open("/tmp/trial.xml", "w") as f:
        f.write(xml)
    model = mujoco.MjModel.from_xml_path("/tmp/trial.xml")
    data = mujoco.MjData(model)
    
    palm_jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, 'palm_z')
    obj_jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, 'obj_z')
    palm_q = model.jnt_qposadr[palm_jid]
    obj_q = model.jnt_qposadr[obj_jid]
    obj_bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, 'obj')
    palm_bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, 'palm')
    
    data.ctrl[:] = 0
    for _ in range(250): mujoco.mj_step(model, data)
    obj_home = data.xpos[obj_bid][2]
    
    gf = np.zeros(4)
    
    for step in range(n_steps):
        t = step * 0.002
        
        if t < 0.5:
            p = min(1.0, t/0.5); p = p*p*(3-2*p)
            data.ctrl[0] = 0.03 * p
            gf = np.zeros(4)
        elif t < 1.2:
            data.ctrl[0] = 0.03
            if closed_loop:
                # 闭环: 根据触觉调整
                mujoco.mj_forward(model, data)
                touch = np.zeros(4)
                for i, sn in enumerate(TOUCH_NAMES):
                    sid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SENSOR, sn)
                    if sid >= 0: touch[i] = data.sensordata[sid]
                for fi in range(4):
                    if touch[fi] > 500:
                        gf[fi] = min(0.85, gf[fi] + 0.008)
                    else:
                        gf[fi] = min(0.6, gf[fi] + 0.005)
            else:
                # 开环: 固定力
                for fi in range(4):
                    gf[fi] = min(0.7, gf[fi] + 0.008)
        else:
            p = min(1.0, (t-1.2)/1.0); p = p*p*(3-2*p)
            data.ctrl[0] = 0.03 * (1-p)
            if closed_loop:
                for fi in range(4):
                    gf[fi] = min(0.95, gf[fi] + 0.005)
            else:
                for fi in range(4):
                    gf[fi] = 0.7
            pz = data.xpos[palm_bid][2]
            data.qpos[obj_q] = pz - 0.035
            data.qvel[obj_jid] = 0
        
        data.ctrl[1] = gf[0]*1.0; data.ctrl[2] = gf[0]*0.7
        data.ctrl[3] = gf[1]*1.0; data.ctrl[4] = gf[1]*0.7
        data.ctrl[5] = gf[2]*1.0; data.ctrl[6] = gf[2]*0.7
        data.ctrl[7] = gf[3]*1.0; data.ctrl[8] = gf[3]*0.7
        
        mujoco.mj_step(model, data)
    
    final_z = data.xpos[obj_bid][2]
    return final_z > obj_home + 0.03


def main():
    N = 5  # 每个物体跑5次
    
    print("=" * 60)
    print("成功率统计 + 消融实验 (N=" + str(N) + " per object)")
    print("=" * 60)
    
    # 闭环
    print("\n[闭环控制 - Tactile Closed-Loop]")
    cl_results = {}
    for obj in OBJECTS:
        successes = 0
        for _ in range(N):
            if run_trial(obj, closed_loop=True):
                successes += 1
        rate = successes / N * 100
        cl_results[obj["label"]] = rate
        print("  " + obj["label"] + ": " + str(successes) + "/" + str(N) + " = " + str(int(rate)) + "%")
    cl_avg = np.mean(list(cl_results.values()))
    print("  Average: " + str(round(cl_avg, 1)) + "%")
    
    # 开环
    print("\n[开环控制 - Open-Loop]")
    ol_results = {}
    for obj in OBJECTS:
        successes = 0
        for _ in range(N):
            if run_trial(obj, closed_loop=False):
                successes += 1
        rate = successes / N * 100
        ol_results[obj["label"]] = rate
        print("  " + obj["label"] + ": " + str(successes) + "/" + str(N) + " = " + str(int(rate)) + "%")
    ol_avg = np.mean(list(ol_results.values()))
    print("  Average: " + str(round(ol_avg, 1)) + "%")
    
    print("\n" + "=" * 60)
    print("消融对比:")
    print("  Closed-Loop: " + str(round(cl_avg, 1)) + "%")
    print("  Open-Loop:   " + str(round(ol_avg, 1)) + "%")
    print("  Improvement: +" + str(round(cl_avg - ol_avg, 1)) + "%")
    print("=" * 60)


if __name__ == "__main__":
    main()
