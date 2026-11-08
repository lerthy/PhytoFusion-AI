# Devpost project page (copy and paste)

Each heading below matches a field on the Devpost form. Text in this file only states what the prototype does today. The slide deck `PhytoFusion-AI-pitch.pptx` follows the same order.

## Project title

PhytoFusion AI

## Selected challenge track

EthnoHack, Track 2: Genetic Trait Integration (hypothetical gene transfer between two medicinal plants, studied computationally).

## Short project description

PhytoFusion AI compares the genomes of two related medicinal plants and helps researchers reason, on paper, about a hypothetical CRISPR gene transfer: what the published evidence supports, and what is still unknown. Nothing is edited or built, and every finding is traced to a PMID or DOI.

## Problem statement

Medicinal plants make valuable compounds through genes spread across large, differently organised genomes. A researcher who asks "could a gene from one plant add a missing step in another?" has to piece together genomes, papers and pathways by hand, with no simple way to see how well the evidence supports the idea or what is still missing.

Both plants are used in traditional Chinese medicine (*S. baicalensis*: Zhao et al. 2019, PMID 31236960; *S. barbata*, also used in Korean medicine: Wang et al. 2020, PMID 31577937). Traditional use is a reason to study them, not proof that they work.

Our case study: *Scutellaria baicalensis* (host, known for flavonoids such as baicalin, baicalein and wogonin) and *Scutellaria barbata* (donor, known for clerodane diterpenoids). The two plants have different numbers of chromosomes (2n = 18 and 2n = 26) and different gene sets (30,313 and 34,909 genes in the annotations we use), so names and positions do not line up and compatibility has to be checked gene by gene. The question: could a KPS (clerodane diterpene synthase) gene from the donor, in theory, add early diterpenoid steps in the host?

## Solution and approach

A web platform made of five connected engines:

1. **Scientific data ingestion:** loads genome annotations and protein sequences (GFF3 and FASTA) and publications into Supabase Postgres.
2. **Comparative genomics:** BLAST+ `blastp` of donor candidate genes against the host proteome, followed by a reciprocal best-hit check. Gene positions are shown on chromosome maps and a 3D helix view. A "find a gene by sequence" search takes a protein sequence or an NCBI accession and lists the matching genes (computed by BLAST, not AI).
3. **Pathway intelligence:** a curated pathway graph where every edge carries a source and an evidence level.
4. **GeneBridge:** a categorical assessment of sequence, function, pathway, expression and context, with an evidence class (strong, moderate or limited). It never produces a score or probability, and it says "unknown" when evidence is missing.
5. **CRISPR scenario simulator:** two hypothetical modes (host gene modification and donor integration) that produce a report restating only facts supplied by the other engines, with explicit limits.

**Where AI is used:** gene matching and the evidence classes are deterministic (BLAST and written rules), so they are explainable and repeatable. A large language model (Groq-hosted open model by default, or Claude through the Anthropic API) is used only to write an optional plain-language explanation of results the app has already computed. It is told to restate only those facts, the text is labelled as AI-written, and it never decides an evidence level.

Design rules: no invented biology, no success predictions, every finding cited, and "hypothetical" and "computational" in the wording. CI fails the build if the code introduces numeric compatibility scores or engineering claims.

## Technologies used

- **Frontend:** React 18, TypeScript 5, Vite 5, Cytoscape (pathway graph), three.js (3D genome view), Vitest
- **Backend:** Python 3.12, FastAPI, pydantic, pandas, networkx, httpx
- **Bioinformatics:** BLAST+ 2.17 (`blastp`)
- **AI:** a language model behind a small provider switch (Groq with an open model by default; Claude through the Anthropic API is supported) for optional plain-language explanations of computed results, grounded only in the facts supplied
- **Data:** Supabase (Postgres with pgvector, row-level security, private file storage), versioned SQL migrations
- **Quality and delivery:** pytest with an 85% coverage gate, ruff, schema tests on real Postgres, Docker, GitHub Actions CI/CD (seven checks and one gate), security scans (pip-audit, gitleaks)
- **Hosting:** Netlify (frontend), Render (backend in Docker), Supabase (data)
- **Planned:** AWS (S3 and CloudFront, ECS Fargate behind an Application Load Balancer, Aurora PostgreSQL with pgvector, Secrets Manager). The architecture diagram is generated as code with AWS Diagram-as-Code: `docs/architecture/aws-target.yaml`

## Data sources

All public. Full links and the matching method are in `docs/SOURCES.md`.

- **Genomes:** Genome Warehouse GWHAOTO00000000 (*S. baicalensis*, 30,313 genes) and GWHAOTP00000000 (*S. barbata*, 34,909 genes). Comparative Genome Analysis of *Scutellaria baicalensis* and *Scutellaria barbata*, Genomics, Proteomics & Bioinformatics 2020 (PMC7801248).
- **Key paper:** Qiu T et al., *Tandem duplication and sub-functionalization of clerodane diterpene synthase originate the blooming of clerodane diterpenoids in Scutellaria barbata*, The Plant Journal 2023. PMID 37395679, doi:10.1111/tpj.16377.
- **Traditional use:** two reviews checked against their PubMed abstracts: Zhao T et al., J Pharm Pharmacol 2019 (PMID 31236960, doi:10.1111/jphp.13129) and Wang L et al., J Ethnopharmacol 2020 (PMID 31577937, doi:10.1016/j.jep.2019.112260).
- **Protein sequences:** NCBI Protein WJZ49119.1 (SbarKPS1) and WJZ49120.1 (SbarKPS2), deposited with the paper.

