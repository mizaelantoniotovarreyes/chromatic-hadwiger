"""
ANALISIS: ¿Cuándo todos los vecinos son puntos de articulación? — V25 (FIX)
Mizael Antonio Tovar Reyes — Ciudad Juárez, 2026
CON PROGRESO EN VIVO para PowerShell

BUG CORREGIDO EN V25 (2026-06-12):
  La version anterior "reparaba" clases desconectadas agregando los
  vertices de un shortest_path SIN quitarlos de su set original ->
  los branch sets quedaban TRASLAPADOS (no disjuntos). El resultado
  "0 trampas en 344 grafos" reportado en el paper V24 Sec. 5.3 era un
  artefacto de ese bug y queda RETIRADO.

  FIX: los branch sets son ahora exactamente las clases de color
  (la Fase 1 fiel del paper, disjunta por construccion), y la trampa
  se analiza sobre ese estado. Con la construccion fiel, las trampas
  SI ocurren (Mycielski M4, todos los Kneser K(n,2) n=5..10; ver
  matr_repair_hard_families.py y matr_repair_exhaustive_small.py,
  que ademas exploran todas las secuencias de movimientos).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import networkx as nx

try:
    from core_utils import chromatic_exact, get_optimal_coloring, get_all_graphs
except ImportError:
    print("ERROR: Necesita core_utils.py en el mismo directorio.")
    sys.exit(1)


def build_branch_sets_fase1(G, coloring, chi):
    """
    FASE 1 FIEL al paper (V25): B_i = A_i, las clases de color puras.
    Particion disjunta por construccion. (La version anterior agregaba
    vertices de shortest_path sin quitarlos de su set original,
    rompiendo la disyuncion — corregido.)
    """
    classes = {}
    for v, c in coloring.items():
        classes.setdefault(c, set()).add(v)
    colors = sorted(classes.keys())
    branch_sets = {c: set(classes[c]) for c in colors}
    return branch_sets, colors


def analyze_articulation_trap(G, branch_sets, colors):
    node_to_bs = {}
    for c, bs in branch_sets.items():
        for v in bs:
            node_to_bs[v] = c

    traps = []

    for ci in colors:
        subg = G.subgraph(branch_sets[ci])
        if nx.is_connected(subg):
            continue

        all_frontier = []
        for v in branch_sets[ci]:
            for nb in G.neighbors(v):
                cj = node_to_bs.get(nb)
                if cj and cj != ci:
                    remaining = branch_sets[cj] - {nb}
                    if not remaining:
                        continue
                    is_articulation = not nx.is_connected(G.subgraph(remaining))
                    all_frontier.append({
                        "nb": nb,
                        "donor_group": cj,
                        "donor_size": len(branch_sets[cj]),
                        "is_articulation": is_articulation,
                    })

        if not all_frontier:
            traps.append({"group": ci, "reason": "sin vecinos frontera", "frontier": []})
            continue

        robable = [f for f in all_frontier if not f["is_articulation"]]
        articulations = [f for f in all_frontier if f["is_articulation"]]

        if not robable:
            traps.append({
                "group": ci,
                "reason": "TODOS los vecinos son puntos de articulacion",
                "frontier": all_frontier,
                "donor_sizes": [f["donor_size"] for f in articulations]
            })

    return traps


def main():
    print("=" * 60)
    print("  ANALISIS: Trampa de puntos de articulacion?")
    print("=" * 60)
    print("  Cargando grafos...")
    sys.stdout.flush()

    graphs = get_all_graphs(num_random=300, random_seed=2026)
    graphs = [(G, n, f) for G, n, f in graphs if nx.is_connected(G)]
    print(f"  Total grafos cargados: {len(graphs)}")
    print("  Procesando...\n")
    sys.stdout.flush()

    total = 0
    traps_found = 0
    disconnected_groups = 0

    for i, (G, name, familia) in enumerate(graphs):
        n = G.number_of_nodes()
        chi = chromatic_exact(G, max_k=15 if n <= 20 else 10)
        if chi is None or chi < 3:
            continue
        coloring = get_optimal_coloring(G, chi)
        if coloring is None:
            continue

        branch_sets, colors = build_branch_sets_fase1(G, coloring, chi)
        total += 1

        for c in colors:
            if not nx.is_connected(G.subgraph(branch_sets[c])):
                disconnected_groups += 1

        traps = analyze_articulation_trap(G, branch_sets, colors)

        if traps:
            traps_found += 1
            for trap in traps:
                print(f"  TRAMPA en [{familia}] {name}  chi={chi}")
                print(f"     Grupo {trap['group']} desconectado")
                print(f"     Razon: {trap['reason']}")
                if trap.get("donor_sizes"):
                    print(f"     Tamanos donantes: {trap['donor_sizes']}")
                sys.stdout.flush()

        # Progreso cada 10 grafos
        if total % 10 == 0:
            print(f"  [{total}/{len(graphs)}] procesados... trampas: {traps_found}")
            sys.stdout.flush()

    print()
    print("=" * 60)
    print(f"  Grafos analizados        : {total}")
    print(f"  Grupos desconectados     : {disconnected_groups}")
    print(f"  Trampas encontradas      : {traps_found}")
    print()
    if traps_found == 0:
        print("  RESULTADO: ninguna trampa en ESTA muestra.")
        print()
        print("  OJO (V25): las trampas SI existen — ocurren en Mycielski M4,")
        print("  en todos los Kneser K(n,2) n=5..10 y en regulares ralos")
        print("  (ver matr_repair_hard_families.py). Cero aqui solo significa")
        print("  que esta muestra aleatoria no las contiene.")
    else:
        print(f"  Se encontraron {traps_found} trampas — consistente con V25")
        print("  (la trampa de articulacion es real; ver Sec. 6 del paper).")
    print("=" * 60)
    sys.stdout.flush()


if __name__ == "__main__":
    main()
