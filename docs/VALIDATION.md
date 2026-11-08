# How we checked it

What was tested, what the numbers were, and what is **not** validated. The results come from the real genomes
(see [SOURCES.md](SOURCES.md)) and can be reproduced with the commands below.

## 1. Method in one paragraph

For a donor gene, `blastp` (BLAST+ 2.17) searches the host proteome. We keep the best hit, then search that
hit back against the donor proteome (a reciprocal best hit, RBH). A match is labelled:

| Label | Rule (`backend/app/comparison.py`) |
|---|---|
| related | identity at least 40% **and** E-value at most 1e-10 |
| weakly related | E-value at most 1e-3 |
| no clear match | otherwise |

The label describes **sequence similarity only**. It never says a gene would work in the host. Evidence level
(strong, moderate, limited) is a separate, rule-based assessment of five dimensions, shown as a class and never
as a score.

## 2. Check A: a known answer (positive control)

The two KPS proteins deposited with the paper (Qiu et al. 2023, PMID 37395679) were searched against both
proteomes of our annotation.

| Query (NCBI) | Best donor gene | Identity | Reading |
|---|---|---|---|
| WJZ49120.1 (SbarKPS2) | `Sbar9A9T61` | 100% | The same protein: the annotation contains the paper's gene |
| WJZ49119.1 (SbarKPS1) | `Sbar9A10T43` | 94.8% | Best match, not identical (853 aa in our model, 809 in the paper) |

Sanity check on the biology: `Sbar9A9T61` (979,922 to 985,718) and `Sbar9A10T43` (1,017,746 to 1,024,094) sit on
the same sequence and strand, 38 kb apart, which fits the tandem gene pair the paper describes.

## 3. Check B: is the best hit clearly the best? (specificity)

Best and runner-up host hits for the same two proteins:

| Query | Best host hit | Identity | Runner-up | Identity | Gap |
|---|---|---|---|---|---|
| SbarKPS1 (WJZ49119.1) | `Sbai8C203T0` | 84.2% | `Sbai8A89T185` | 56.5% | 27.7 points |
| SbarKPS2 (WJZ49120.1) | `Sbai8C203T0` | 88.5% | `Sbai8A89T185` | 57.2% | 31.3 points |

Bit scores tell the same story (1249 against 862, and 1312 against 863). The same host gene is the best hit for
both donor genes, and the match is clear, not one of a crowd. In the app, `Sbar9A9T61` and `Sbai8C203T0` are also
a mutual best match.

## 4. Check C: what does "related" really mean? (an honest limit)

We searched 300 random donor genes (at least 100 aa, excluding the two KPS genes, random seed 7) against the host
proteome and applied our thresholds:

| Label | Genes | Share |
|---|---|---|
| related | 258 | 86% |
| weakly related | 30 | 10% |
| no clear match | 12 | 4% |

The median best-hit identity was 81.6%. **Because both plants belong to the same genus, most genes have a close
relative, so "related" alone does not single out a gene.** What does carry information is the mutual best match
(RBH) and the gap between the best and the second-best hit, as in Check B. The app shows the RBH flag; the
margin is currently only in this document.

## 5. Software checks

| Check | Result (latest CI run on `dev`) |
|---|---|
| Backend tests | 221 passed, 98.3% line coverage (gate: 85%) |
| Frontend tests | 74 passed |
| Database schema | Applied on a real Postgres with pgvector, then re-applied from scratch |
| Scientific guardrails | CI fails if code or UI copy contains a numeric compatibility claim, "has been engineered", "proven effective" or "cures" |
| Dependency and secret scans | pip-audit and gitleaks |

## 6. Handling uncertainty

- Every evidence class lists what is **missing** (pathway, expression, context, function) and what **conflicts**.
- Unknown is a valid answer everywhere; nothing is filled in. Reports state "hypothetical" and "computational".
- Two of the three KPS gene mappings are inferences from sequence similarity. They are labelled "best match",
  not "proven identical". The paper's own gene-ID table would confirm them.
- An optional AI explanation is written only from facts the app computed, is labelled as AI-written, and never
  sets an evidence level.

## 7. What is not validated

- No benchmark set of known orthologs, so we report no precision or recall.
- No expression data (RNA-seq), so expression is "unavailable" in every scenario.
- SbaiKPS1 can only be found by similarity: no *S. baicalensis* sequence is linked to the paper.
- Only one gene family (KPS) and one species pair were examined.
- The genome files hold many small unplaced sequences (80 and 297 hidden on the map), so this is not a
  chromosome-level assembly in every respect.

## 8. Reproduce Checks B and C

```bash
# protein sets and the two paper proteins are described in docs/SOURCES.md
makeblastdb -in host_genes.faa  -dbtype prot -out host
makeblastdb -in donor_genes.faa -dbtype prot -out donor

# Check B: best and runner-up hits
blastp -query WJZ49119.1.fa -db host -outfmt "6 sseqid pident length evalue bitscore" -max_target_seqs 4
blastp -query WJZ49120.1.fa -db host -outfmt "6 sseqid pident length evalue bitscore" -max_target_seqs 4

# Check C: 300 random donor proteins against the host, then apply the thresholds in section 1
blastp -query random300.fa -db host -outfmt "6 qseqid sseqid pident evalue bitscore" -evalue 1e-3 -max_target_seqs 5
```

## 9. Next steps that would strengthen it

1. Show the best-versus-runner-up margin in the Compare table, next to the mutual-best-match flag.
2. Build a small benchmark of published orthologs between the two species and report precision and recall.
3. Add RNA-seq expression for the KPS genes so the expression dimension can be assessed.
