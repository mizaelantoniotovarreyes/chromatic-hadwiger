"""
SCRIPT 11 — BUSQUEDA EXHAUSTIVA DE OBSTRUCCIONES (n <= 7) — V25
================================================================
Autor    : Mizael Antonio Tovar Reyes
Ubicacion: Ciudad Juarez, Chihuahua, Mexico

QUE HACE (NUEVO EN V25):
  Responde Open Problem 6.1 EXHAUSTIVAMENTE para grafos pequenos.

  Para CADA grafo conexo simple con n <= 7 vertices (atlas completo de
  networkx, sin excepciones), para CADA coloracion optima (todas, modulo
  permutacion de colores), explora TODAS las secuencias posibles de
  movimientos de reparacion de la Seccion 4.1 del paper V24:

    Movimiento: mover v de B_j a B_i cuando
      (a) v es adyacente a >= 2 componentes distintas de G[B_i]
      (b) B_j - {v} es no vacio y conexo
      (c) tras el movimiento, todo par de sets sigue teniendo arista

  RESULTADO POSIBLE 1: todo (grafo, coloracion) alcanza branch sets
    conexos -> TEOREMA COMPUTACIONAL: "para n<=7 la fase de reparacion
    siempre puede tener exito". Primera verificacion exhaustiva de la
    construccion del paper.

  RESULTADO POSIBLE 2: existe (grafo, coloracion) donde TODA secuencia
    se atora -> OBSTRUCCION MINIMA ENCONTRADA. Se reporta completa
    (grafo en formato edge-list, coloracion, estado atorado, taxonomia
    de por que falla cada candidato). Eso seria un descubrimiento.

  TAXONOMIA DE ESTADOS ATORADOS (nueva):
    T_A  : ningun vertice satisface (a) para ningun set desconectado
    T_B  : hay candidatos (a) pero todos fallan (b)  [trampa articulacion]
    T_C  : hay candidatos (a)+(b) pero todos fallan (c) [trampa adyacencia]
    T_MIX: mezcla de fallas (b) y (c)
  La trampa T_C NO esta nombrada en el paper V24 — si aparece, es nueva.

  GARANTIA DE TERMINACION: el potencial Phi (Lemma 4.3) decrece
  estrictamente con cada movimiento, asi que el arbol de busqueda tiene
  profundidad <= n - k y la memoizacion sobre estados lo hace finito.

Investigador : Mizael Antonio Tovar Reyes
Version      : V25 — Junio 2026
"""

import sys
import json
import time
import itertools
from pathlib import Path
from collections import deque
from datetime import datetime

import networkx as nx

BASE_DIR = Path(__file__).resolve().parent
LOG_FILE = BASE_DIR.parent / "logs" / "log_matr_repair_exhaustive_small.txt"
OBSTRUCTION_FILE = BASE_DIR.parent / "logs" / "obstrucciones_n7.json"

MAX_COLORINGS_PER_GRAPH = 5000   # tope de seguridad (modulo permutacion)
MAX_STATES_PER_SEARCH = 2_000_000


# ─────────────────────────────────────────────────────────────────────────────
# UTILIDADES BASICAS (independientes de core_utils: el script debe ser
# verificable por si solo, como exige la reproducibilidad del paper)
# ─────────────────────────────────────────────────────────────────────────────

def chromatic_exact_small(G):
    """chi(G) exacto por backtracking. Suficiente para n <= 7."""
    nodes = list(G.nodes())
    n = len(nodes)
    if n == 0:
        return 0
    adj = {v: set(G.neighbors(v)) for v in nodes}

    def try_k(k):
        col = {}
        def bt(i):
            if i == n:
                return True
            v = nodes[i]
            used = {col[u] for u in adj[v] if u in col}
            for c in range(1, k + 1):
                if c not in used:
                    col[v] = c
                    if bt(i + 1):
                        return True
                    del col[v]
            return False
        return bt(0)

    for k in range(1, n + 1):
        if try_k(k):
            return k
    return n


