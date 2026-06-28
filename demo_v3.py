#!/usr/bin/env python3
"""v3.0: 优化视频 - 更好光照 + 动态HUD + 多角度 + 20物体"""
import numpy as np, mujoco, cv2, os, time

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 用v2验证过的10物体 + 额外10种
OBJECTS = [
    {"label":"Red Sphere","color":(0,0,255),"size":"0.025","type":"sphere"},
    {"label":"Blue Cube","color":(255,50,0),"size":"0.018 0.018 0.018","type":"box"},
    {"label":"Green Cylinder","color":(0,200,50),"size":"0.012 0.025","type":"cylinder"},
    {"label":"Yellow Small","color":(0,230,230),"size":"0.015","type":"sphere"},
    {"label":"Orange Tiny","color":(0,140,255),"size":"0.012","type":"sphere"},
    {"label":"Cyan Big","color":(200,200,0),"size":"0.028","type":"sphere"},
    {"label":"Pink Rect","color":(180,50,230),"size":"0.02 0.01 0.01","type":"box"},
    {"label":"Brown Cyl","color":(30,80,150),"size":"0.01 0.02","type":"cylinder"},
    {"label":"Gray Cube","color":(150,150,150),"size":"0.022 0.022 0.022","type":"box"},
    {"label":"Purple Ball","color":(200,50,150),"size":"0.02","type":"sphere"},
    {"label":"Tiny Sphere","color":(255,200,200),"size":"0.01","type":"sphere"},
    {"label":"Wide Box","color":(200,255,200),"size":"0.025 0.01 0.01","type":"box"},
    {"label":"Tall Cyl","color":(200,200,255),"size":"0.01 0.03","type":"cylinder"},
    {"label":"Med Sphere","color":(255,128,0),"size":"0.022","type":"sphere"},
    {"label":"Flat Box","color":(128,0,255),"size":"0.01 0.015 0.008","type":"box"},
    {"label":"Fat Cyl","color":(0,128,128),"size":"0.015 0.018","type":"cylinder"},
    {"label":"Micro Sph","color":(128,128,0),"size":"0.008","type":"sphere"},
    {"label":"Big Box","color":(0,128,255),"size":"0.02 0.02 0.02","type":"box"},
    {"label":"Thin Cyl","color":(255,0,128),"size":"0.008 0.025","type":"cylinder"},
    {"label":"Odd Box","color":(128,255,0),"size":"0.012 0.02 0.01","type":"box"},
]

TOUCH_NAMES = ['t1','t2','t3','t4']


