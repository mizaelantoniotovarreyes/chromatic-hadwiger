"""
SCRIPT 13 — QUE MOVIMIENTOS SI BASTAN? (FLIP GRAPH DE PARTICIONES) — V25
=========================================================================
Autor    : Mizael Antonio Tovar Reyes
Ubicacion: Ciudad Juarez, Chihuahua, Mexico

CONTEXTO (resultado del Script 11):
  La fase de reparacion del paper V24 Sec. 4.1 es INSUFICIENTE:
  contraejemplo minimo P_3 (n=3), y 366 grafos con n<=7 donde TODA
  coloracion optima se atora. Las particiones objetivo SI existen
  (Hadwiger probado para k<=6), pero los movimientos no las alcanzan.

PREGUNTA NUEVA (este script):
  Cual es el repertorio minimo de movimientos que SI basta?
  Se estudia el FLIP GRAPH: estados = particiones de V en k sets
  no vacios PAIRWISE ADYACENTES; aristas = transferir UN vertice
  preservando la adyacencia. Pregunta: desde la particion de la
  coloracion optima, es alcanzable una particion con todos los
  sets conexos?

NIVELES DE MOVIMIENTO (cada uno contiene al anterior):
  N1 (paper)    : destino desconectado, v toca >=2 componentes (a),
                  donante queda no vacio y conexo (b), adyacencia (c)
  N2 (relajado) : igual que N1 pero el donante puede quedar DESCONECTADO
                  (solo se exige no vacio); (a) y (c) se mantienen
  N3 (flip total): cualquier transferencia de un vertice; solo se exige
                  donante no vacio y adyacencia global (c)

  En N2/N3 el potencial Phi ya no decrece -> la busqueda es
  alcanzabilidad con memoizacion sobre el espacio de estados (finito).

RESULTADOS POSIBLES:
  - N3 basta para TODO par (grafo, coloracion) con n<=7
    -> CONJETURA NUEVA verificable: "el flip graph de particiones
       adyacentes siempre conecta la coloracion con una particion
       conexa" — una reformulacion local/discreta de Hadwiger.
  - N3 NO basta en algun par -> obstruccion profunda nueva (el flip
    graph tiene una componente sin estados conexos). Descubrimiento.

Investigador : Mizael Antonio Tovar Reyes
Version      : V25 — Junio 2026
"""

import sys
import json
import time
from pathlib import Path
from collections import deque
from datetime import datetime

import networkx as nx

sys.path.insert(0, str(Path(__file__).resolve().parent))
from matr_repair_exhaustive_small import (
    components_of, has_edge_between, chromatic_exact_small,
    all_optimal_partitions,
)

BASE_DIR = Path(__file__).resolve().parent
LOG_FILE = BASE_DIR.parent / "logs" / "log_matr_repair_generalized.txt"
DEEP_FILE = BASE_DIR.parent / "logs" / "obstrucciones_profundas_n7.json"

MAX_STATES = 3_000_000


def moves_at_level(G, sets, level):
    """Movimientos legales (j, v, i) segun el nivel."""
    k = len(sets)
    comps = [components_of(G, s) for s in sets]
    out = []
    for j in range(k):
        if len(sets[j]) < 2:
            continue  # donante quedaria vacio
        for v in sets[j]:
            nbrs = set(G.neighbors(v))
            remaining = sets[j] - {v}
            if level <= 2:
                donor_ok = (len(components_of(G, remaining)) == 1
                            if level == 1 else True)
            else:
                donor_ok = True
            if not donor_ok:
                continue
            for i in range(k):
                if i == j:
                    continue
                if level <= 2:
                    # destino desconectado y v toca >= 2 componentes (a)
                    if len(comps[i]) <= 1:
                        continue
                    touched = sum(1 for c in comps[i] if nbrs & c)
                    if touched < 2:
                        continue
                # condicion (c): solo pares con el donante pueden perder arista
                new_i = sets[i] | {v}
                ok = True
                for m in range(k):
                    if m == j:
                        continue
                    other = new_i if m == i else sets[m]
                    if not has_edge_between(G, remaining, other):
                        ok = False
                        break
                if ok:
                    out.append((j, v, i))
    return out


def reachable_connected(G, initial_sets, level):
    """
    Alcanzabilidad: existe un estado con todos los sets conexos
    alcanzable desde initial_sets con movimientos del nivel dado?
    BFS con memoizacion (espacio de estados finito).
    Devuelve True / False / None (overflow).
    """
    def all_connected(sets):
        return all(len(components_of(G, s)) == 1 for s in sets)

    start = tuple(frozenset(s) for s in initial_sets)
    if all_connected(start):
        return True
    seen = {frozenset(start)}
    queue = deque([start])
    while queue:
        if len(seen) > MAX_STATES:
            return None
        sets = queue.popleft()
        for (j, v, i) in moves_at_level(G, sets, level):
            new_sets = list(sets)
            new_sets[j] = sets[j] - {v}
            new_sets[i] = sets[i] | {v}
            new_t = tuple(new_sets)
            key = frozenset(new_t)
            if key in seen:
                continue
            if all_connected(new_t):
                return True
            seen.add(key)
            queue.append(new_t)
    return False