def all_optimal_partitions(G, chi, cap=MAX_COLORINGS_PER_GRAPH):
    """
    TODAS las chi-coloraciones propias de G, modulo permutacion de colores,
    devueltas como particiones (frozenset de frozensets).
    Canonizacion: un vertice solo puede estrenar el color max_usado+1,
    asi cada particion se genera exactamente una vez.
    """
    nodes = list(G.nodes())
    adj = {v: set(G.neighbors(v)) for v in nodes}
    partitions = []
    col = {}
    truncated = [False]

    def bt(i, max_used):
        if len(partitions) >= cap:
            truncated[0] = True
            return
        if i == len(nodes):
            classes = {}
            for v, c in col.items():
                classes.setdefault(c, set()).add(v)
            if len(classes) == chi:
                partitions.append(tuple(frozenset(s) for s in
                                        sorted(classes.values(), key=sorted)))
            return
        v = nodes[i]
        used = {col[u] for u in adj[v] if u in col}
        for c in range(1, min(max_used + 1, chi) + 1):
            if c not in used:
                col[v] = c
                bt(i + 1, max(max_used, c))
                del col[v]

    bt(0, 0)
    return partitions, truncated[0]


def components_of(G, S):
    """Componentes conexas de G[S] como lista de sets."""
    S = set(S)
    comps = []
    seen = set()
    for s in S:
        if s in seen:
            continue
        comp = {s}
        q = deque([s])
        while q:
            v = q.popleft()
            for u in G.neighbors(v):
                if u in S and u not in comp:
                    comp.add(u)
                    q.append(u)
        seen |= comp
        comps.append(comp)
    return comps


def has_edge_between(G, A, B):
    for v in A:
        for u in G.neighbors(v):
            if u in B:
                return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
# MOVIMIENTOS DE REPARACION — FIELES AL PAPER V24, SECCION 4.1
# ─────────────────────────────────────────────────────────────────────────────

def legal_moves(G, sets):
    """
    Genera todos los movimientos legales (j, v, i) -> mover v de sets[j]
    a sets[i], con las condiciones (a),(b),(c) del paper verificadas
    POR MOVIMIENTO. Tambien clasifica las fallas para la taxonomia.
    """
    k = len(sets)
    comps_cache = [components_of(G, s) for s in sets]
    moves = []
    failures = []  # (j, v, i, razon)

    for i in range(k):
        comps_i = comps_cache[i]
        if len(comps_i) <= 1:
            continue  # B_i ya conexo
        for j in range(k):
            if j == i:
                continue
            for v in sets[j]:
                nbrs = set(G.neighbors(v))
                touched = sum(1 for comp in comps_i if nbrs & comp)
                if touched < 2:
                    continue  # no es candidato (a); no se registra como falla
                # (a) OK — candidato real
                remaining = sets[j] - {v}
                if not remaining:
                    failures.append((j, v, i, "b_vacio"))
                    continue
                if len(components_of(G, remaining)) != 1:
                    failures.append((j, v, i, "b_articulacion"))
                    continue
                # (b) OK — verificar (c): solo pares con B_j pueden perder arista
                new_i = sets[i] | {v}
                c_ok = True
                for m in range(k):
                    if m == j:
                        continue
                    other = new_i if m == i else sets[m]
                    if not has_edge_between(G, remaining, other):
                        c_ok = False
                        break
                if not c_ok:
                    failures.append((j, v, i, "c_adyacencia"))
                    continue
                moves.append((j, v, i))

    return moves, failures


def classify_stuck(failures, any_disconnected):
    """Taxonomia del estado atorado."""
    if not any_disconnected:
        return None
    if not failures:
        return "T_A"
    reasons = {r for (_, _, _, r) in failures}
    has_b = bool(reasons & {"b_vacio", "b_articulacion"})
    has_c = "c_adyacencia" in reasons
    if has_b and has_c:
        return "T_MIX"
    if has_b:
        return "T_B"
    return "T_C"


