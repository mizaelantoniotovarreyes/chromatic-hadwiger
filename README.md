# A Patio Adjacency Lemma for Greedy Colorings — V24 (paper) / V25 (code)
### by Mizael Antonio Tovar Reyes — Ciudad Juárez, Chihuahua, México

---

## What This Is

This repository contains the computational verification and mathematical results
associated with the following paper:

> **"A Patio Adjacency Lemma for Greedy Colorings, with Computational Evidence
> Toward Branch-Set Connectivity"**
> — Mizael Antonio Tovar Reyes, Version 24, 2026
> DOI (V24): [10.5281/zenodo.20478975](https://doi.org/10.5281/zenodo.20478975)
> DOI (all versions): [10.5281/zenodo.19262568](https://doi.org/10.5281/zenodo.19262568)

The central proved result is:

> **Theorem 3.4 (Patio Adjacency Lemma):** Let G be a connected simple graph
> with an ordering attaining p(G), with expansion centers c₁,...,cₖ. For every
> pair of colors i < j, cⱼ has a neighbor in color class Aᵢ. Consequently,
> every pair of color classes is joined by a direct edge.

Built on the identity **χ(G) = 1 + p(G)** (Proposition 3.1 — essentially
folklore; the novelty is the constructive packaging via expansion centers).

**Hadwiger's conjecture for k ≥ 7 remains open. This repository does not
close it and does not claim to.**

---

## V25 Computational Findings (June 2026) — what is NEW

The V25 scripts (11–14) implement the repair phase **exactly as written in
the paper (§4.1, conditions (a)/(b)/(c) checked per move, sets always
disjoint)** and then study what move repertoire actually suffices. Three
findings, each reproducible from this repo:

### Finding 1 — The §4.1 repair phase is provably insufficient
Exhaustive search over **all 994 connected graphs with n ≤ 7** (networkx
Graph Atlas), **all optimal colorings** of each (5,425 graph–coloring pairs),
and **all possible move sequences** (memoized DFS; the potential Φ of
Lemma 4.3 bounds the depth):

| Outcome | Pairs |
|---|---|
| Repair succeeds (some sequence connects all sets) | 1,905 |
| Repair dead-ends under **every** sequence | 3,520 |
| Graphs where **every** optimal coloring dead-ends | 366 of 994 |

The **minimal counterexample is P₃** (path on 3 vertices): coloring
{0},{1,2} — the only repair candidate is the center, and moving it empties
its set (violates (b)). Stuck states classify into a taxonomy:
**T_A** (no candidate at all), **T_B** (all candidates are articulation
points of their donor — the paper's "articulation trap"), **T_C** (all
candidates would break pairwise adjacency — an obstruction **not named in
the paper**), and T_MIX. Counts on n ≤ 7: T_A=392, T_B=2,667, T_C=364,
T_MIX=1,231.

This answers the **constructive half of Open Problem 6.1 negatively**: an
adjacency-preserving connectivity move does **not** always exist. The
partition form of Open Problem 6.1 (does the partition *exist*?) is
untouched and remains equivalent to Hadwiger's conjecture.

### Finding 2 — The articulation trap is real (correcting paper §5.3)
The paper reported "no articulation traps in 344 graphs". That run used an
earlier construction with a set-overlap bug (branch sets were not kept
disjoint). With the faithful disjoint construction, **articulation traps
(T_B) occur already in Mycielski M₄ (n = 11)** and in **every Kneser graph
K(n,2), n = 5..10** tested. Section 5.3 of the paper should be corrected
in the next version.

### Finding 3 — The Flip Conjecture (new)
If the move set is enlarged to **arbitrary single-vertex transfers** that
only preserve (i) k non-empty sets and (ii) pairwise adjacency — the
"flip graph" of adjacent partitions — then a fully connected partition
**was reached in every single case tested**:

- **Exhaustive (n ≤ 7):** all 5,425 graph–coloring pairs reachable. 0 failures.
  (1,905 already reachable with paper moves; 470 more with relaxed donors;
  3,050 need general flips.)
- **Hard large graphs (heuristic + verified certificates):** 35/35 successes,
  including Mycielski M₇ (n=95, k=7), Kneser K(10,2) (n=45, k=8), random
  regular graphs, trees, grids, hypercube — each solved in 5–18 flips, with
  the full flip sequence saved and independently re-verified
  (`logs/certificados_flip_large.json`).

> **Flip Conjecture.** For every connected simple graph G with χ(G) = k and
> every optimal coloring, the flip graph of pairwise-adjacent k-partitions
> contains a path from the coloring partition to a partition whose classes
> are all connected.

The Flip Conjecture **implies Hadwiger's conjecture** (so it is at least as
hard); whether it is equivalent is open. Its value is the new, finite,
local object it offers: every counterexample to Hadwiger must contain a
flip-graph component with no connected-partition state — something that can
be hunted computationally.

---

## Key Results Table (honest status)

| Result | Status | Script |
|---|---|---|
| Proposition 3.1: χ(G) = 1 + p(G) | PROVED (short) + sanity-checked | matr_chromatic_identity |
| **Theorem 3.4: Patio Adjacency Lemma** ★ | **PROVED + verified, 130,000+ graphs, 0 failures** | matr_hadwiger_theorem |
| Adjacency half of branch-set construction | Verified (562 graphs) | matr_minor_certificate |
| Connectivity of branch sets | **NOT achieved in general** (12/84 in re-audit) | — |
| §4.1 repair phase sufficiency | **DISPROVED — minimal counterexample P₃** (V25) | matr_repair_exhaustive_small |
| Articulation trap exists? | **YES — Mycielski M₄, all Kneser K(n,2)** (V25; corrects §5.3) | matr_repair_hard_families |
| **Flip Conjecture** (new) | **Exhaustive n ≤ 7: 5,425/5,425 + 35/35 hard large graphs** | matr_repair_generalized_moves, matr_flip_conjecture_large |
| Open Problem 6.1 (partition form) | **OPEN — equivalent to Hadwiger, k ≥ 7** | — |

★ Main original contribution of the paper.
Note: `p(G) = χ(G) − 1` is a theorem, so V25 scripts obtain optimal
orderings deterministically (order any optimal coloring by classes) instead
of random search.

---

## Repository Structure

```
chromatic-hadwiger/
|
+-- scripts/
|   +-- core_utils.py                     Shared library (graphs, coloring, logging)
|   +-- matr_chromatic_identity.py        Proposition 3.1 sanity check
|   +-- matr_completeness_lemma.py        Lemma 3.3 (color-class adjacency)
|   +-- matr_hadwiger_theorem.py          Theorem 3.4 verification
|   +-- matr_exact_families.py            Exact graph families
|   +-- matr_branch_absorption.py         Absorption experiments
|   +-- matr_alternating_connector.py     Alternating connector (conditional)
|   +-- matr_minor_certificate.py         Adjacency half on 562 graphs
|   +-- matr_high_chi_solver.py           High-chi runs
|   +-- matr_final_verifier.py            Independent judge/verifier
|   +-- matr_false_negative_closer.py     V20 closed cases
|   +-- matr_full_verification.py         Verification harness
|   +-- analisis_articulacion.py          (V24; superseded — had set-overlap bug)
|   +-- matr_repair_exhaustive_small.py   V25: exhaustive obstruction search n<=7
|   +-- matr_repair_hard_families.py      V25: faithful repair on hard families
|   +-- matr_repair_generalized_moves.py  V25: flip graph, move levels N1/N2/N3
|   +-- matr_flip_conjecture_large.py     V25: Flip Conjecture on large graphs
|
+-- logs/                                 All runs (autosaved, reproducible seeds)
|   +-- obstrucciones_n7.json             V25: all minimal obstructions, n<=7
|   +-- certificados_flip_large.json      V25: verified flip certificates
|
+-- Conjecture/                           Paper versions and proofs
+-- visual/                               Interactive visualizations (INDEX.html)
+-- requirements.txt / LICENSE / README.md
```

---

## Installation & Reproducing

```bash
pip install -r requirements.txt
```

V25 findings (fast — minutes on a normal PC):

```bash
cd scripts
python matr_repair_exhaustive_small.py    # Finding 1: exhaustive n<=7
python matr_repair_hard_families.py       # Finding 2: traps in hard families
python matr_repair_generalized_moves.py   # Finding 3: flip levels N1/N2/N3
python matr_flip_conjecture_large.py      # Finding 3: large-graph certificates
```

Original verification suite (Patio Lemma etc.): scripts 1–10 as in V23,
see headers of each `matr_*.py`.

---

## Version history

| Version | Key change |
|---|---|
| V20 | 562 graphs verified, script 10 |
| V21 | **Patio Adjacency Lemma** (Theorem 3.4) — main result |
| V22 | Proof of Proposition 3.1 corrected |
| V23 | Honest title and framing, conditional lemmas |
| V24 | Published framing: adjacency half only; Open Problem 6.1 stated (DOI 10.5281/zenodo.20478975) |
| **V25 (code)** | **Repair phase disproved (minimal: P₃); trap taxonomy T_A/T_B/T_C; §5.3 corrected; Flip Conjecture with exhaustive n≤7 verification + 35/35 large certificates** |

---

## Author

**Mizael Antonio Tovar Reyes**
Independent researcher — Ciudad Juárez, Chihuahua, México — 2026

- Email: mizaelantoniotovarreyes@gmail.com
- GitHub: github.com/mizaelantoniotovarreyes

## License

Custom Research License: free for academic and personal use; commercial use
requires written permission. See `LICENSE`.

## Citation

```
Tovar Reyes, M. A. (2026). A Patio Adjacency Lemma for Greedy Colorings,
with Computational Evidence Toward Branch-Set Connectivity (Version 24).
Zenodo. https://doi.org/10.5281/zenodo.20478975
```

GitHub: https://github.com/mizaelantoniotovarreyes/chromatic-hadwiger
