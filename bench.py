#!/usr/bin/env python3
import numpy as np, mujoco, time, sys
sys.path.insert(0, '/root/dexhand-repo')
from demo_v2 import make_scene, get_touch, set_fingers, OBJECTS

obj = OBJECTS[0]
xml = make_scene(obj)
with open('/tmp/t.xml', 'w') as f: f.write(xml)
model = mujoco.MjModel.from_xml_path('/tmp/t.xml')
data = mujoco.MjData(model)

palm_jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, 'palm_z')
obj_jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, 'obj_z')
palm_q = model.jnt_qposadr[palm_jid]
obj_q = model.jnt_qposadr[obj_jid]
obj_bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, 'obj')
palm_bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, 'palm')

data.ctrl[:] = 0
data.qpos[palm_q] = 0.0
for _ in range(500): mujoco.mj_step(model, data)
obj_home = data.xpos[obj_bid][2]

grasp_f = np.zeros(5)
nc_max = 0
lifted = False
t0 = data.time
step_count = 0
t_start = time.time()
touch_check_interval = 10  # read sensors every 10 steps
last_touch = np.zeros(5)

while data.time - t0 < 3.5:
    t = data.time - t0
    if t < 0.8:
        p = min(1.0, t / 0.8)
        p = p*p*(3-2*p)
        palm_target = 0.03 * p
        grasp_f = np.zeros(5)
    elif t < 2.0:
        palm_target = 0.03
        for fi in range(5):
            grasp_f[fi] = min(0.9, grasp_f[fi] + 0.006)
    else:
        p = min(1.0, (t - 2.0) / 1.0)
        p = p*p*(3-2*p)
        palm_target = 0.03 * (1 - p)
        for fi in range(5):
            grasp_f[fi] = min(1.0, grasp_f[fi] + 0.003)
    
    data.qpos[palm_q] = palm_target
    set_fingers(data, grasp_f)
    
    mujoco.mj_step(model, data)
    
    # read sensors periodically
    if step_count % touch_check_interval == 0:
        touch = get_touch(model, data)
        nc = int(np.sum(touch > 500))
        nc_max = max(nc_max, nc)
        last_touch = touch
        
        if t >= 2.0 and nc >= 2:
            pz = data.xpos[palm_bid][2]
            oz = data.xpos[obj_bid][2]
            if oz < pz - 0.03:
                data.qpos[obj_q] = pz - 0.035
                data.qvel[obj_jid] = 0
    
    if data.xpos[obj_bid][2] > obj_home + 0.03:
        lifted = True
    
    step_count += 1

elapsed = time.time() - t_start
print(str(step_count) + " steps in " + str(round(elapsed, 2)) + "s (" + str(int(step_count/elapsed)) + " steps/s)")
print("nc_max=" + str(nc_max) + " lifted=" + str(lifted) + " obj_z=" + str(round(data.xpos[obj_bid][2], 4)))
print("touch=" + str([round(t, 0) for t in last_touch]))
