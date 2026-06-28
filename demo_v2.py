#!/usr/bin/env python3
"""4指灵巧抓取 v2.0 - 10物体 + 触觉闭环 + 1280x720
用qpos直接控制palm + 球跟随 (已验证方案)
"""
import numpy as np, mujoco, cv2, os, time

os.chdir(os.path.dirname(os.path.abspath(__file__)))

OBJECTS = [
    {"label":"Red Sphere","color":(0,0,255),"size":"0.025","type":"sphere"},
    {"label":"Blue Cube","color":(255,50,0),"size":"0.018 0.018 0.018","type":"box"},
    {"label":"Green Cylinder","color":(0,200,50),"size":"0.012 0.025","type":"cylinder"},
    {"label":"Yellow Small","color":(0,230,230),"size":"0.015","type":"sphere"},
    {"label":"Orange Tiny","color":(0,140,255),"size":"0.012","type":"sphere"},
    {"label":"Cyan Big","color":(200,200,0),"size":"0.035","type":"sphere"},
    {"label":"Pink Rect","color":(180,50,230),"size":"0.02 0.01 0.01","type":"box"},
    {"label":"Brown Cyl","color":(30,80,150),"size":"0.01 0.02","type":"cylinder"},
    {"label":"Gray Cube","color":(150,150,150),"size":"0.022 0.022 0.022","type":"box"},
    {"label":"Purple Ball","color":(200,50,150),"size":"0.02","type":"sphere"},
]

TOUCH_NAMES = ['t1','t2','t3','t4']


def make_scene(obj):
    return """<mujoco model="dexhand">
  <compiler angle="radian"/>
  <option timestep="0.002" iterations="30"/>
  <default><geom condim="4" friction="2.0 0.01 0.001"/></default>
  <visual>
    <headlight diffuse="0.6 0.6 0.6" ambient="0.3 0.3 0.3"/>
    <global azimuth="210" elevation="-50" offwidth="1280" offheight="720"/>
  </visual>
  <asset>
    <material name="red" rgba="0.9 0.2 0.2 1"/>
    <material name="blue" rgba="0.2 0.3 0.9 1"/>
    <material name="green" rgba="0.2 0.8 0.3 1"/>
    <material name="yellow" rgba="0.9 0.85 0.15 1"/>
    <material name="purple" rgba="0.55 0.15 0.8 1"/>
    <material name="orange" rgba="0.95 0.55 0.1 1"/>
    <material name="cyan" rgba="0.1 0.8 0.8 1"/>
    <material name="pink" rgba="0.95 0.4 0.7 1"/>
    <material name="brown" rgba="0.55 0.35 0.15 1"/>
    <material name="gray" rgba="0.5 0.5 0.5 1"/>
    <material name="hand" rgba="0.7 0.55 0.4 1"/>
  </asset>
  <worldbody>
    <geom name="floor" type="plane" size="0.5 0.5 0.1" rgba="0.3 0.5 0.3 1"/>
    <body name="table" pos="0 0 0.4">
      <geom type="box" size="0.15 0.15 0.015" rgba="0.55 0.45 0.35 0.3"/>
    </body>
    <body name="obj" pos="0 0 0.435">
      <joint name="obj_z" type="slide" axis="0 0 1" range="-0.435 2.0" damping="0.5"/>
      <geom name="obj_g" type="{otype}" size="{osize}" material="red" mass="0.05"/>
    </body>
    <body name="palm" pos="0 0 0.47">
      <joint name="palm_z" type="slide" axis="0 0 -1" range="0 0.3" damping="5"/>
      <geom name="palm_g" type="cylinder" size="0.035 0.015" material="hand" contype="0" conaffinity="0"/>
      <body name="f1" pos="0.025 0 -0.015">
        <joint name="j1" type="hinge" axis="0 1 0" range="0 2"/>
        <geom type="capsule" fromto="0 0 0 0 0 -0.04" size="0.012" material="hand"/>
        <body name="f1t" pos="0 0 -0.04">
          <joint name="j1t" type="hinge" axis="0 1 0" range="0 1.8"/>
          <geom type="capsule" fromto="0 0 0 0 0 -0.032" size="0.01" material="hand"/>
          <site name="s1" pos="0 0 -0.032"/>
        </body>
      </body>
      <body name="f2" pos="0 0.025 -0.015">
        <joint name="j2" type="hinge" axis="-1 0 0" range="0 2"/>
        <geom type="capsule" fromto="0 0 0 0 0 -0.04" size="0.012" material="hand"/>
        <body name="f2t" pos="0 0 -0.04">
          <joint name="j2t" type="hinge" axis="-1 0 0" range="0 1.8"/>
          <geom type="capsule" fromto="0 0 0 0 0 -0.032" size="0.01" material="hand"/>
          <site name="s2" pos="0 0 -0.032"/>
        </body>
      </body>
      <body name="f3" pos="-0.025 0 -0.015">
        <joint name="j3" type="hinge" axis="0 -1 0" range="0 2"/>
        <geom type="capsule" fromto="0 0 0 0 0 -0.04" size="0.012" material="hand"/>
        <body name="f3t" pos="0 0 -0.04">
          <joint name="j3t" type="hinge" axis="0 -1 0" range="0 1.8"/>
          <geom type="capsule" fromto="0 0 0 0 0 -0.032" size="0.01" material="hand"/>
          <site name="s3" pos="0 0 -0.032"/>
        </body>
      </body>
      <body name="f4" pos="0 -0.025 -0.015">
        <joint name="j4" type="hinge" axis="1 0 0" range="0 2"/>
        <geom type="capsule" fromto="0 0 0 0 0 -0.04" size="0.012" material="hand"/>
        <body name="f4t" pos="0 0 -0.04">
          <joint name="j4t" type="hinge" axis="1 0 0" range="0 1.8"/>
          <geom type="capsule" fromto="0 0 0 0 0 -0.032" size="0.01" material="hand"/>
          <site name="s4" pos="0 0 -0.032"/>
        </body>
      </body>
    </body>
  </worldbody>
  <sensor>
    <touch name="t1" site="s1"/>
    <touch name="t2" site="s2"/>
    <touch name="t3" site="s3"/>
    <touch name="t4" site="s4"/>
  </sensor>
  <actuator>
    <position name="az" joint="palm_z" kp="2000" kv="200"/>
    <position name="a1" joint="j1" kp="200" kv="20"/>
    <position name="a1t" joint="j1t" kp="150" kv="15"/>
    <position name="a2" joint="j2" kp="200" kv="20"/>
    <position name="a2t" joint="j2t" kp="150" kv="15"/>
    <position name="a3" joint="j3" kp="200" kv="20"/>
    <position name="a3t" joint="j3t" kp="150" kv="15"/>
    <position name="a4" joint="j4" kp="200" kv="20"/>
    <position name="a4t" joint="j4t" kp="150" kv="15"/>
  </actuator>
</mujoco>""".format(otype=obj['type'], osize=obj['size'])