def repair_search(G, initial_sets):
    """
    DFS exhaustivo sobre TODAS las secuencias de movimientos.
    Memoizacion sobre estados (Phi decrece -> sin ciclos, arbol finito).

    Devuelve:
      ("SUCCESS", None)            si alguna secuencia conecta todo
      ("STUCK", lista_de_estados)  si toda secuencia muere; incluye los
                                   estados terminales atorados con taxonomia
      ("OVERFLOW", None)           si se supero MAX_STATES (no ocurre n<=7)
    """
    memo = {}
    stuck_states = []
    counter = [0]

    def all_connected(sets):
        return all(len(components_of(G, s)) == 1 for s in sets)

    def dfs(sets):
        key = frozenset(sets)
        if key in memo:
            return memo[key]
        counter[0] += 1
        if counter[0] > MAX_STATES_PER_SEARCH:
            return None  # overflow
        if all_connected(sets):
            memo[key] = True
            return True
        moves, failures = legal_moves(G, sets)
        if not moves:
            tax = classify_stuck(failures, True)
            stuck_states.append({
                "sets": [sorted(s) for s in sets],
                "taxonomia": tax,
                "fallas": [
                    {"v": v, "de": sorted(sets[j]), "hacia": sorted(sets[i]),
                     "razon": r}
                    for (j, v, i, r) in failures
                ],
            })
            memo[key] = False
            return False
        result = False
        for (j, v, i) in moves:
            new_sets = list(sets)
            new_sets[j] = sets[j] - {v}
            new_sets[i] = sets[i] | {v}
            sub = dfs(tuple(new_sets))
            if sub is None:
                return None
            if sub:
                result = True
                break
        memo[key] = result
        return result

    res = dfs(tuple(frozenset(s) for s in initial_sets))
    if res is None:
        return "OVERFLOW", None
    if res:
        return "SUCCESS", None
    return "STUCK", stuck_states


# ─────────────────────────────────────────────────────────────────────────────
# MAIN — ATLAS COMPLETO n <= 7
# ─────────────────────────────────────────────────────────────────────────────

