"""
SCRIPT 14 — CONJETURA DEL FLIP EN GRAFOS GRANDES — V25
=======================================================
Autor    : Mizael Antonio Tovar Reyes
Ubicacion: Ciudad Juarez, Chihuahua, Mexico

CONJETURA DEL FLIP (nueva, verificada exhaustivamente para n<=7 en
Script 13): para todo grafo conexo G con chi(G)=k y toda coloracion
optima, existe una secuencia de transferencias de UN vertice que
preserva en cada paso (i) k sets no vacios y (ii) adyacencia por pares,
y termina con todos los sets conexos. Implica Hadwiger.

ESTE SCRIPT: busca evidencia (o refutacion) en grafos grandes donde
el Script 13 no puede ser exhaustivo. Busqueda heuristica en el flip
graph con movimientos N3:
  - greedy sobre el potencial Phi (total de componentes) con desempate
    aleatorio
  - se permiten movimientos laterales (Phi igual) con presupuesto
  - reinicios aleatorios
HONESTIDAD: "EXITO" = secuencia encontrada (certificado positivo,
verificable). "SIN RUTA" = la heuristica no encontro; NO prueba
inalcanzabilidad. Cada exito guarda la secuencia completa de
movimientos como certificado reproducible.

Investigador : Mizael Antonio Tovar Reyes
Version      : V25 — Junio 2026
"""

import sys
import json
import time
import random
from pathlib import Path
from datetime import datetime

import networkx as nx

sys.path.insert(0, str(Path(__file__).resolve().parent))
from matr_repair_exhaustive_small import components_of, has_edge_between
from matr_repair_generalized_moves import moves_at_level
from matr_repair_hard_families import (
    mycielski_with_coloring, kneser2_with_coloring,
    optimal_coloring_bruteforce,
)

BASE_DIR = Path(__file__).resolve().parent
LOG_FILE = BASE_DIR.parent / "logs" / "log_matr_flip_conjecture_large.txt"
CERT_FILE = BASE_DIR.parent / "logs" / "certificados_flip_large.json"

RESTARTS = 25
SIDEWAYS_BUDGET = 400     # movimientos laterales permitidos por corrida
SEED = 2026


def phi(G, sets):
    return sum(len(components_of(G, s)) for s in sets)


def flip_search(G, initial_sets, rng):
    """Greedy sobre Phi con laterales y reinicio. Devuelve secuencia o None."""
    k = len(initial_sets)
    target = k
    for _ in range(RESTARTS):
        sets = [set(s) for s in initial_sets]
        seq = []
        sideways_left = SIDEWAYS_BUDGET
        visited = {frozenset(frozenset(s) for s in sets)}
        current_phi = phi(G, sets)
        dead = False
        while current_phi > target and not dead:
            moves = moves_at_level(G, tuple(frozenset(s) for s in sets), 3)
            scored = []
            for (j, v, i) in moves:
                ns = [set(s) for s in sets]
                ns[j].discard(v)
                ns[i].add(v)
                key = frozenset(frozenset(s) for s in ns)
                if key in visited:
                    continue
                scored.append((phi(G, ns), (j, v, i), ns, key))
            if not scored:
                dead = True
                break
            best_phi = min(s[0] for s in scored)
            if best_phi < current_phi:
                pool = [s for s in scored if s[0] == best_phi]
            else:
                if sideways_left <= 0:
                    dead = True
                    break
                sideways_left -= 1
                cutoff = current_phi  # laterales (no empeorar)
                pool = [s for s in scored if s[0] <= cutoff]
                if not pool:
                    dead = True
                    break
            new_phi, mv, ns, key = rng.choice(pool)
            sets = ns
            visited.add(key)
            seq.append(mv)
            current_phi = new_phi
        if current_phi == target:
            # verificacion final independiente del certificado
            assert all(len(components_of(G, s)) == 1 for s in sets)
            for a in range(k):
                for b in range(a + 1, k):
                    assert has_edge_between(G, sets[a], sets[b])
            return seq, sets
    return None, None