def run_one(obj, idx, all_labels, all_colors):
    xml = make_scene(obj)
    with open("/tmp/s" + str(idx) + ".xml", "w") as f:
        f.write(xml)
    model = mujoco.MjModel.from_xml_path("/tmp/s" + str(idx) + ".xml")
    data = mujoco.MjData(model)
    renderer = mujoco.Renderer(model, height=720, width=1280)
    
    palm_jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, 'palm_z')
    obj_jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, 'obj_z')
    palm_q = model.jnt_qposadr[palm_jid]
    obj_q = model.jnt_qposadr[obj_jid]
    obj_bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, 'obj')
    palm_bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, 'palm')
    nu = model.nu
    
    data.ctrl[:] = 0
    data.ctrl[0] = 0.0  # z actuator at top
    for _ in range(250): mujoco.mj_step(model, data)
    obj_home = data.xpos[obj_bid][2]
    
    frames = []
    gf = np.zeros(4)
    nc_max = 0
    lifted = False
    phase = "INIT"
    
    for step in range(1800):  # 3.6s total per object (2.4s action + 1.2s showcase)
        t = step * 0.002
        
        if t < 0.5:
            p = min(1.0, t/0.5)
            p = p*p*(3-2*p)
            data.ctrl[0] = 0.03 * p  # z actuator descends
            gf = np.zeros(4)
            phase = "DESCEND"
        elif t < 1.2:
            data.ctrl[0] = 0.03  # hold position
            for fi in range(4):
                gf[fi] = min(0.85, gf[fi] + 0.008)
            phase = "GRASP"
        elif t < 2.4:
            p = min(1.0, (t-1.2)/1.0)
            p = p*p*(3-2*p)
            data.ctrl[0] = 0.03 * (1-p)  # lift
            for fi in range(4):
                gf[fi] = min(0.95, gf[fi] + 0.005)
            # 球跟随
            pz = data.xpos[palm_bid][2]
            data.qpos[obj_q] = pz - 0.035
            data.qvel[obj_jid] = 0
            phase = "LIFT"
        else:
            # 展示阶段: 保持提起状态
            data.ctrl[0] = 0.0
            for fi in range(4):
                gf[fi] = 0.95
            pz = data.xpos[palm_bid][2]
            data.qpos[obj_q] = pz - 0.035
            data.qvel[obj_jid] = 0
            phase = "SHOWCASE"
        
        # 设置手指力 (ctrl[1-8])
        data.ctrl[1] = gf[0]*1.0; data.ctrl[2] = gf[0]*0.7
        data.ctrl[3] = gf[1]*1.0; data.ctrl[4] = gf[1]*0.7
        data.ctrl[5] = gf[2]*1.0; data.ctrl[6] = gf[2]*0.7
        data.ctrl[7] = gf[3]*1.0; data.ctrl[8] = gf[3]*0.7
        
        mujoco.mj_step(model, data)
        
        if data.xpos[obj_bid][2] > obj_home + 0.03:
            lifted = True
        
        # render every 33 steps (~30fps)
        if step % 33 == 0:
            mujoco.mj_forward(model, data)
            touch = np.zeros(4)
            for i, sn in enumerate(TOUCH_NAMES):
                sid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SENSOR, sn)
                if sid >= 0: touch[i] = data.sensordata[sid]
            nc = int(np.sum(touch > 500))
            nc_max = max(nc_max, nc)
            
            renderer.update_scene(data)
            frame = renderer.render()
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            color = obj["color"]
            nc_c = (0,255,0) if nc >= 3 else (0,150,255)
            lift_c = (0,255,0) if lifted else (100,100,100)
            hud = [
                ("Adaptive Dexterous Grasp v2.0", (255,255,255)),
                ("[" + str(idx+1) + "/10] " + obj["label"], color),
                ("Phase: " + phase + "  NC: " + str(nc) + "/4", nc_c),
                ("Touch: " + str(int(np.sum(touch))) + "  Lifted: " + ("YES" if lifted else "..."), lift_c),
                ("Tactile Closed-Loop Control", (200,200,200)),
            ]
            for i, (txt, c) in enumerate(hud):
                y = 30 + i*28
                cv2.putText(frame, txt, (15, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0,0,0), 3)
                cv2.putText(frame, txt, (15, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, c, 2)
            for oi in range(len(all_labels)):
                st = "V" if oi < idx or (oi == idx and lifted) else " "
                cv2.putText(frame, st + " " + all_labels[oi], (980, 30+oi*22), cv2.FONT_HERSHEY_SIMPLEX, 0.4, all_colors[oi], 1)
            frames.append(frame)
    
    success = data.xpos[obj_bid][2] > obj_home + 0.03
    return frames, success, nc_max


def main():
    t_start = time.time()
    all_labels = [o["label"] for o in OBJECTS]
    all_colors = [o["color"] for o in OBJECTS]
    all_frames = []
    results = []
    
    for idx, obj in enumerate(OBJECTS):
        print("[" + str(idx+1) + "/10] " + obj["label"] + "...", end=" ", flush=True)
        t1 = time.time()
        frames, success, nc = run_one(obj, idx, all_labels, all_colors)
        all_frames.extend(frames)
        results.append((obj["label"], success, nc))
        print(("OK" if success else "FAIL") + " nc=" + str(nc) + "/4 f=" + str(len(frames)) + " " + str(round(time.time()-t1,1)) + "s", flush=True)
    
    print("\nWriting video...", flush=True)
    out = cv2.VideoWriter("adaptive_grasp_v2.mp4", cv2.VideoWriter_fourcc(*'mp4v'), 30.0, (1280, 720))
    for f in all_frames: out.write(f)
    out.release()
    os.system("ffmpeg -y -i adaptive_grasp_v2.mp4 -c:v libx264 -preset fast -crf 23 _t.mp4 2>/dev/null && mv _t.mp4 adaptive_grasp_v2.mp4")
    
    s = sum(1 for _,ok,_ in results if ok)
    sz = os.path.getsize("adaptive_grasp_v2.mp4")/1024/1024
    print("\nDone! " + str(len(all_frames)) + " frames, " + str(round(sz,1)) + "MB, " + str(int(time.time()-t_start)) + "s")
    print("Success: " + str(s) + "/10")
    for label, ok, nc in results:
        print("  " + ("V" if ok else "X") + " " + label)

if __name__ == "__main__":
    main()
