# CHANGELOG — Version 25 (current)
## A Patio Adjacency Lemma for Greedy Colorings, with Computational Evidence Toward Branch-Set Connectivity
### Mizael Antonio Tovar Reyes — Ciudad Juárez, Chihuahua, México

DOI (this version): https://doi.org/10.5281/zenodo.20736262
DOI (all versions): https://doi.org/10.5281/zenodo.19262568

> **One paper = one idea.** V25 is the Patio Adjacency Lemma **only**. The separate
> "Flip Conjecture" exploration lives in its own repository
> (github.com/mizantorey/flip-conjecture) and is **not** part of this paper.

---

## V24 → V25 Summary

V25 is a **correctness and honesty pass** over the published V24. No claim was strengthened;
two were **corrected** against the author's own further computation.

---

## Corrections (the important ones)

### 1. §5.3 — the "articulation trap" count was wrong in V24
V24 reported *"0 articulation traps in 344 graphs."* That run used a construction with a
set-overlap bug (branch sets were not kept disjoint). Re-running the **same 344-graph
protocol with disjoint sets finds 196 traps** — and the trap already appears in
Mycielski M₄ (n = 11) and in **every** Kneser graph K(n,2), n = 5..10. **§5.3 is corrected.**
Verification: `scripts/analisis_articulacion.py`, `logs/log_analisis_articulacion_v25.txt`.

### 2. χ(K(10,2)) = 8 (Lovász 1978) — Table 1 corrected
The chromatic number of the Kneser graph K(10,2) is **8**, separated out and attributed to
Lovász (1978). Table 1 corrected.

### 3. Table 1 column "Cert." → "Adjacency"
Relabeled so the caption makes explicit that what is certified is the **adjacency half**,
not full Kₖ-minor certificates.

### 4. k = 5 attribution fixed (§7)
Now attributed to the Four-Color Theorem (Appel–Haken 1977) and Robertson–Seymour–Thomas
(1993); the incorrect "Wagner 1964" citation was removed.

### 5. Wording and references
- "80 years" → **"83 years"** (Hadwiger 1943).
- Kₖ notation unified throughout.
- References: **added** Lovász (1978), Appel–Haken (1977); **removed** Brooks (1941),
  Zhu (2001), Wagner (1964) — unused or incorrect.
- Acknowledgments: added an explicit, honest disclosure of AI coding-tool assistance.

### 6. Repository hygiene
- GitHub username corrected to **mizantorey** throughout.
- The alternating connector is stated as a **sufficient condition**, not unconditional,
  consistent with Open Problem 6.1.
- The visual suite was made version-neutral (atemporal); a "Where the Proof Stands"
  honest-status page replaced the older "proof chain."

---

## What is UNCHANGED (and remains the whole point)

- **Patio Adjacency Lemma (Theorem 3.4)** — PROVED, verified on 130,000+ graphs, 0 failures.
- **χ(G) = 1 + p(G)** (Proposition 3.1).
- **Open Problem 6.1** (branch-set connectivity) — OPEN, equivalent to Hadwiger for k ≥ 7.
- **No claim is made about Hadwiger's conjecture for k ≥ 7.**

---

## Files

| File | Description |
|---|---|
| `conjecture/Patio-Adjacency-Lemma_V25.docx` | **Current paper (V25)** |
| `conjecture/CHANGELOG_V25.md` | This file |
| `conjecture/CHANGELOG_V24.md` · `CHANGELOG_V23.md` · `CHANGELOG_V20.md` | Version history |
| `conjecture/case3b_anti_destruction_proof.md` | Conditional monotonicity lemma (see its V25 note) |
| `conjecture/Explained Simply.txt` | Plain-language overview (current) |

---

*Mizael Antonio Tovar Reyes — Ciudad Juárez, Chihuahua, México*
