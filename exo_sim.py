"""
Prototipo virtual del exoasistente de rodilla (MuJoCo, modelo sagital plano).

Persona: 3 segmentos (pierna, muslo, tronco+cabeza+brazos) con los dos lados
sumados en una sola cadena. Pie fijo al suelo. Antropometría de Winter para
75 kg / 1,70 m. La persona controla sus articulaciones con par anticipado
(dinámica inversa de la trayectoria de referencia) + realimentación con
retardo neuromuscular, y su par de extensión de rodilla está limitado a una
fracción de lo que necesita (el déficit que el exo debe cubrir).

Exo: un actuador en la rodilla. Cada diseño de transmisión define la inercia
reflejada (Jm·N²), la fricción de la reductora vista desde la salida, el
amortiguamiento con bobinado en cortocircuito (kt²·N²/R) y el límite de par
por corriente y por tensión de batería.

Convenciones de ángulos (grados en la API, radianes internamente):
  tobillo  + = pierna inclinada hacia adelante
  rodilla  + = flexión (0 = extendida, tope mecánico en 0)
  cadera   + = flexión (tronco hacia adelante respecto al muslo)
"""
from dataclasses import dataclass, field
import numpy as np
import mujoco

# ------------------------------------------------------------------ persona
MASA, ALTURA = 75.0, 1.70
L_PIERNA, L_MUSLO = 0.246 * ALTURA, 0.245 * ALTURA
H_TOBILLO = 0.039 * ALTURA
M_PIERNA, M_MUSLO, M_HAT = 2 * 0.0465 * MASA, 2 * 0.100 * MASA, 0.678 * MASA
COM_HAT = 0.19 * ALTURA            # centro de masa del tronco sobre la cadera
RG_HAT = 0.155 * ALTURA            # radio de giro del tronco

