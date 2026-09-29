"""Genera las imágenes de los 4 casos de la guía (fotogramas + gráficas) y casos.json."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("MUJOCO_GL", "osmesa")
import numpy as np, mujoco
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import exo_sim as X

AQUI = os.path.dirname(os.path.abspath(__file__)); IMG = os.path.join(AQUI, "img"); os.makedirs(IMG, exist_ok=True)
D = X.DISENOS
CASOS = {
  "A": dict(titulo="Todo sale bien", cfg=X.Config(diseno=D["BLDC cuasi directo 9:1"]), evento=None),
  "B1": dict(titulo="El exo se apaga a mitad de la subida", cfg=X.Config(diseno=D["DC 12 V + 170:1"], t_falla=1.3, modo_falla="libre"), evento=(1.3, "el exo se apaga")),
  "B2": dict(titulo="El motor se vuelve loco y no tiene tope de fuerza", cfg=X.Config(diseno=D["BLDC + 36:1"], t_runaway=1.7, watchdog=0.2, par_runaway=D["BLDC + 36:1"].par_bloqueo, limite_hw=False), evento=(1.7, "el motor empuja al revés")),
  "B3": dict(titulo="La asistencia llega tarde", cfg=X.Config(diseno=D["BLDC cuasi directo 9:1"], capacidad=0.90, t_inicio_asist=0.7), evento=(0.7, "el exo empieza a ayudar")),
}
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
AZUL, GRIS, VERDE, ROJO = "#2a78d6", "#8a8984", "#1baf7a", "#d03b3b"
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "figure.facecolor": "white"})
def render(m, d, r, q):
    d.qpos[:] = q; mujoco.mj_forward(m, d); r.update_scene(d, camera="lateral"); return r.render()

out = {}
m = mujoco.MjModel.from_xml_string(X._xml()); d = mujoco.MjData(m); r = mujoco.Renderer(m, 360, 480)
ts, qref, _, _ = X.tabla_referencia(X.ref_levantarse, 4.5, 0.001)
for k, c in CASOS.items():
    o = X.simular(c["cfg"]); t = o["t"]
    res = X.resultado_levantarse(o); v = max(X.impacto_asiento(o), 0.0)
    cae = np.where((t > 1.2) & (o["f_asiento"] > 50))[0]
    t_imp = float(t[cae[0]]) if len(cae) else None
    fin = t_imp + 0.5 if t_imp else 2.9
    if k == "A": tiempos = [0.0, 0.7, 1.3, 1.9, 2.7]
    else:
        base = {"B1": [0.0, 1.0, 1.4, 2.0], "B2": [0.0, 1.3, 1.9, 2.9], "B3": [0.0, 0.7, 1.3, 1.8]}[k]
        tiempos = base + [round(t_imp + 0.05, 2)]
    q = np.radians(np.c_[o["tobillo"], o["rodilla"], o["cadera"]])
    fig, ax = plt.subplots(1, len(tiempos), figsize=(3 * len(tiempos), 2.55))
    for a, tt in zip(np.atleast_1d(ax), tiempos):
        a.imshow(render(m, d, r, q[int(tt / 0.001)])); a.axis("off")
        a.set_title(f"{tt:.1f} s", fontsize=13, color=INK, fontweight="bold")
    fig.subplots_adjust(wspace=0.02, left=0.005, right=0.995, top=0.88, bottom=0.0)
    fig.savefig(f"{IMG}/{k}_fotos.png", dpi=110); plt.close(fig)
    # gráficas
    fig, ax = plt.subplots(1, 2, figsize=(9.6, 3.1))
    hi = t <= fin
    ax[0].plot(ts[ts <= fin], np.degrees(qref[ts <= fin, 1]), color=INK2, ls="--", lw=1.2, label="lo que debería hacer")
    ax[0].plot(t[hi], o["rodilla"][hi], color=VERDE if res == "de pie" else ROJO, lw=2.4, label="lo que hace la rodilla")
    ax[0].set(xlabel="tiempo (s)", ylabel="rodilla doblada (°)\n95° sentada · 0° de pie", xlim=(0, fin))
    ax[1].plot(t[hi], np.clip(-o["tau_h_rod"][hi], 0, None), color=GRIS, lw=2, label="la persona")
    ax[1].plot(t[hi], np.abs(o["tau_exo"][hi]) * np.sign(-o["tau_exo"][hi]), color=AZUL, lw=2, label="el exo")
    ax[1].axhline(o["lim_rod_ext"], color=GRIS, ls=":", lw=1)
    ax[1].text(0.02, o["lim_rod_ext"] + 3, "tope de fuerza de la persona", fontsize=8, color=INK2)
    inf = min(-30, float(np.min(-o["tau_exo"][hi])) - 8)
    ax[1].set(xlabel="tiempo (s)", ylabel="fuerza de extensión (N·m)", xlim=(0, fin), ylim=(inf, 135))
    if c["evento"]:
        for a in ax:
            a.axvline(c["evento"][0], color=ROJO if k != "B3" else AZUL, lw=1, ls="-.")
        ax[0].text(c["evento"][0] + 0.03, 60, c["evento"][1], fontsize=8.5, color=INK, rotation=90, va="center")
    if t_imp:
        for a in ax: a.axvline(t_imp, color=ROJO, lw=1)
        ax[0].text(t_imp + 0.03, 20, f"toca la silla\na {v:.1f} m/s", fontsize=8.5, color=ROJO)
    for a in ax: a.grid(color=GRID, lw=.6)
    ax[0].legend(frameon=False, fontsize=8, loc="upper right"); ax[1].legend(frameon=False, fontsize=8, loc="center right")
    fig.tight_layout(); fig.savefig(f"{IMG}/{k}_graf.png", dpi=130); plt.close(fig)
    out[k] = dict(titulo=c["titulo"], resultado=res, impacto_m_s=round(v, 2), t_impacto=t_imp, fotos=tiempos)
    print(k, res, round(v, 2), t_imp, tiempos)
json.dump(out, open(f"{AQUI}/casos.json", "w"), ensure_ascii=False, indent=1)
