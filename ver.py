"""
Ver al humano simulado.

    python3 ver.py                           # visor 3D interactivo (en macOS: mjpython ver.py)
    python3 ver.py --escenario falla         # nominal | sin-exo | falla | sentarse
    python3 ver.py --gif levantarse.gif      # graba un GIF sin abrir ventana

En el visor: arrastra con el ratón para girar la cámara, rueda para acercar, espacio para pausar.
El motor azul en la rodilla es el exo.
"""
import argparse, time
import numpy as np
import mujoco
import exo_sim as X

ESCENARIOS = {
    "nominal":  ("Con exo, 85% de fuerza: se levanta",
                 lambda: X.Config(diseno=X.DISENOS["BLDC cuasi directo 9:1"])),
    "sin-exo":  ("Sin exo, 85% de fuerza: no se levanta",
                 lambda: X.Config()),
    "falla":    ("DC 170:1, el exo falla a 1,3 s: cae a la silla",
                 lambda: X.Config(diseno=X.DISENOS["DC 12 V + 170:1"], t_falla=1.3)),
    "sentarse": ("Sentarse con 60% de fuerza, sin exo",
                 lambda: X.Config(tarea="sentarse", capacidad=0.6, T=4)),
}

def trayectoria(nombre):
    cfg = ESCENARIOS[nombre][1]()
    o = X.simular(cfg)
    q = np.radians(np.c_[o["tobillo"], o["rodilla"], o["cadera"]])
    t = o["t"]
    if cfg.tarea == "levantarse":
        # tras volver a caer a la silla el modelo ya no es realista (la persona simulada
        # sigue intentando la trayectoria de pie), así que se corta 0,4 s después del impacto
        cae = np.where((t > 1.2) & (o["f_asiento"] > 50))[0]
        if len(cae):
            fin = min(len(t), cae[0] + int(0.4 / (t[1] - t[0])))
            t, q = t[:fin], q[:fin]
    return t, q

def gif(nombre, ruta, fps=25, ancho=480, alto=360):
    from PIL import Image
    m = mujoco.MjModel.from_xml_string(X._xml())
    d = mujoco.MjData(m)
    r = mujoco.Renderer(m, alto, ancho)
    t, q = trayectoria(nombre)
    paso = int(round(1 / fps / (t[1] - t[0])))
    frames = []
    for i in range(0, len(t), paso):
        d.qpos[:] = q[i]
        mujoco.mj_forward(m, d)
        r.update_scene(d, camera="lateral")
        frames.append(Image.fromarray(r.render()))
    frames[0].save(ruta, save_all=True, append_images=frames[1:], duration=int(1000 / fps), loop=0)
    print("GIF guardado en", ruta)

def visor(nombre):
    import mujoco.viewer
    m = mujoco.MjModel.from_xml_string(X._xml())
    d = mujoco.MjData(m)
    t, q = trayectoria(nombre)
    print(ESCENARIOS[nombre][0], "(se repite en bucle; cierra la ventana para salir)")
    with mujoco.viewer.launch_passive(m, d) as v:
        v.cam.type = mujoco.mjtCamera.mjCAMERA_FIXED
        v.cam.fixedcamid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_CAMERA, "lateral")
        while v.is_running():
            inicio = time.time()
            for i in range(0, len(t), 10):
                if not v.is_running():
                    break
                d.qpos[:] = q[i]
                mujoco.mj_forward(m, d)
                v.sync()
                espera = t[i] - (time.time() - inicio)
                if espera > 0:
                    time.sleep(espera)
            time.sleep(1.0)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--escenario", choices=ESCENARIOS, default="nominal")
    p.add_argument("--gif")
    a = p.parse_args()
    gif(a.escenario, a.gif) if a.gif else visor(a.escenario)