def _xml(asiento=True):
    cp = 0.567 * L_PIERNA          # CoM de la pierna medido desde el tobillo
    cm = 0.567 * L_MUSLO           # CoM del muslo medido desde la rodilla
    Ip = M_PIERNA * (0.302 * L_PIERNA) ** 2
    Im = M_MUSLO * (0.323 * L_MUSLO) ** 2
    Ih = M_HAT * RG_HAT ** 2
    seat = ""
    if asiento:
        sx, sz = _pos_asiento()
        seat = f"""
    <geom name="asiento" type="box" pos="{sx} 0 {sz}" size="0.25 0.2 0.01"
          rgba=".55 .4 .28 1" contype="2" conaffinity="2"/>
    <geom name="respaldo" type="box" pos="{sx - 0.24} 0 {sz + 0.25}" size="0.01 0.2 0.25" rgba=".55 .4 .28 1"/>
    <geom type="box" pos="{sx + 0.22} 0.17 {sz / 2}" size="0.015 0.015 {sz / 2}" rgba=".35 .25 .18 1"/>
    <geom type="box" pos="{sx - 0.22} 0.17 {sz / 2}" size="0.015 0.015 {sz / 2}" rgba=".35 .25 .18 1"/>"""
    return f"""
<mujoco model="exoasistente_rodilla">
  <compiler angle="radian"/>
  <option timestep="0.001" integrator="implicitfast" gravity="0 0 -9.81"/>
  <default><geom contype="0" conaffinity="0"/></default>
  <visual><global offwidth="960" offheight="720"/></visual>
  <asset>
    <texture name="piso" type="2d" builtin="checker" rgb1=".86 .87 .88" rgb2=".78 .79 .8" width="256" height="256"/>
    <texture type="skybox" builtin="gradient" rgb1=".93 .94 .96" rgb2=".72 .76 .82" width="256" height="256"/>
    <material name="piso" texture="piso" texrepeat="6 6"/>
    <material name="piel" rgba=".87 .69 .56 1"/>
    <material name="ropa" rgba=".25 .33 .45 1"/>
    <material name="exo" rgba=".75 .78 .8 1" specular=".6" shininess=".8"/>
    <material name="motor" rgba=".12 .45 .8 1"/>
  </asset>
  <worldbody>
    <light pos="0.5 -2 3" dir="-0.2 1 -1.2" diffuse=".8 .8 .8"/>
    <camera name="lateral" pos="-0.15 -2.6 0.9" xyaxes="1 0 0 0 0 1"/>
    <geom type="plane" size="2 2 .1" material="piso"/>{seat}
    <geom type="box" pos="0.06 0 0.035" size="0.13 0.05 0.035" rgba=".15 .15 .15 1"/>
    <body name="pierna" pos="0 0 {H_TOBILLO}">
      <joint name="tobillo" type="hinge" axis="0 1 0" range="-0.6 0.7" limited="true"/>
      <inertial pos="0 0 {cp}" mass="{M_PIERNA}" diaginertia="{Ip} {Ip} {Ip/10}"/>
      <geom type="capsule" fromto="0 0 0 0 0 {L_PIERNA}" size="0.05" material="ropa"/>
      <geom type="box" pos="0.0 -0.075 {L_PIERNA * 0.55}" size="0.012 0.008 {L_PIERNA * 0.42}" material="exo"/>
      <geom type="box" pos="0.0 -0.06 {L_PIERNA * 0.3}" size="0.06 0.012 0.025" rgba=".1 .1 .1 1"/>
      <body name="muslo" pos="0 0 {L_PIERNA}">
        <joint name="rodilla" type="hinge" axis="0 -1 0" range="0 2.1" limited="true"/>
        <inertial pos="0 0 {cm}" mass="{M_MUSLO}" diaginertia="{Im} {Im} {Im/10}"/>
        <geom type="capsule" fromto="0 0 0 0 0 {L_MUSLO}" size="0.07" material="ropa"/>
        <geom type="cylinder" pos="0 -0.1 0" euler="1.5708 0 0" size="0.055 0.03" material="motor"/>
        <geom type="box" pos="0.0 -0.09 {L_MUSLO * 0.45}" size="0.012 0.008 {L_MUSLO * 0.42}" material="exo"/>
        <geom type="box" pos="0.0 -0.08 {L_MUSLO * 0.65}" size="0.08 0.012 0.03" rgba=".1 .1 .1 1"/>
        <body name="tronco" pos="0 0 {L_MUSLO}">
          <joint name="cadera" type="hinge" axis="0 1 0" range="-0.2 2.4" limited="true"/>
          <inertial pos="0 0 {COM_HAT}" mass="{M_HAT}" diaginertia="{Ih} {Ih} {Ih/4}"/>
          <geom type="capsule" fromto="0 0 0 0 0 0.5" size="0.12" material="ropa"/>
          <geom type="sphere" pos="0.02 0 0.68" size="0.1" material="piel"/>
          <geom type="capsule" fromto="0 -0.16 0.45 0.05 -0.16 0.2" size="0.035" material="piel"/>
          <geom name="gluteo" type="sphere" pos="-0.03 0 -0.06" size="0.07"
                contype="2" conaffinity="2"/>
          <site name="pelvis" pos="0 0 0"/>
        </body>
      </body>
    </body>
  </worldbody>
</mujoco>"""

_ASIENTO = None
def _pos_asiento():
    """Coloca la silla justo bajo el glúteo en la postura sentada."""
    global _ASIENTO
    if _ASIENTO is None:
        m = mujoco.MjModel.from_xml_string(_xml(asiento=False))
        d = mujoco.MjData(m)
        d.qpos[:] = SENTADO
        mujoco.mj_forward(m, d)
        g = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, "gluteo")
        x, _, z = d.geom_xpos[g]
        # tablero de 50 cm; borde delantero 10 cm por delante del glúteo
        _ASIENTO = (x - 0.15, z - 0.07 - 0.01)
    return _ASIENTO

# --------------------------------------------------- trayectoria de referencia
def _minjerk(t, t0, t1, a, b):
    s = np.clip((t - t0) / (t1 - t0), 0, 1)
    return a + (b - a) * (10 * s**3 - 15 * s**4 + 6 * s**5)

SENTADO = np.radians([8, 95, 95])
SEAT_OFF_REF = 0.8   # s, fin de la fase de impulso del tronco

