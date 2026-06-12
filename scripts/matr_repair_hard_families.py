"""
SCRIPT 12 — REPARACION EN FAMILIAS DURAS — V25
================================================================
Autor    : Mizael Antonio Tovar Reyes
Ubicacion: Ciudad Juarez, Chihuahua, Mexico

QUE HACE (NUEVO EN V25):
  Ejecuta la construccion FIEL al paper V24 Sec. 4.1 (condiciones
  (a)/(b)/(c) por movimiento, sets siempre disjuntos) sobre las familias
  donde Hadwiger es realmente dificil: chi alto con clases de color
  grandes y dispersas.

  CLAVE TEORICA QUE PERMITE LLEGAR LEJOS:
  - p(G) = chi(G) - 1 SIEMPRE (Proposicion 3.1, probada) -> no se busca
    por fuerza bruta; el ordenamiento por clases de color es optimo.
  - Mycielski M_t: chi conocido = t y coloracion optima CONSTRUIBLE por
    recursion (la copia sombra hereda colores, el apex estrena color).
  - Kneser K(n,2): chi = n-2 (Lovasz 1978) y coloracion optima explicita:
    clase i = {pares con min = i} para i=1..n-3, mas la clase de los
    pares dentro de los ultimos 3 elementos (pairwise intersectantes).
  Eso da coloraciones optimas EXACTAS para grafos de 100+ vertices sin
  resolver chi por backtracking.

  Para cada (grafo, coloracion): busqueda con reinicios aleatorios
  (multi-restart) sobre las secuencias de movimientos. Si TODOS los
  reinicios mueren, se registra el estado atorado con su taxonomia
  (T_A / T_B trampa articulacion / T_C trampa adyacencia / T_MIX).

  HONESTIDAD: a diferencia del Script 11 (exhaustivo), aqui "atorado"
  significa "ningun reinicio lo logro", NO "es imposible". Los atorados
  se guardan en JSON para estudio posterior.

Investigador : Mizael Antonio Tovar Reyes
Version      : V25 — Junio 2026
"""

import sys
import json
import time
import random
import itertools
from pathlib import Path
from collections import deque
from datetime import datetime

import networkx as nx

sys.path.insert(0, str(Path(__file__).resolve().parent))
from matr_repair_exhaustive_small import (
    components_of, legal_moves, classify_stuck, chromatic_exact_small,
)

BASE_DIR = Path(__file__).resolve().parent
LOG_FILE = BASE_DIR.parent / "logs" / "log_matr_repair_hard_families.txt"
STUCK_FILE = BASE_DIR.parent / "logs" / "atorados_familias_duras.json"

RESTARTS = 60          # reinicios aleatorios por (grafo, coloracion)
MAX_MOVES = 5000       # tope duro (Phi garantiza <= n-k en realidad)
SEED = 2026


# ─────────────────────────────────────────────────────────────────────────────
# COLORACIONES OPTIMAS CONSTRUIDAS POR TEORIA (sin fuerza bruta)
# ─────────────────────────────────────────────────────────────────────────────

def mycielski_with_coloring(t):
    """
    M_2 = K_2, M_{i+1} = mycielskian(M_i). chi(M_t) = t (Mycielski 1955).
    Coloracion optima recursiva: si col es t-coloracion de M, en mu(M)
    los originales conservan color, las sombras u_i' toman col(u_i)
    (sombra solo ve vecinos del original, mismo conjunto de colores
    prohibidos... pero hay que evitar el color del original? NO:
    u_i' NO es adyacente a u_i, asi que col(u_i) es legal), y el apex
    estrena el color t+1 (es adyacente a todas las sombras, que usan
    los t colores). Verificado con assert al construir.
    """
    G = nx.complete_graph(2)  # M_2
    coloring = {0: 1, 1: 2}
    for target in range(3, t + 1):
        n = G.number_of_nodes()
        H = nx.Graph()
        H.add_nodes_from(range(2 * n + 1))
        new_col = {}
        for u, v in G.edges():
            H.add_edge(u, v)                    # original
            H.add_edge(u, n + v)                # original-sombra
            H.add_edge(v, n + u)
        apex = 2 * n
        for i in range(n):
            H.add_edge(n + i, apex)
            new_col[i] = coloring[i]
            new_col[n + i] = coloring[i]
        new_col[apex] = target
        G, coloring = H, new_col
    # verificacion de propiedad
    for u, v in G.edges():
        assert coloring[u] != coloring[v], "coloracion Mycielski invalida"
    return G, coloring