def main():
    t0 = time.time()
    print("=" * 76)
    print("  SCRIPT 13 — FLIP GRAPH: QUE MOVIMIENTOS BASTAN? (n <= 7) — V25")
    print("=" * 76)

    atlas = nx.graph_atlas_g()
    graphs = [(idx, G) for idx, G in enumerate(atlas)
              if G.number_of_nodes() >= 3 and nx.is_connected(G)]
    print(f"  Grafos conexos del atlas: {len(graphs)}")
    print()

    stats = {1: 0, 2: 0, 3: 0, "imposible": 0, "overflow": 0}
    total = 0
    deep_obstructions = []
    log_lines = []

    for count, (idx, G) in enumerate(graphs, 1):
        chi = chromatic_exact_small(G)
        if chi < 2:
            continue
        partitions, _ = all_optimal_partitions(G, chi)
        for part in partitions:
            total += 1
            sets = [set(s) for s in part]
            solved = None
            for level in (1, 2, 3):
                r = reachable_connected(G, sets, level)
                if r is None:
                    stats["overflow"] += 1
                    solved = "overflow"
                    break
                if r:
                    stats[level] += 1
                    solved = level
                    break
            if solved is None:
                stats["imposible"] += 1
                deep_obstructions.append({
                    "atlas_index": idx,
                    "n": G.number_of_nodes(),
                    "m": G.number_of_edges(),
                    "chi": chi,
                    "edges": sorted(map(sorted, G.edges())),
                    "coloracion": [sorted(s) for s in part],
                })
                line = (f"  !! OBSTRUCCION PROFUNDA (ni N3) atlas#{idx} "
                        f"n={G.number_of_nodes()} chi={chi} "
                        f"col={[sorted(s) for s in part]}")
                print(line)
                log_lines.append(line)

        if count % 100 == 0:
            el = time.time() - t0
            print(f"  [{count}/{len(graphs)}] pares={total} "
                  f"N1={stats[1]} N2={stats[2]} N3={stats[3]} "
                  f"imposibles={stats['imposible']} | {el:.0f}s")
            sys.stdout.flush()

    elapsed = (time.time() - t0) / 60
    print()
    print("=" * 76)
    print("  RESULTADO FINAL — NIVEL MINIMO SUFICIENTE (exhaustivo n <= 7)")
    print("=" * 76)
    print(f"  Pares (grafo, coloracion)      : {total}")
    print(f"  Basta N1 (movimientos del paper): {stats[1]}")
    print(f"  Necesita N2 (donante fragmentable): {stats[2]}")
    print(f"  Necesita N3 (flip total)        : {stats[3]}")
    print(f"  NI N3 ALCANZA (obstr. profunda) : {stats['imposible']}")
    print(f"  Overflow                        : {stats['overflow']}")
    print(f"  Tiempo                          : {elapsed:.1f} min")
    print("-" * 76)
    if stats["imposible"] == 0 and stats["overflow"] == 0:
        print("  HALLAZGO: con el flip total (N3) TODO par alcanza particion")
        print("  conexa. CONJETURA NUEVA (verificada n<=7): en el flip graph")
        print("  de particiones pairwise-adyacentes, desde toda coloracion")
        print("  optima es alcanzable una particion con sets conexos.")
        print("  Esta conjetura implica Hadwiger; su forma local es nueva.")
    elif stats["imposible"] > 0:
        print("  DESCUBRIMIENTO: hay pares inalcanzables incluso con flip")
        print(f"  total — ver {DEEP_FILE}")
    print("=" * 76)

    LOG_FILE.parent.mkdir(exist_ok=True)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("SCRIPT 13 — FLIP GRAPH N1/N2/N3 — V25\n")
        f.write(f"Investigador : Mizael Antonio Tovar Reyes\n")
        f.write(f"Fecha        : {datetime.now():%Y-%m-%d %H:%M:%S}\n\n")
        f.write(f"Pares: {total}\n")
        f.write(f"N1 basta: {stats[1]}\nN2 necesario: {stats[2]}\n")
        f.write(f"N3 necesario: {stats[3]}\n")
        f.write(f"Imposibles: {stats['imposible']}\n")
        f.write(f"Overflow: {stats['overflow']}\n")
        f.write(f"Tiempo (min): {elapsed:.1f}\n\n")
        for line in log_lines:
            f.write(line + "\n")

    if deep_obstructions:
        with open(DEEP_FILE, "w", encoding="utf-8") as f:
            json.dump(deep_obstructions, f, indent=2, ensure_ascii=False)

    return stats["imposible"]


if __name__ == "__main__":
    main()
