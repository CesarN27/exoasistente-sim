"""
Corre los experimentos del prototipo virtual y guarda figuras + resultados.json.

    python3 experimentos.py          # todo (~3 min)
    python3 experimentos.py fallas   # solo uno: nominal | latencia | fallas | sentarse | runaway
"""
import sys, json, os, dataclasses as dc
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import exo_sim as X

AQUI = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(AQUI, "figuras")
os.makedirs(FIG, exist_ok=True)

# paleta: categórica (diseños) y estado (resultado)
SERIE = {"sin exo": "#8a8984", "DC 12 V + 170:1": "#2a78d6", "BLDC + 36:1": "#eb6834",
         "BLDC cuasi directo 9:1": "#1baf7a"}
ESTADO = {"de pie": "#0ca30c", "suave": "#fab219", "medio": "#ec835a", "fuerte": "#d03b3b"}
TXT, TXT2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({"font.size": 10, "axes.edgecolor": GRID, "axes.labelcolor": TXT2,
                     "xtick.color": TXT2, "ytick.color": TXT2, "axes.titlecolor": TXT,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb"})
R = {}

def clase(o):
    r = X.resultado_levantarse(o)
    v = X.impacto_asiento(o)
    if r == "de pie":
        return 0, "de pie", v
    if r == "queda a medio camino":
        return 2, "medio", v
    v = max(v, 0.0)
    return (1, "suave", v) if v < 0.5 else (3, "fuerte", v)

def mapa(ax, M, V, filas, cols, titulo, xlabel):
    cmap = ListedColormap([ESTADO["de pie"], ESTADO["suave"], ESTADO["medio"], ESTADO["fuerte"]])
    ax.imshow(M, cmap=cmap, vmin=-0.5, vmax=3.5, aspect="auto")
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            s = "✓" if M[i, j] == 0 else ("a medio" if M[i, j] == 2 else f"{V[i, j]:.1f}")
            ax.text(j, i, s, ha="center", va="center", fontsize=7.5,
                    color="#ffffff" if M[i, j] in (0, 3) else TXT)
    ax.set_xticks(range(len(cols)), cols)
    ax.set_yticks(range(len(filas)), filas)
    ax.set_xticks(np.arange(-.5, len(cols)), minor=True)
    ax.set_yticks(np.arange(-.5, len(filas)), minor=True)
    ax.grid(which="minor", color="#fcfcfb", linewidth=2)
    ax.tick_params(which="both", length=0)
    ax.set_title(titulo, loc="left", fontsize=11)
    ax.set_xlabel(xlabel)

def leyenda_estado(fig):
    from matplotlib.patches import Patch
    h = [Patch(color=ESTADO["de pie"], label="✓ termina de pie"),
         Patch(color=ESTADO["suave"], label="vuelve a la silla < 0,5 m/s (n = m/s)"),
         Patch(color=ESTADO["fuerte"], label="cae a la silla ≥ 0,5 m/s"),
         Patch(color=ESTADO["medio"], label="queda a medio camino")]
    fig.legend(handles=h, loc="lower center", ncol=4, frameon=False, fontsize=8.5)

# ---------------------------------------------------------------- nominal
def nominal():
    qdd = X.DISENOS["BLDC cuasi directo 9:1"]
    casos = {"sin exo": X.Config(), "con exo (BLDC 9:1)": X.Config(diseno=qdd)}
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.6))
    ts, q, _, _ = X.tabla_referencia(X.ref_levantarse, 4.5, 0.001)
    ax[0].plot(ts, np.degrees(q[:, 1]), color=TXT2, lw=1.2, ls="--", label="referencia")
    R["nominal"] = {}
    for (nom, cfg), col in zip(casos.items(), ["#8a8984", SERIE["BLDC cuasi directo 9:1"]]):
        o = X.simular(cfg)
        R["nominal"][nom] = X.resultado_levantarse(o)
        ax[0].plot(o["t"], o["rodilla"], color=col, lw=2, label=f"{nom}: {R['nominal'][nom]}")
        ax[1].plot(o["t"], -o["tau_h_rod"], color=col, lw=2, label=f"persona ({nom})")
        if cfg.diseno:
            ax[1].plot(o["t"], -o["tau_exo"], color="#2a78d6", lw=2, label="exo")
    ax[1].axhline(o["lim_rod_ext"], color=TXT2, lw=1, ls=":")
    ax[1].text(4.4, o["lim_rod_ext"] + 3, "fuerza máxima de la persona", ha="right", fontsize=8, color=TXT2)
    ax[0].set(xlabel="tiempo (s)", ylabel="flexión de rodilla (°)", xlim=(0, 4.5))
    ax[1].set(xlabel="tiempo (s)", ylabel="par de extensión de rodilla (N·m)", xlim=(0, 4.5))
    ax[0].set_title("Levantarse con 85% de la fuerza necesaria", loc="left", fontsize=11)
    ax[1].set_title("Quién pone el par", loc="left", fontsize=11)
    for a in ax:
        a.legend(frameon=False, fontsize=8); a.grid(color=GRID, lw=.6)
    fig.tight_layout(); fig.savefig(f"{FIG}/1_nominal.png", dpi=160); plt.close(fig)