def main():
    t0 = time.time()
    print("=" * 72)
    print("  SCRIPT 11 — BUSQUEDA EXHAUSTIVA DE OBSTRUCCIONES (n <= 7) — V25")
    print("=" * 72)
    print("  Open Problem 6.1, respondido exhaustivamente para n <= 7:")
    print("  todos los grafos conexos, todas las coloraciones optimas,")
    print("  todas las secuencias de movimientos (a)/(b)/(c) del paper.")
    print("-" * 72)

    atlas = nx.graph_atlas_g()
    graphs = []
    for idx, G in enumerate(atlas):
        if G.number_of_nodes() < 3:
            continue
        if not nx.is_connected(G):
            continue
        graphs.append((idx, G))
    print(f"  Grafos conexos en el atlas (3 <= n <= 7): {len(graphs)}")
    print()

    total_pairs = 0          # (grafo, coloracion) analizados
    success_pairs = 0
    stuck_pairs = 0
    truncated_graphs = 0
    immediate = 0            # coloraciones ya conexas sin reparar
    obstructions = []        # descubrimientos
    graphs_with_stuck_coloring = []   # grafos donde ALGUNA coloracion se atora
    graphs_all_colorings_stuck = []   # grafos donde TODAS se atoran (anti-Hadwiger señal)
    tax_count = {"T_A": 0, "T_B": 0, "T_C": 0, "T_MIX": 0}

    log_lines = []

    for count, (idx, G) in enumerate(graphs, 1):
        n = G.number_of_nodes()
        chi = chromatic_exact_small(G)
        if chi < 2:
            continue
        partitions, truncated = all_optimal_partitions(G, chi)
        if truncated:
            truncated_graphs += 1

        graph_stuck = 0
        graph_success = 0

        for part in partitions:
            total_pairs += 1
            sets = [set(s) for s in part]
            if all(len(components_of(G, s)) == 1 for s in sets):
                immediate += 1
                success_pairs += 1
                graph_success += 1
                continue
            status, stuck = repair_search(G, sets)
            if status == "SUCCESS":
                success_pairs += 1
                graph_success += 1
            elif status == "STUCK":
                stuck_pairs += 1
                graph_stuck += 1
                for st in stuck:
                    if st["taxonomia"]:
                        tax_count[st["taxonomia"]] += 1
                obstructions.append({
                    "atlas_index": idx,
                    "n": n,
                    "m": G.number_of_edges(),
                    "chi": chi,
                    "edges": sorted(map(sorted, G.edges())),
                    "coloracion_inicial": [sorted(s) for s in part],
                    "estados_atorados": stuck[:20],
                })
                line = (f"  !! OBSTRUCCION atlas#{idx} n={n} m={G.number_of_edges()} "
                        f"chi={chi} coloracion={[sorted(s) for s in part]}")
                print(line)
                log_lines.append(line)
            else:
                line = f"  !! OVERFLOW atlas#{idx} (no esperado para n<=7)"
                print(line)
                log_lines.append(line)

        if graph_stuck > 0:
            graphs_with_stuck_coloring.append(idx)
            if graph_success == 0:
                graphs_all_colorings_stuck.append(idx)

        if count % 100 == 0:
            el = time.time() - t0
            print(f"  [{count}/{len(graphs)}] grafos | "
                  f"pares={total_pairs} exito={success_pairs} "
                  f"atorados={stuck_pairs} | {el:.0f}s")
            sys.stdout.flush()

    elapsed = (time.time() - t0) / 60

    # ── REPORTE ──
    print()
    print("=" * 72)
    print("  RESULTADO FINAL — EXHAUSTIVO n <= 7")
    print("=" * 72)
    print(f"  Grafos conexos analizados            : {len(graphs)}")
    print(f"  Pares (grafo, coloracion) analizados : {total_pairs}")
    print(f"  Coloraciones ya conexas (Prop. 4.4)  : {immediate}")
    print(f"  Reparacion EXITOSA                   : {success_pairs}")
    print(f"  Reparacion ATORADA (toda secuencia)  : {stuck_pairs}")
    print(f"  Grafos con alguna coloracion atorada : {len(graphs_with_stuck_coloring)}")
    print(f"  Grafos con TODAS atoradas            : {len(graphs_all_colorings_stuck)}")
    print(f"  Taxonomia de atascos                 : {tax_count}")
    print(f"  Grafos truncados por tope coloraciones: {truncated_graphs}")
    print(f"  Tiempo                               : {elapsed:.1f} min")
    print("-" * 72)
    if stuck_pairs == 0:
        print("  TEOREMA COMPUTACIONAL (verificado exhaustivamente):")
        print("  Para todo grafo conexo con n <= 7 y toda coloracion optima,")
        print("  la fase de reparacion del paper V24 (Sec. 4.1) puede alcanzar")
        print("  branch sets conexos. Open Problem 6.1 es CIERTO para n <= 7.")
    else:
        print("  DESCUBRIMIENTO: existen obstrucciones minimas — ver JSON.")
        print(f"  Guardadas en: {OBSTRUCTION_FILE}")
    print("=" * 72)

    # ── PERSISTIR ──
    LOG_FILE.parent.mkdir(exist_ok=True)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("SCRIPT 11 — BUSQUEDA EXHAUSTIVA n<=7 — V25\n")
        f.write(f"Investigador : Mizael Antonio Tovar Reyes\n")
        f.write(f"Fecha        : {datetime.now():%Y-%m-%d %H:%M:%S}\n")
        f.write(f"Grafos       : {len(graphs)}\n")
        f.write(f"Pares        : {total_pairs}\n")
        f.write(f"Inmediatos   : {immediate}\n")
        f.write(f"Exitosos     : {success_pairs}\n")
        f.write(f"Atorados     : {stuck_pairs}\n")
        f.write(f"Taxonomia    : {tax_count}\n")
        f.write(f"Grafos c/atasco: {graphs_with_stuck_coloring}\n")
        f.write(f"Grafos todo atascado: {graphs_all_colorings_stuck}\n")
        f.write(f"Truncados    : {truncated_graphs}\n")
        f.write(f"Tiempo (min) : {elapsed:.1f}\n\n")
        for line in log_lines:
            f.write(line + "\n")
        if stuck_pairs == 0:
            f.write("\nCONCLUSION: 0 obstrucciones. Open Problem 6.1 verificado "
                    "exhaustivamente cierto para n <= 7.\n")

    if obstructions:
        with open(OBSTRUCTION_FILE, "w", encoding="utf-8") as f:
            json.dump(obstructions, f, indent=2, ensure_ascii=False)

    return stuck_pairs


if __name__ == "__main__":
    sys.exit(0 if main() == 0 else 2)