def ref_levantarse(t):
    """Levantarse en 2,6 s (adulto mayor). Devuelve q [rad]."""
    a = _minjerk(t, 0, 0.8, 8, 16) + _minjerk(t, 0.8, 2.6, 0, -16)
    k = _minjerk(t, 0.8, 2.6, 95, 0)
    h = _minjerk(t, 0, 0.8, 95, 128) + _minjerk(t, 0.8, 2.6, 0, -128)
    return np.radians([a, k, h])

def ref_sentarse(t):
    """Sentarse en 2,6 s: la misma trayectoria recorrida al revés."""
    return ref_levantarse(2.6 - t) if t < 2.6 else SENTADO.copy()

def tabla_referencia(fref, T, dt):
    ts = np.arange(0, T + dt, dt)
    q = np.array([fref(t) for t in ts])
    qd = np.gradient(q, dt, axis=0)
    qdd = np.gradient(qd, dt, axis=0)
    return ts, q, qd, qdd

def dinamica_inversa(q, qd, qdd):
    """Par articular que la persona necesita (sin exo, sin silla)."""
    m = mujoco.MjModel.from_xml_string(_xml(asiento=False))
    d = mujoco.MjData(m)
    tau = np.zeros_like(q)
    for i in range(len(q)):
        d.qpos[:], d.qvel[:], d.qacc[:] = q[i], qd[i], qdd[i]
        mujoco.mj_inverse(m, d)
        tau[i] = d.qfrc_inverse
    return tau

# ------------------------------------------------------------ diseños de exo
@dataclass
class Transmision:
    nombre: str
    N: float          # relación de reducción
    kt: float         # N·m/A (lado motor)
    R: float          # ohm
    Jm: float         # kg·m² rotor
    eta: float        # eficiencia directa
    fric: float       # fricción de Coulomb vista desde la salida (N·m)
    visc: float = 0.2 # viscosa de la reductora vista desde la salida (N·m·s/rad)
    V: float = 12.0   # batería
    tau_max: float = 25.0

    @property
    def armadura(self): return self.Jm * self.N**2
    @property
    def b_corto(self): return self.kt**2 * self.N**2 / self.R

    @property
    def par_bloqueo(self):
        """Par de salida con el motor a tensión plena y sin límite de corriente."""
        return self.eta * self.N * self.kt * self.V / self.R

    def par_disponible(self, w, limitar=True):
        """Par de salida máximo a velocidad articular w (límite por tensión y, si limitar, por corriente)."""
        v_rest = self.V - self.kt * self.N * abs(w)
        tope = self.tau_max if limitar else np.inf
        return float(np.clip(self.eta * self.N * self.kt * v_rest / self.R, 0, tope))

# Valores representativos, no de un catálogo concreto (ver README).
DISENOS = {
    "DC 12 V + 170:1": Transmision("DC 12 V + 170:1", N=170, kt=0.0194, R=0.6, Jm=1.1e-6, eta=0.6, fric=5.0, V=12),
    "BLDC + 36:1":     Transmision("BLDC + 36:1",     N=36,  kt=0.05,   R=0.3, Jm=3.0e-5, eta=0.8, fric=1.2, V=24),
    "BLDC cuasi directo 9:1": Transmision("BLDC cuasi directo 9:1", N=9, kt=0.14, R=0.25, Jm=1.5e-4, eta=0.92, fric=0.4, V=24),
}

# -------------------------------------------------------------- simulación
@dataclass
class Config:
    tarea: str = "levantarse"          # "levantarse" | "sentarse"
    diseno: Transmision | None = None   # None = sin exo
    capacidad: float = 0.85             # fuerza de extensión de rodilla / mínima para levantarse sola
    asistencia: float = 0.25            # fracción del par de rodilla que aporta el exo
    t_inicio_asist: float = 0.4         # s, cuando se detecta la inclinación del tronco
    t_reaccion: float = 0.15            # s hasta que la persona deja de contar con el exo tras una falla
    T: float = 4.5
    # fallas
    t_falla: float | None = None
    modo_falla: str = "libre"           # "libre" | "corto" | "freno" | "diodo" | "trinquete"
    par_freno: float = 150.0            # N·m que sostiene un freno o trinquete
    # comando descontrolado del firmware
    t_runaway: float | None = None
    par_runaway: float = 25.0           # en flexión
    watchdog: float = 0.05              # s hasta el corte por hardware
    limite_hw: bool = True              # False: el driver no limita la corriente (el motor llega a su par de bloqueo)
    modo_exo_sentarse: str = "transparente"  # "transparente" | "amortiguado"
    b_amortiguado: float = 8.0

