# Scientific guidelines

These rules protect the project's credibility. CI enforces the ones that can be checked automatically.

## 1. Traceability
Every finding (gene function, pathway step, comparison) links to a PMID or DOI.
- Schema: `evidence` rejects rows with neither.
- Code: `PathwayGraph.add_step` rejects edges without a reference; `classify_evidence` ignores studies without one.

## 2. Evidence classes, not probabilities

| Class | Meaning |
|---|---|
| strong | 2+ distinct references, at least one experimental |
| moderate | 1 experimental reference, or 2+ computational references |
| limited | mostly predictions, or missing information |

These describe how well-supported a claim is. They do **not** estimate whether engineering would succeed.

## 3. Five assessment dimensions
Sequence relationship, functional evidence, pathway completeness, expression compatibility, genomic context. Each has categorical values (see `app/genebridge.py`) including an explicit "unknown / unavailable" so gaps stay visible.

## 4. Forbidden claims
- Percentages of "compatibility", "success" or "efficacy" (CI check `science-guardrails`).
- That a plant "has been engineered" or a medicine "works".
- That predicted functions are experimentally proven.

## 5. Required language
Use "hypothetical", "computational scenario", "candidate", "published evidence suggests". Always show limitations next to results.

## 6. Biology reminders
- We study individual genes, never whole chromosomes. The two species have different chromosome numbers (9 vs 13).
- Knocking out or editing a host gene is a different operation from inserting a large donor sequence, which is still technically hard in plants.
- A donor enzyme is only useful if the host supplies its precursors and downstream machinery.
- Therapeutic efficacy needs separate experimental evidence.

## 7. Candidate gene list (initial)
PAL, CHS, 4CL, CHI, CYP82D (flavonoid side) and the KPS family (SbarKPS1, SbarKPS2, SbaiKPS1) for the diterpenoid case study. Verify each gene's function against its publication before it enters the database.