def kneser2_with_coloring(n):
    """
    K(n,2): vertices = pares de [n], aristas entre pares disjuntos.
    chi = n - 2 (Lovasz). Coloracion optima explicita:
      clase i (i=1..n-3): pares cuyo minimo es i
      clase n-2         : pares dentro de {n-2, n-1, n} (se intersectan
                          dos a dos -> conjunto independiente)
    """
    subsets = list(itertools.combinations(range(1, n + 1), 2))
    idx = {s: i for i, s in enumerate(subsets)}
    G = nx.Graph()
    G.add_nodes_from(range(len(subsets)))
    for a, b in itertools.combinations(subsets, 2):
        if not set(a) & set(b):
            G.add_edge(idx[a], idx[b])
    coloring = {}
    last3 = {n - 2, n - 1, n}
    for s in subsets:
        if set(s) <= last3:
            coloring[idx[s]] = n - 2
        else:
            coloring[idx[s]] = min(s)
    for u, v in G.edges():
        assert coloring[u] != coloring[v], "coloracion Kneser invalida"
    return G, coloring


def optimal_coloring_bruteforce(G):
    """Para grafos chicos/aleatorios: chi exacto + una coloracion optima."""
    chi = chromatic_exact_small(G)
    nodes = list(G.nodes())
    adj = {v: set(G.neighbors(v)) for v in nodes}
    col = {}

    def bt(i):
        if i == len(nodes):
            return True
        v = nodes[i]
        used = {col[u] for u in adj[v] if u in col}
        for c in range(1, chi + 1):
            if c not in used:
                col[v] = c
                if bt(i + 1):
                    return True
                del col[v]
        return False

    bt(0)
    return dict(col), chi


# ─────────────────────────────────────────────────────────────────────────────
# REPARACION CON REINICIOS ALEATORIOS
# ─────────────────────────────────────────────────────────────────────────────

def repair_randomized(G, initial_sets, rng):
    """Una corrida: elige movimientos al azar hasta conectar o atorarse."""
    sets = [set(s) for s in initial_sets]
    moves_done = 0
    while moves_done <= MAX_MOVES:
        if all(len(components_of(G, s)) == 1 for s in sets):
            return "SUCCESS", sets, None, moves_done
        moves, failures = legal_moves(G, tuple(frozenset(s) for s in sets))
        if not moves:
            tax = classify_stuck(failures, True)
            return "STUCK", sets, tax, moves_done
        j, v, i = rng.choice(moves)
        sets[j].discard(v)
        sets[i].add(v)
        moves_done += 1
    return "OVERFLOW", sets, None, moves_done