# Con este modelo, una persona necesita un par de extensión de rodilla de al menos
# UMBRAL_SOLA x (pico de dinámica inversa) para levantarse sin ayuda. Se obtuvo por
# bisección con calibrar_umbral(); "capacidad" se expresa como fracción de ese mínimo.
UMBRAL_SOLA = 1.094

# rigidez y amortiguamiento de postura (músculo + reflejos, agrupados)
KP = np.array([1500.0, 900.0, 700.0])
KD = np.array([150.0, 70.0, 60.0])

def simular(cfg: Config):
    m = mujoco.MjModel.from_xml_string(_xml())
    d = mujoco.MjData(m)
    dt = m.opt.timestep
    fref = ref_levantarse if cfg.tarea == "levantarse" else ref_sentarse
    ts, qr, qdr, qddr = tabla_referencia(fref, cfg.T, dt)
    tau_id = dinamica_inversa(qr, qdr, qddr)

    # capacidad humana: extensión de rodilla limitada al déficit; tobillo/cadera holgados
    # pico tras el despegue del asiento (antes, la silla carga el peso)
    fuera_silla = ts >= SEAT_OFF_REF if cfg.tarea == "levantarse" else ts <= 2.6 - SEAT_OFF_REF
    pico = np.abs(tau_id[fuera_silla]).max(axis=0)
    lim_rod_ext = cfg.capacidad * UMBRAL_SOLA * pico[1]
    lim = 1.5 * pico

    ex = cfg.diseno
    kk = 1  # índice de rodilla
    if ex is not None:
        m.dof_armature[kk] = ex.armadura
        m.dof_frictionloss[kk] = ex.fric
        m.dof_damping[kk] = ex.visc

    # par nominal del exo que la persona "espera" (aprendido)
    asist_on = ex is not None and cfg.tarea == "levantarse"
    tau_exo_nom = np.zeros(len(ts))
    if asist_on:
        fase = ts >= cfg.t_inicio_asist
        tau_exo_nom = np.where(fase, cfg.asistencia * tau_id[:, kk], 0.0)
        tau_exo_nom = np.clip(tau_exo_nom, -ex.tau_max, ex.tau_max)

    d.qpos[:] = qr[0]
    mujoco.mj_forward(m, d)

    n = len(ts)
    out = {k: np.zeros(n) for k in ["t", "tobillo", "rodilla", "cadera", "pelvis_z", "vz_pelvis",
                                     "tau_exo", "tau_h_rod", "f_asiento", "cop"]}
    fallado = False
    q_lock = np.inf
    corte_hw = False
    sid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_SITE, "pelvis")
    gid_asiento = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, "asiento")
    for i in range(n):
        t = ts[i]
        # la persona descuenta el par que espera del exo hasta darse cuenta de la falla
        t_ev = min(x for x in (cfg.t_falla, cfg.t_runaway, np.inf) if x is not None)
        espera = tau_exo_nom[i] if t < t_ev + cfg.t_reaccion else 0.0
        tau_h = tau_id[i] - np.array([0, espera, 0])
        tau_h = tau_h + KP * (qr[i] - d.qpos) + KD * (qdr[i] - d.qvel)
        tau_h = np.clip(tau_h, -lim, lim)
        # rodilla: + = flexión, así que extensión es par negativo
        tau_h[kk] = max(tau_h[kk], -lim_rod_ext)

        tau_e = 0.0
        if ex is not None:
            if cfg.t_falla is not None and t >= cfg.t_falla and not fallado:
                fallado = True
                if cfg.modo_falla == "corto":
                    m.dof_damping[kk] = ex.visc + ex.b_corto
                elif cfg.modo_falla == "freno":
                    m.dof_frictionloss[kk] = cfg.par_freno
            if cfg.t_runaway is not None and t >= cfg.t_runaway + cfg.watchdog and not corte_hw:
                corte_hw = True   # watchdog/límite por hardware: corta y cortocircuita
                m.dof_damping[kk] = ex.visc + ex.b_corto
            if fallado or corte_hw:
                tau_e = 0.0
                w = d.qvel[kk]
                if fallado and cfg.modo_falla == "diodo" and w > 0:
                    # cortocircuito a través de un diodo: solo frena la flexión
                    tau_e = -ex.b_corto * w
                elif fallado and cfg.modo_falla == "trinquete":
                    # bloqueo mecánico unidireccional: la rodilla puede extenderse pero no volver a flexionarse
                    q_lock = min(q_lock, d.qpos[kk])
                    pen = d.qpos[kk] - q_lock
                    if pen > 0 or w > 0:
                        tau_e = -min(cfg.par_freno, 3000.0 * pen + 100.0 * max(w, 0.0))
            elif cfg.t_runaway is not None and t >= cfg.t_runaway:
                tau_e = +cfg.par_runaway
            elif asist_on:
                tau_e = tau_exo_nom[i]
            elif cfg.tarea == "sentarse" and cfg.modo_exo_sentarse == "amortiguado":
                tau_e = -cfg.b_amortiguado * d.qvel[kk]
            if not (fallado or corte_hw):   # el límite del motor no aplica a frenos pasivos
                runaway = cfg.t_runaway is not None and t >= cfg.t_runaway
                tmax = ex.par_disponible(d.qvel[kk], limitar=not (runaway and not cfg.limite_hw))
                tau_e = float(np.clip(tau_e, -tmax, tmax))

        d.qfrc_applied[:] = tau_h
        d.qfrc_applied[kk] += tau_e
        mujoco.mj_step(m, d)

        # fuerza del asiento
        fz = 0.0
        for c in range(d.ncon):
            if gid_asiento not in (d.contact[c].geom1, d.contact[c].geom2):
                continue   # solo el asiento; el respaldo no cuenta
            f6 = np.zeros(6)
            mujoco.mj_contactForce(m, d, c, f6)
            fz += abs(f6[0])
        # centro de presión aproximado: par de tobillo / peso
        cop = tau_h[0] / (MASA * 9.81) if fz < 1 else np.nan
        vz = (d.site_xpos[sid][2] - out["pelvis_z"][i - 1]) / dt if i else 0.0
        for k, v in zip(out, [t, *np.degrees(d.qpos), d.site_xpos[sid][2], vz, tau_e, tau_h[kk], fz, cop]):
            out[k][i] = v
    out["pico_requerido_rodilla"] = pico[1]
    out["lim_rod_ext"] = lim_rod_ext
    return out