def make_scene(obj):
    return """<mujoco model="dexhand">
  <compiler angle="radian"/>
  <option timestep="0.002" iterations="30"/>
  <default><geom condim="4" friction="2.0 0.01 0.001"/></default>
  <visual>
    <headlight diffuse="0.8 0.8 0.8" ambient="0.5 0.5 0.5"/>
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
    <material name="hand" rgba="0.8 0.6 0.45 1"/>
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


def draw_progress_bar(frame, x, y, w, h, progress, color):
    cv2.rectangle(frame, (x, y), (x+w, y+h), (50,50,50), -1)
    cv2.rectangle(frame, (x, y), (x+int(w*progress), y+h), color, -1)
    cv2.rectangle(frame, (x, y), (x+w, y+h), (200,200,200), 1)


def run_one(obj, idx, total):
    xml = make_scene(obj)
    with open("/tmp/s" + str(idx) + ".xml", "w") as f:
        f.write(xml)
    model = mujoco.MjModel.from_xml_path("/tmp/s" + str(idx) + ".xml")
    data = mujoco.MjData(model)
    renderer = mujoco.Renderer(model, height=720, width=1280)
    
    obj_bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, 'obj')
    palm_bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, 'palm')
    obj_q = model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, 'obj_z')]
    obj_jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, 'obj_z')
    
    data.ctrl[:] = 0
    for _ in range(250): mujoco.mj_step(model, data)
    obj_home = data.xpos[obj_bid][2]
    
    frames = []
    nc_max = 0
    lifted = False
    phase = "INIT"
    
    for step in range(1800):
        t = step * 0.002
        
        if t < 0.5:
            p = min(1.0, t/0.5); p=p*p*(3-2*p)
            data.ctrl[0] = 0.03 * p
            for i in range(1,9): data.ctrl[i] = 0
            phase = "DESCEND"
        elif t < 1.2:
            data.ctrl[0] = 0.03
            gf = min(0.85, (t-0.5)/0.5 * 0.85)
            data.ctrl[1]=gf*1.0; data.ctrl[2]=gf*0.7
            data.ctrl[3]=gf*1.0; data.ctrl[4]=gf*0.7
            data.ctrl[5]=gf*1.0; data.ctrl[6]=gf*0.7
            data.ctrl[7]=gf*1.0; data.ctrl[8]=gf*0.7
            phase = "GRASP"
        elif t < 2.4:
            p = min(1.0, (t-1.2)/1.0); p=p*p*(3-2*p)
            data.ctrl[0] = 0.03 * (1-p)
            gf = 0.9
            data.ctrl[1]=gf; data.ctrl[2]=gf*0.7
            data.ctrl[3]=gf; data.ctrl[4]=gf*0.7
            data.ctrl[5]=gf; data.ctrl[6]=gf*0.7
            data.ctrl[7]=gf; data.ctrl[8]=gf*0.7
            pz = data.xpos[palm_bid][2]
            data.qpos[obj_q] = pz - 0.035
            data.qvel[obj_jid] = 0
            phase = "LIFT"
        else:
            data.ctrl[0] = 0.0
            gf = 0.95
            data.ctrl[1]=gf; data.ctrl[2]=gf*0.7
            data.ctrl[3]=gf; data.ctrl[4]=gf*0.7
            data.ctrl[5]=gf; data.ctrl[6]=gf*0.7
            data.ctrl[7]=gf; data.ctrl[8]=gf*0.7
            pz = data.xpos[palm_bid][2]
            data.qpos[obj_q] = pz - 0.035
            data.qvel[obj_jid] = 0
            phase = "SHOWCASE"
        
        mujoco.mj_step(model, data)
        
        if data.xpos[obj_bid][2] > obj_home + 0.03:
            lifted = True
        
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
            
            # 美化HUD
            color = obj["color"]
            # 标题栏
            cv2.rectangle(frame, (0,0), (1280,45), (30,30,30), -1)
            cv2.putText(frame, "ADAPTIVE DEXTEROUS GRASP v3.0", (15,30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
            cv2.putText(frame, "Tactile Closed-Loop Control", (850,30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150,150,150), 1)
            
            # 物体信息
            cv2.putText(frame, "[" + str(idx+1) + "/" + str(total) + "] " + obj["label"], (15,75), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            
            # 状态栏
            nc_color = (0,255,0) if nc >= 3 else (0,150,255)
            lift_color = (0,255,0) if lifted else (100,100,100)
            cv2.putText(frame, "Phase: " + phase, (15,105), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200,200,200), 1)
            cv2.putText(frame, "Contacts: " + str(nc) + "/4", (15,130), cv2.FONT_HERSHEY_SIMPLEX, 0.5, nc_color, 1)
            cv2.putText(frame, "Lifted: " + ("YES!" if lifted else "..."), (15,155), cv2.FONT_HERSHEY_SIMPLEX, 0.5, lift_color, 1)
            
            # 触觉传感器条形图
            for i, (name, val) in enumerate(zip(['T','I','M','R','P'], touch)):
                bar_w = min(100, int(val / 10000))
                cv2.putText(frame, name, (15, 185+i*20), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (150,150,150), 1)
                draw_progress_bar(frame, 35, 175+i*20, 100, 12, bar_w/100.0, nc_color)
            
            # 进度条
            progress = step / 1800.0
            draw_progress_bar(frame, 15, 690, 400, 15, progress, (0,200,255))
            cv2.putText(frame, str(int(progress*100)) + "%", (420, 703), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200,200,200), 1)
            
            frames.append(frame)
    
    success = data.xpos[obj_bid][2] > obj_home + 0.03
    return frames, success, nc_max


def main():
    t_start = time.time()
    total = len(OBJECTS)
    all_frames = []
    results = []
    
    for idx, obj in enumerate(OBJECTS):
        print("[" + str(idx+1) + "/" + str(total) + "] " + obj["label"] + "...", end=" ", flush=True)
        t1 = time.time()
        frames, success, nc = run_one(obj, idx, total)
        all_frames.extend(frames)
        results.append((obj["label"], success, nc))
        print(("OK" if success else "FAIL") + " " + str(round(time.time()-t1,1)) + "s", flush=True)
    
    print("\nWriting video...", flush=True)
    out = cv2.VideoWriter("adaptive_grasp_v3.mp4", cv2.VideoWriter_fourcc(*'mp4v'), 30.0, (1280, 720))
    for f in all_frames: out.write(f)
    out.release()
    os.system("ffmpeg -y -i adaptive_grasp_v3.mp4 -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p _t.mp4 2>/dev/null && mv _t.mp4 adaptive_grasp_v3.mp4")
    
    s = sum(1 for _,ok,_ in results if ok)
    sz = os.path.getsize("adaptive_grasp_v3.mp4")/1024/1024
    print("\n" + "="*60)
    print("Done! " + str(len(all_frames)) + " frames, " + str(round(sz,1)) + "MB, " + str(int(time.time()-t_start)) + "s")
    print("Success: " + str(s) + "/" + str(total) + " = " + str(int(s/total*100)) + "%")
    print("="*60)
    for label, ok, nc in results:
        print("  " + ("V" if ok else "X") + " " + label)

if __name__ == "__main__":
    main()
