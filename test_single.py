#!/usr/bin/env python3
"""快速测试单个物体"""
import numpy as np, mujoco, cv2, time, sys
sys.path.insert(0, '/root/dexhand-repo')
from demo_v2 import make_scene, get_touch, set_fingers, OBJECTS

obj = OBJECTS[0]
xml = make_scene(obj)
with open('/tmp/test_scene.xml', 'w') as f:
    f.write(xml)

model = mujoco.MjModel.from_xml_path('/tmp/test_scene.xml')
data = mujoco.MjData(model)
renderer = mujoco.Renderer(model, height=720, width=1280)

palm_jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, 'palm_z')
obj_jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, 'obj_z')
palm_q = model.jnt_qposadr[palm_jid]
obj_q = model.jnt_qposadr[obj_jid]
obj_bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, 'obj')
palm_bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, 'palm')

# 初始化
data.ctrl[:] = 0
data.qpos[palm_q] = 0.0
for _ in range(500): mujoco.mj_step(model, data)
obj_home = data.xpos[obj_bid][2]
print(f'home: obj_z={obj_home:.4f}')

# 下降
for step in range(400):
    p = min(1.0, step / 300.0)
    p = p * p * (3 - 2 * p)
    data.qpos[palm_q] = 0.03 * p
    set_fingers(data, np.zeros(5))
    mujoco.mj_step(model, data)
print(f'descend: palm_z={data.xpos[palm_bid][2]:.4f}')

# 抓取
for step in range(600):
    data.qpos[palm_q] = 0.03
    gf = np.minimum(0.9, np.ones(5) * step / 400.0)
    set_fingers(data, gf)
    mujoco.mj_step(model, data)
touch = get_touch(model, data)
nc = int(np.sum(touch > 500))
print(f'grasp: nc={nc}/5 touch={[round(t,0) for t in touch]}')

# 提起
for step in range(800):
    p = min(1.0, step / 600.0)
    p = p * p * (3 - 2 * p)
    data.qpos[palm_q] = 0.03 * (1 - p)
    set_fingers(data, np.ones(5) * 0.95)
    pz = data.xpos[palm_bid][2]
    data.qpos[obj_q] = pz - 0.035
    data.qvel[obj_jid] = 0
    mujoco.mj_step(model, data)

final_z = data.xpos[obj_bid][2]
print(f'lift: obj_z={final_z:.4f} LIFTED={final_z > obj_home + 0.03}')

renderer.update_scene(data)
frame = renderer.render()
cv2.imwrite('/tmp/test_result.jpg', cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
print('saved /tmp/test_result.jpg')