# ---------------------------------------------------------------- latencia
def latencia():
    d = X.DISENOS["BLDC cuasi directo 9:1"]
    onsets = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
    caps = [0.95, 0.9, 0.85, 0.8, 0.75]
    M = np.zeros((len(caps), len(onsets))); V = np.zeros_like(M)
    for i, c in enumerate(caps):
        for j, t0 in enumerate(onsets):
            M[i, j], _, V[i, j] = clase(X.simular(X.Config(diseno=d, capacidad=c, t_inicio_asist=t0)))
    R["latencia"] = {"inicio_asistencia_s": onsets, "capacidad": caps, "clase": M.tolist()}
    fig, ax = plt.subplots(figsize=(8, 3.4))
    mapa(ax, M, V, [f"{int(c*100)}%" for c in caps], [f"{t:.1f}" for t in onsets],
         "¿Cuándo tiene que empezar a ayudar el exo? (despegue del asiento a 0,8 s)",
         "inicio de la asistencia desde que empieza a inclinar el tronco (s)")
    ax.set_ylabel("fuerza de la persona")
    leyenda_estado(fig); fig.tight_layout(rect=(0, .08, 1, 1))
    fig.savefig(f"{FIG}/2_latencia.png", dpi=160); plt.close(fig)

# ---------------------------------------------------------------- fallas
MODOS = {"libre": "libre (sin energía)", "corto": "bobinado en corto",
         "diodo": "corto con diodo (solo frena flexión)", "freno": "freno 150 N·m",
         "trinquete": "trinquete (bloquea flexión)"}

def fallas():
    tf = np.round(np.arange(0.6, 2.21, 0.1), 2)
    filas, M, V = [], [], []
    for k, d in X.DISENOS.items():
        for m, etiqueta in MODOS.items():
            fila_m, fila_v = [], []
            for t in tf:
                c, _, v = clase(X.simular(X.Config(diseno=d, t_falla=float(t), modo_falla=m)))
                fila_m.append(c); fila_v.append(v)
            filas.append(f"{k} · {etiqueta}"); M.append(fila_m); V.append(fila_v)
    M, V = np.array(M), np.array(V)
    R["fallas"] = {"t_falla_s": tf.tolist(), "filas": filas, "clase": M.tolist(),
                   "impacto_m_s": np.round(V, 2).tolist()}
    ts, q, _, _ = X.tabla_referencia(X.ref_levantarse, 3, 0.001)
    rod = [int(round(np.degrees(q[int(t / 0.001), 1]))) for t in tf]
    fig, ax = plt.subplots(figsize=(12, 7.2))
    mapa(ax, M, V, filas, [f"{t:.1f}\n{r}°" for t, r in zip(tf, rod)],
         "Falla del exo a mitad del levantarse (persona con 85% de la fuerza necesaria)",
         "momento de la falla (s) y flexión de rodilla en ese momento")
    for y in (4.5, 9.5):
        ax.axhline(y, color="#fcfcfb", lw=6)
    leyenda_estado(fig); fig.tight_layout(rect=(0, .05, 1, 1))
    fig.savefig(f"{FIG}/3_fallas.png", dpi=160); plt.close(fig)