## Results and prototype demonstration

**Live prototype:** https://photofusionai.netlify.app (the backend sleeps when idle, so the first request can take up to a minute).

What the working prototype shows:

- **Genomes:** both genomes load from the database, with chromosome maps drawn to scale (9 and 13 main sequences) and a 3D view.
- **Gene matching:** BLAST of the paper's KPS protein sequences against both proteomes gave:

| Paper's gene | Gene in our annotation | Identity | Confidence |
|---|---|---|---|
| SbarKPS2 | `Sbar9A9T61` | 100% | Same protein |
| SbarKPS1 | `Sbar9A10T43` | 94.8% | Best match, not identical |
| SbaiKPS1 | `Sbai8C203T0` | 84 to 89% | Best match only |

- **Checks that fit the biology:** the two donor genes lie 38 kb apart on the same sequence and strand (a tandem pair), and `Sbar9A9T61` and `Sbai8C203T0` are each other's best match in the app's reciprocal check (89%).
- **Report:** a saved scenario shows the donor gene on its chromosome, a hypothetical arrow to an open host slot ("insertion site: not chosen"), a moderate evidence level (one experimental study), what we don't know, and the limits.

**How we checked it** (full write-up: `docs/VALIDATION.md`): the paper's own protein finds its gene at 100% identity; the best host hit for both KPS proteins is `Sbai8C203T0` at 84% and 89%, against a runner-up near 57%; and the two donor genes lie 38 kb apart as a tandem pair should. We also report an honest limit: 86% of 300 random donor genes would be labelled "related" too, because the plants share a genus, so the label alone is not the signal. The mutual best match and the gap to the runner-up are. Backend tests: 248 passing at 98% coverage; frontend: 74 passing.

**Honest limits:** two of the three gene matches are inferences from sequence similarity, so we call them best matches. The paper's own gene ID table would confirm them. No genome is edited, no engineered plant exists, and nothing here says how well a compound would work as a medicine.

## Team members

- **Edina Suma:** licensed Pharmacy Technician and Bachelor of Pharmacy student, Faculty of Medicine, University of Prishtina. Led the science.
- **Lerdi Salihi:** DevOps Engineer. Built the pipelines, tests, deployment and the app.

## Impact and future development

**Potential real-world relevance:**
- Helps researchers screen candidate genes on paper before costly laboratory work.
- Every finding traces to a PMID or DOI, so each assessment can be audited.
- Shows what is unknown, not only what is known, so effort goes where it counts.
- The same method can compare other plant pairs that have published genomes.

**Scaling:** the method works for any plant pair with published genomes. BLAST runs on candidate genes only, so whole-proteome comparisons would move to batch jobs; the AWS plan (`docs/STACK.md`) covers hosting.

**Next steps:** build a small benchmark of known orthologs and report precision and recall; add gene expression data and more pathways (such as the full flavonoid route); literature retrieval with embeddings (the database already supports it); sign-in and rate limits before opening the API publicly; move to AWS as planned; test the most promising hypotheses with laboratory partners.

---

## Slide deck (maximum 10 slides)

Submit **`PhytoFusion-AI-submission-10-slides.pptx`**. The longer `PhytoFusion-AI-pitch.pptx` (22 slides) stays as a
backup for questions: it adds the tech stack, delivery pipeline, AWS plan, team and documentation slides.

| # | Slide | Covers |
|---|---|---|
| 1 | Title | |
| 2 | The problem | Problem |
| 3 | Two skullcaps, two chemistries | Problem, relevance (traditional use, sourced) |
| 4 | Our question: the KPS gene family | Problem |
| 5 | Five connected engines | Methodology |
| 6 | GeneBridge AI explains why, with evidence | Methodology |
| 7 | From genomes to a report you can trace | Demonstration |
| 8 | What the prototype found | Results |
| 9 | How we checked it | Results and validation |
| 10 | Why it matters, and what comes next | Impact, credits, demo link |

## Checklist against the challenge requirements

| Requirement | Where it is covered |
|---|---|
| A clearly defined problem | "Problem statement" above; deck slides 3, 4 and 6 |
| A computational or data-driven approach | "Solution and approach"; deck slides 8 to 10 |
| A working prototype or demonstrable result | Live app; "Results and prototype demonstration"; deck slides 11 and 12 |
| Evidence supporting your approach | Gene-matching table, PMID-traced findings, validation checks (`docs/VALIDATION.md`); deck slides 12 and 13 |
| Clear documentation | README plus 14 documents in `docs/`; deck slide 14 |
| Potential real-world relevance | "Impact and future development"; deck slides 17 to 19 |

## Before you submit

- **The GitHub repository is private.** Make it public, or add the judges, before submitting the link.
- **Wake the backend** (open the Render `/health` address) shortly before judging.
- **Demo video:** follow `docs/DEMO.md` (a click-by-click script with timings); the pitch script in `Phytofusion-done.pdf` matches the deck order.
- **Fill the empty tables** before recording: add the key paper on Evidence and save the KPS pathway (see `docs/DEMO.md`).