def attack(G, coloring, name, rng, log, certs):
    classes = {}
    for v, c in coloring.items():
        classes.setdefault(c, set()).add(v)
    initial = [classes[c] for c in sorted(classes)]
    n = G.number_of_nodes()
    k = len(initial)
    phi0 = phi(G, initial)

    t0 = time.time()
    seq, final_sets = flip_search(G, initial, rng)
    dt = time.time() - t0

    if seq is not None:
        line = (f"  [EXITO  ] {name:<24} n={n:<4} k={k:<3} Phi0={phi0:<4} "
                f"flips={len(seq):<5} {dt:5.1f}s — CONJETURA SE SOSTIENE")
        certs.append({
            "name": name, "n": n, "k": k, "phi_inicial": phi0,
            "num_flips": len(seq),
            "secuencia": [[j, str(v), i] for (j, v, i) in seq],
            "particion_final": [sorted(map(str, s)) for s in final_sets],
        })
    else:
        line = (f"  [SIN RUTA] {name:<24} n={n:<4} k={k:<3} Phi0={phi0:<4} "
                f"{dt:5.1f}s — heuristica fallo (NO es refutacion; estudiar)")
    print(line)
    sys.stdout.flush()
    log.append(line)
    return seq is not None


def main():
    t0 = time.time()
    rng = random.Random(SEED)
    print("=" * 78)
    print("  SCRIPT 14 — CONJETURA DEL FLIP EN GRAFOS GRANDES — V25")
    print("=" * 78)
    log, certs = [], []
    ok = fail = 0

    # Mycielski: sin triangulos, chi alto, clases enormes y dispersas
    for t in range(3, 8):
        G, col = mycielski_with_coloring(t)
        if attack(G, col, f"Mycielski_M{t}", rng, log, certs):
            ok += 1
        else:
            fail += 1

    # Kneser K(n,2) hasta 45 vertices, chi=8
    for n in range(5, 11):
        G, col = kneser2_with_coloring(n)
        if attack(G, col, f"Kneser_K({n},2)", rng, log, certs):
            ok += 1
        else:
            fail += 1

    # Regulares (los que se atoraron al 100% con movimientos del paper)
    for d, n in [(3, 14), (3, 20), (4, 15), (4, 21), (5, 16), (5, 22), (6, 17)]:
        for s in range(3):
            G = nx.random_regular_graph(d, n, seed=SEED + 100 * d + 10 * n + s)
            if not nx.is_connected(G):
                continue
            col, chi = optimal_coloring_bruteforce(G)
            if attack(G, col, f"Regular_{d}r_n{n}_s{s}", rng, log, certs):
                ok += 1
            else:
                fail += 1

    # Bipartitos ralos (arboles/grids: clases gigantes desconectadas)
    for name, G in [("Arbol_n31", nx.random_labeled_tree(31, seed=SEED)),
                    ("Grid_5x6", nx.convert_node_labels_to_integers(
                        nx.grid_2d_graph(5, 6))),
                    ("Hipercubo_Q4", nx.convert_node_labels_to_integers(
                        nx.hypercube_graph(4)))]:
        col = {v: (c + 1) for v, c in
               nx.algorithms.bipartite.color(G).items()}
        if attack(G, col, name, rng, log, certs):
            ok += 1
        else:
            fail += 1

    elapsed = (time.time() - t0) / 60
    print()
    print("=" * 78)
    print("  RESULTADO FINAL — CONJETURA DEL FLIP EN GRANDES")
    print("=" * 78)
    print(f"  Exitos (certificado guardado)   : {ok}")
    print(f"  Sin ruta (heuristica fallo)     : {fail}")
    print(f"  Tiempo                          : {elapsed:.1f} min")
    print("=" * 78)

    LOG_FILE.parent.mkdir(exist_ok=True)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("SCRIPT 14 — CONJETURA DEL FLIP EN GRANDES — V25\n")
        f.write(f"Investigador : Mizael Antonio Tovar Reyes\n")
        f.write(f"Fecha        : {datetime.now():%Y-%m-%d %H:%M:%S}\n")
        f.write(f"Reinicios: {RESTARTS} | Laterales: {SIDEWAYS_BUDGET} "
                f"| Semilla: {SEED}\n\n")
        for line in log:
            f.write(line + "\n")
        f.write(f"\nExitos: {ok} | Sin ruta: {fail} | {elapsed:.1f} min\n")

    with open(CERT_FILE, "w", encoding="utf-8") as f:
        json.dump(certs, f, indent=2, ensure_ascii=False)

    return fail


if __name__ == "__main__":
    main()