# ---------------------------------------------------------------- sentarse
def sentarse():
    caps = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5]
    qdd, dcm = X.DISENOS["BLDC cuasi directo 9:1"], X.DISENOS["DC 12 V + 170:1"]
    series = {"sin exo": ({}, SERIE["sin exo"], "-"),
              "DC 170:1 apagado": ({"diseno": dcm}, SERIE["DC 12 V + 170:1"], "-"),
              "BLDC 9:1 apagado": ({"diseno": qdd}, SERIE["BLDC cuasi directo 9:1"], "--"),
              "BLDC 9:1 sin energía, corto con diodo": ({"diseno": qdd, "t_falla": 0.0, "modo_falla": "diodo"},
                                                        "#4a3aa7", "-"),
              "BLDC 9:1 amortiguando (8 N·m·s/rad)": ({"diseno": qdd, "modo_exo_sentarse": "amortiguado"},
                                                      SERIE["BLDC cuasi directo 9:1"], "-")}
    R["sentarse"] = {"capacidad": caps}
    fig, ax = plt.subplots(figsize=(7.5, 4))
    for nom, (kw, col, ls) in series.items():
        v = [X.impacto_asiento(X.simular(X.Config(tarea="sentarse", capacidad=c, T=4, **kw))) for c in caps]
        R["sentarse"][nom] = np.round(v, 2).tolist()
        ax.plot([c * 100 for c in caps], v, color=col, ls=ls, lw=2, marker="o", ms=5, label=nom)
    ax.axhline(0.5, color=TXT2, lw=1, ls=":")
    ax.text(51, 0.53, "0,5 m/s", fontsize=8, color=TXT2)
    ax.invert_xaxis()
    ax.set(xlabel="fuerza de la persona (% de la necesaria para levantarse sola)",
           ylabel="velocidad al tocar la silla (m/s)")
    ax.set_title("Sentarse: qué tan fuerte cae a la silla", loc="left", fontsize=11)
    ax.grid(color=GRID, lw=.6); ax.legend(frameon=False, fontsize=8.5)
    fig.tight_layout(); fig.savefig(f"{FIG}/4_sentarse.png", dpi=160); plt.close(fig)

# ---------------------------------------------------------------- firmware descontrolado
T_RUN = 1.7   # s: momento en que cualquier diseño, si solo se apagara, igual terminaría de pie

def runaway():
    Ws = [0.02, 0.05, 0.1, 0.2, 0.5]
    filas, M, V = [], [], []
    for k, d in X.DISENOS.items():
        stall = d.par_bloqueo
        for lim in (False, True):
            par = d.tau_max if lim else stall
            fm, fv = [], []
            for W in Ws:
                c, _, v = clase(X.simular(X.Config(diseno=d, t_runaway=T_RUN, watchdog=W,
                                                    par_runaway=par, limite_hw=lim)))
                fm.append(c); fv.append(v)
            filas.append(f"{k} · " + ("límite 25 N·m por hardware" if lim else f"sin límite ({stall:.0f} N·m)"))
            M.append(fm); V.append(fv)
    M, V = np.array(M), np.array(V)
    R["runaway"] = {"watchdog_s": Ws, "filas": filas, "clase": M.tolist(), "impacto_m_s": np.round(V, 2).tolist()}
    fig, ax = plt.subplots(figsize=(10, 3.8))
    mapa(ax, M, V, filas, [f"{int(w*1000)} ms" for w in Ws],
         "Firmware descontrolado a 1,7 s: el motor empuja en flexión hasta el corte",
         "tiempo hasta que el watchdog por hardware corta la potencia")
    leyenda_estado(fig); fig.tight_layout(rect=(0, .1, 1, 1))
    fig.savefig(f"{FIG}/5_runaway.png", dpi=160); plt.close(fig)

# ---------------------------------------------------------------- transparencia
def transparencia():
    """Par parásito que la persona tiene que vencer para mover el exo apagado."""
    ts, q, qd, qdd = X.tabla_referencia(X.ref_levantarse, 3, 0.001)
    R["transparencia"] = {}
    for k, d in X.DISENOS.items():
        tau = d.armadura * np.abs(qdd[:, 1]) + d.fric + d.visc * np.abs(qd[:, 1])
        R["transparencia"][k] = {"armadura_kgm2": round(d.armadura, 4), "friccion_Nm": d.fric,
                                 "b_corto_Nms_rad": round(d.b_corto, 1),
                                 "par_parasito_pico_Nm": round(float(tau.max()), 1),
                                 "par_bloqueo_Nm": round(d.par_bloqueo, 0)}

if __name__ == "__main__":
    todos = {"nominal": nominal, "latencia": latencia, "fallas": fallas,
             "sentarse": sentarse, "runaway": runaway, "transparencia": transparencia}
    elegidos = sys.argv[1:] or list(todos)
    for n in elegidos:
        print("→", n, flush=True); todos[n]()
    ruta = os.path.join(AQUI, "resultados.json")
    previo = json.load(open(ruta)) if os.path.exists(ruta) else {}
    previo.update(R)
    json.dump(previo, open(ruta, "w"), ensure_ascii=False, indent=1)
    print("listo:", ruta)