def resultado_levantarse(o):
    """Clasifica el final: 'de pie', 'vuelve a la silla' o 'colapso'."""
    fin = o["rodilla"][-1]
    tras_despegue = o["t"] > 1.2
    vuelve = np.any(o["f_asiento"][tras_despegue] > 50)
    if fin < 15 and not vuelve:
        return "de pie"
    return "vuelve a la silla" if vuelve else "queda a medio camino"

def impacto_asiento(o):
    """Velocidad de bajada de la pelvis justo antes de tocar el asiento (m/s)."""
    tras = np.where((o["t"] > 1.2) & (o["f_asiento"] > 50))[0]
    if len(tras) == 0:
        return 0.0
    j = tras[0]
    return float(-o["vz_pelvis"][max(0, j - 5)])

def calibrar_umbral(lo=0.9, hi=1.3, iters=7):
    """Busca la menor capacidad (en múltiplos del pico de dinámica inversa) con la que
    la persona se levanta sola. Devuelve el valor para UMBRAL_SOLA."""
    global UMBRAL_SOLA
    guardado, UMBRAL_SOLA = UMBRAL_SOLA, 1.0
    try:
        for _ in range(iters):
            m = (lo + hi) / 2
            if resultado_levantarse(simular(Config(capacidad=m))) == "de pie":
                hi = m
            else:
                lo = m
    finally:
        UMBRAL_SOLA = guardado
    return hi
