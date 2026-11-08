# Devpost "Project details": paste these

Three parts of the form: the Project Story (Markdown), the "Built with" tags, and the "Try it out" links.

---

## 1. Project Story (paste everything between the two lines)

---

## Inspiration

Medicinal plants make remarkable compounds, but the genes behind them are scattered across huge genomes, papers
and databases. One of us is a pharmacy student, the other a DevOps engineer. We kept asking the same question:
*could a gene from one medicinal plant, in theory, add a missing step in another?* And a second one: how would
anyone know how well the evidence supports that idea, and what is still missing?

We picked two skullcaps from the same genus. ***Scutellaria baicalensis*** is known for flavonoids such as
baicalein, baicalin and wogonin. ***Scutellaria barbata*** is known for clerodane diterpenoids. Both are used in
traditional Chinese medicine (Zhao et al. 2019, PMID 31236960; Wang et al. 2020, PMID 31577937). A 2023 paper
(Qiu et al., PMID 37395679) characterised the KPS enzymes that start clerodane diterpenoid biosynthesis in both
plants. That gave us a precise, testable question for a hypothetical CRISPR gene transfer, studied on paper only.

## What it does

**PhytoFusion AI** is a computational platform for reasoning about that question. Nothing is edited or built.

- **Genomes:** both published genomes (30,313 and 34,909 genes) as chromosome maps drawn to scale, with a 3D view.
- **Compare genes:** BLAST finds the closest host gene for a donor gene, then a reciprocal check confirms it. Don't know the gene ID? Paste a protein sequence or an NCBI accession and BLAST lists the matching genes (computed, not an AI guess).
- **Pathways:** how genes, enzymes and compounds connect, with a source and an evidence level on every step.
- **Evidence:** a strong, moderate or limited class for each finding. Never a score or a probability.
- **Scenario and report:** a hypothetical gene transfer, with what it could mean, **what we don't know**, and the limits.

An optional AI model can explain a result in plain words, but only from facts the app already computed. It is
labelled as AI-written and never sets an evidence level.

## How we built it

- **Backend:** Python, FastAPI and pydantic, with BLAST+ for the sequence search, in a Docker container on Render.
- **Frontend:** React and TypeScript with Vite, Cytoscape for the pathway graph and three.js for the 3D views, on Netlify.
- **Data:** Supabase (Postgres with pgvector, row-level security, versioned SQL migrations).
- **Quality:** 248 backend tests at 98% coverage, 74 frontend tests, and GitHub Actions CI with seven checks.
  The pipeline also fails the build if the code ever contains a numeric success claim or says a plant "has been engineered".
- **Documentation:** a README plus 14 documents, including a sources file where every claim traces to a PMID or DOI.

## Challenges we ran into

- **The gene names did not match the paper.** Our annotation uses IDs like `Sbar9A9T61`, not "SbarKPS2". We downloaded
  the paper's protein sequences and BLASTed them against both genomes. One matched at 100% identity. The other two are
  best matches from sequence similarity, so we label them that way, not as proven identical.
- **A search that took hours.** Comparing whole proteomes against each other was far too slow for a web app. Searching only
  the candidate genes, then checking their best hits back, gives the same answer for these genes in seconds.
- **Not overclaiming.** It is easy to turn "similar sequence" into "it would work". We built the opposite: evidence
  classes, explicit "unknown", and guardrails in the code and in CI.

## Accomplishments that we're proud of

- A **working, deployed prototype** on real published genomes, not a mock-up.
- **Validation we can show.** The paper's own protein finds its gene at 100%. The best host hit for both KPS proteins
  (`Sbai8C203T0`, 84% and 89%) stands about 28 to 31 points above the runner-up (about 57%).
- **An honest limit, published.** 86% of 300 random donor genes would also count as "related", because the plants share a genus.
  So the label alone is not the signal. The mutual best match and the margin are. We say so in our validation document.
- Every finding is **traced to a source**, and the AWS architecture is generated as code and kept in the repository.

## What we learned

- **Sequence similarity is not function.** Two close genes can do different jobs, which is why the app shows what is
  known, what conflicts and what is missing, not a single number.
- **Uncertainty is a feature.** A tool that says "unknown" and lists the gap is more useful to a researcher than one that always answers.
- Combining **pharmacy and DevOps** worked: pharmacy gave the meaning of the data, and automation, tests and
  pipelines made it reproducible.

## What's next for PhytoFusion AI

- Build a small **benchmark of known orthologs** and report precision and recall.
- Add **gene expression data** and more pathways, such as the full flavonoid route.
- Show the **best-versus-runner-up margin** in the comparison table.
- Add sign-in and rate limits before opening the API publicly, then move to **AWS** as planned.
- Test the most promising hypotheses with **laboratory partners**. Traditional use and computation are reasons to
  study a plant, not proof that it works.

---

## 2. Built with (paste each as a tag; up to 25)

`python`, `fastapi`, `pydantic`, `pandas`, `networkx`, `blast`, `typescript`, `react`, `vite`, `three.js`,
`cytoscape.js`, `postgresql`, `pgvector`, `supabase`, `docker`, `github-actions`, `netlify`, `render`, `pytest`,
`vitest`, `groq`

That is 21 tags, so there is room for four more. Add `ncbi` and `genome-warehouse` if you want the data sources
listed too.

## 3. "Try it out" links

| What | URL |
|---|---|
| Live demo | https://photofusionai.netlify.app |
| Source code | https://github.com/lerthy/PhytoFusion-AI |

**The GitHub repository is private.** Judges cannot open the second link until you make it public (GitHub:
Settings, then Danger Zone, then Change visibility) or add them as collaborators. If you would rather keep
it private, remove that link and say so in the story.

Optional third link: the pitch video, once you have recorded it (see `docs/DEMO.md`).

## Before you submit

- Open the demo link a minute before submitting (the free server sleeps and the first request can take a minute).
- The story does not claim any saved evidence or pathways, because your database has none yet.
  If you add them first (see `docs/DEMO.md`), the live site looks more finished.
- Check the AI claim: the explain buttons need `AI_API_KEY` set in Render. Without it they say AI is not switched on,
  which the story already allows for ("optional").