def attack(G, coloring, name, rng, log):
    chi = max(coloring.values())
    classes = {}
    for v, c in coloring.items():
        classes.setdefault(c, set()).add(v)
    initial = [classes[c] for c in sorted(classes)]
    n = G.number_of_nodes()

    disconnected0 = sum(1 for s in initial if len(components_of(G, s)) > 1)

    best = None
    stuck_seen = []
    for r in range(RESTARTS):
        status, sets, tax, nm = repair_randomized(G, initial, rng)
        if status == "SUCCESS":
            best = ("SUCCESS", nm, r + 1)
            break
        stuck_seen.append((tax, [sorted(s) for s in sets]))

    if best:
        line = (f"  [EXITO ] {name:<24} n={n:<4} chi={chi:<3} "
                f"clases_desc={disconnected0:<3} movs={best[1]:<4} "
                f"intentos={best[2]}")
        result = {"name": name, "n": n, "chi": chi, "status": "SUCCESS",
                  "moves": best[1], "restarts_used": best[2]}
    else:
        taxs = [t for t, _ in stuck_seen if t]
        tax_summary = {t: taxs.count(t) for t in set(taxs)}
        line = (f"  [ATORADO] {name:<24} n={n:<4} chi={chi:<3} "
                f"clases_desc={disconnected0:<3} "
                f"{RESTARTS} reinicios fallaron — taxonomia={tax_summary}")
        result = {"name": name, "n": n, "chi": chi, "status": "STUCK",
                  "taxonomia": tax_summary,
                  "edges": sorted(map(sorted, G.edges())),
                  "coloracion": {str(k): v for k, v in coloring.items()},
                  "ejemplo_estado": stuck_seen[0][1] if stuck_seen else None}
    print(line)
    sys.stdout.flush()
    log.append(line)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    t0 = time.time()
    rng = random.Random(SEED)
    print("=" * 76)
    print("  SCRIPT 12 — REPARACION FIEL (Sec. 4.1) EN FAMILIAS DURAS — V25")
    print("=" * 76)
    log = []
    results = []

    # 1) Mycielski M_3..M_7 (chi=3..7; M_7 tiene 95 vertices, sin triangulos)
    for t in range(3, 8):
        G, col = mycielski_with_coloring(t)
        results.append(attack(G, col, f"Mycielski_M{t}", rng, log))

    # 2) Kneser K(n,2), n=5..10 (K(10,2): 45 vertices, chi=8)
    for n in range(5, 11):
        G, col = kneser2_with_coloring(n)
        results.append(attack(G, col, f"Kneser_K({n},2)", rng, log))

    # 3) Regulares aleatorios d-regular (clases dispersas por naturaleza)
    for d, n in [(3, 14), (3, 20), (4, 15), (4, 21), (5, 16), (5, 22), (6, 17)]:
        for s in range(3):
            G = nx.random_regular_graph(d, n, seed=SEED + 100 * d + 10 * n + s)
            if not nx.is_connected(G):
                continue
            col, chi = optimal_coloring_bruteforce(G)
            results.append(attack(G, col, f"Regular_{d}r_n{n}_s{s}", rng, log))

    # 4) Erdos-Renyi densos (chi alto)
    cnt = 0
    trial = 0
    while cnt < 40 and trial < 400:
        trial += 1
        n = rng.randint(10, 22)
        p = rng.uniform(0.45, 0.8)
        G = nx.gnp_random_graph(n, p, seed=SEED * 31 + trial)
        if not nx.is_connected(G):
            continue
        col, chi = optimal_coloring_bruteforce(G)
        if chi < 5:
            continue  # solo casos duros: chi >= 5
        cnt += 1
        results.append(attack(G, col, f"GNP_n{n}_chi{chi}_t{trial}", rng, log))

    elapsed = (time.time() - t0) / 60
    succ = [r for r in results if r["status"] == "SUCCESS"]
    stuck = [r for r in results if r["status"] == "STUCK"]

    print()
    print("=" * 76)
    print("  RESULTADO FINAL — FAMILIAS DURAS")
    print("=" * 76)
    print(f"  Grafos atacados      : {len(results)}")
    print(f"  Reparacion EXITOSA   : {len(succ)}")
    print(f"  ATORADOS (60 reinicios): {len(stuck)}")
    if stuck:
        print("  Atorados (candidatos a obstruccion, estudiar):")
        for r in stuck:
            print(f"    - {r['name']} n={r['n']} chi={r['chi']} tax={r['taxonomia']}")
    print(f"  Tiempo               : {elapsed:.1f} min")
    print("=" * 76)

    LOG_FILE.parent.mkdir(exist_ok=True)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("SCRIPT 12 — FAMILIAS DURAS — V25\n")
        f.write(f"Investigador : Mizael Antonio Tovar Reyes\n")
        f.write(f"Fecha        : {datetime.now():%Y-%m-%d %H:%M:%S}\n")
        f.write(f"Reinicios    : {RESTARTS} | Semilla: {SEED}\n\n")
        for line in log:
            f.write(line + "\n")
        f.write(f"\nExitosos: {len(succ)} / {len(results)}\n")
        f.write(f"Atorados: {len(stuck)}\n")
        f.write(f"Tiempo: {elapsed:.1f} min\n")

    if stuck:
        with open(STUCK_FILE, "w", encoding="utf-8") as f:
            json.dump(stuck, f, indent=2, ensure_ascii=False)

    return len(stuck)


if __name__ == "__main__":
    main()
