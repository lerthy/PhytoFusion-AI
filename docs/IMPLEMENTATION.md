# Implementation reference

A file-by-file description of the code that exists today. For intent and scope see
[Context.md](../Context.md); for the rules the code enforces see
[SCIENTIFIC_GUIDELINES.md](SCIENTIFIC_GUIDELINES.md).

Status: all five engines have a first implementation (engine 1 covers GFF3 only; the RAG part of
engine 4 and database persistence are not written), plus the six-screen frontend.

---

## 1. Layout

```
backend/
  pyproject.toml          deps, pytest/ruff/coverage config
  Dockerfile              python:3.12-slim + ncbi-blast+, non-root, healthcheck
  .dockerignore
  app/
    __init__.py           __version__ = "0.1.0"
    evidence.py           evidence classification
    genebridge.py         categorical compatibility assessment
    pathway.py            gene -> enzyme -> reaction -> compound graph
    main.py               FastAPI app
    ingestion/gff3.py     GFF3 parsing + gene id normalisation
    comparison.py         engine 2: FASTA/BLAST parsing, reciprocal best hits, blastp wrapper
    crispr.py             engine 5: scenario simulator + Markdown report
  tests/                  158 tests, ~99% statement+branch coverage
    data/sample.gff3      fixture
supabase/
  migrations/0001_init.sql
  tests/schema_test.sql
.github/
  workflows/ci.yml, workflows/deploy.yml, dependabot.yml, pull_request_template.md
```

Python 3.11+ (CI runs 3.11 and 3.12). Runtime deps: fastapi, pydantic, networkx, pandas, uvicorn.
Dev deps: pytest, pytest-cov, httpx, ruff, pip-audit.

---

## 2. `app/evidence.py`

Turns a set of literature references into one of three classes.

```python
EvidenceLevel = Literal["strong", "moderate", "limited"]
LEVELS: tuple[EvidenceLevel, ...]

@dataclass(frozen=True)
class Study:
    reference: str      # PMID or DOI
    experimental: bool  # True = experimentally characterised, False = computational

def classify_evidence(studies: Iterable[Study]) -> EvidenceLevel
```

Algorithm: references are collapsed into a dict keyed by the trimmed `reference` string, so a
duplicate reference counts once; if the same reference appears both ways, `experimental` wins
(logical OR). A study whose reference is empty or whitespace is dropped entirely — this is the
code-level half of the traceability rule.

| Distinct refs | Experimental refs | Result |
|---|---|---|
| ≥2 | ≥1 | `strong` |
| any | ≥1 | `moderate` |
| ≥2 | 0 | `moderate` |
| otherwise | | `limited` |

Pure function, no I/O. Tested in `tests/test_evidence.py` (9 tests) at every boundary.

---

## 3. `app/ingestion/gff3.py`

Standard-library GFF3 reading (no Biopython needed for this part). Three public functions plus a
`GeneRecord` dataclass (`gene_id`, `chromosome`, `start`, `end`, `strand`, `name`, `description`).

```python
def normalize_gene_id(raw: str) -> str
def parse_attributes(attr: str) -> dict[str, str]
def parse_gff3_genes(lines: Iterable[str]) -> list[GeneRecord]
def parse_chromosome_lengths(lines: Iterable[str]) -> dict[str, int]
```

- `normalize_gene_id` trims whitespace and strips a leading `gene:` or `gene-` prefix.
  **Case is preserved** — gene symbols are case-sensitive in this project. Raises `ValueError` on an
  empty result.
- `parse_attributes` splits column 9 on `;` then `=`, percent-decodes values with
  `urllib.parse.unquote` (so `Note=Kaurene%20synthase-like` reads correctly), ignores empty
  segments, and raises on a segment with no `=`.
- `parse_gff3_genes` accepts any iterable of lines. It skips blanks and `#` comments, keeps only
  rows whose type column is exactly `gene`, and **fails loudly** rather than silently dropping bad
  data. Every raised `ValueError` carries the 1-based line number. Validated: exactly 9
  tab-separated columns, integer coordinates, `1 <= start <= end`, strand in `+ - . ?`, and an `ID`
  attribute.
- `parse_chromosome_lengths` reads `##sequence-region <id> <start> <end>` directives and returns
  `end - start + 1`.

Design note: the parser is deliberately strict. A malformed annotation file that parses "mostly
fine" would put wrong coordinates on screen, which is worse than a crash.

Tested in `tests/test_gff3.py` (13 tests) against `tests/data/sample.gff3`, which mixes gene, mRNA
and exon rows, two chromosomes, a percent-encoded note, a `-` strand gene and a blank line.

---

## 4. `app/genebridge.py`

The assessment engine. Input and output are both frozen dataclasses of categorical values — there is
no numeric score anywhere by design.

```python
@dataclass(frozen=True)
class AssessmentInput:
    sequence:   Literal["related", "weakly_related", "unknown"]
    functional: Literal["characterized", "predicted"]
    pathway:    Literal["supported", "incomplete", "unknown"]
    expression: Literal["supporting", "conflicting", "unavailable"]
    context:    Literal["characterized", "uncertain"]

@dataclass(frozen=True)
class Assessment:
    level: EvidenceLevel
    deserves_investigation: bool
    missing_information: list[str]
    concerns: list[str]
    explanation: str

def assess(data: AssessmentInput) -> Assessment
```

Each of the five dimensions has an explicit "we don't know" value, so a gap stays visible instead of
defaulting to something optimistic.

`assess` does four things:

1. **Collect missing information.** Each `unknown` / `predicted` / `unavailable` / `uncertain` value
   appends a plain-language string naming what is absent.
2. **Collect concerns.** `weakly_related`, `incomplete` and `conflicting` append a specific warning.
3. **Pick a level.** All five favourable → `strong`. Otherwise `unknown` sequence or `predicted`
   function → `limited` (these two gaps dominate: without them there is nothing to reason from).
   Everything else → `moderate`.
4. **Decide `deserves_investigation`** — `level != "limited" and pathway != "incomplete"`. This reads
   the input field directly rather than string-matching the generated `concerns` text, so changing
   wording can't change the verdict.

`_explain` renders the explanation and always opens with "This is an evidence class, not a success
probability."

`assess` is pure and deterministic — same input, same `Assessment`, which the tests assert.

Tested in `tests/test_genebridge.py` (14 tests), including that explanations never contain `%`.

---

## 5. `app/pathway.py`

A `networkx.DiGraph` wrapper that enforces traceability at insertion time.

```python
NODE_KINDS = ("gene", "enzyme", "reaction", "compound")

class PathwayGraph:
    def add_node(node_id, kind, label=None) -> None
    def add_step(source, target, relation, evidence_level, reference) -> None
    def downstream(node_id) -> set[str]
    def shared_precursors(compound_a, compound_b) -> set[str]
    def to_cytoscape() -> list[dict]
```

- `add_node` rejects a `kind` outside `NODE_KINDS`; `label` defaults to the id.
- `add_step` is the guard rail. It raises `KeyError` if either endpoint is unknown (no accidental
  node creation, which is `networkx`'s default), `ValueError` on an evidence level outside `LEVELS`,
  and `ValueError` if `reference` is empty or whitespace. **An edge without a PMID/DOI cannot exist.**
- `downstream` wraps `nx.descendants`.
- `shared_precursors` intersects `nx.ancestors` of both targets and filters to `kind == "compound"`,
  so an upstream gene or enzyme is not reported as a precursor.
- `to_cytoscape` emits the `{"data": {...}}` element list Cytoscape.js expects, nodes then edges,
  carrying `evidence_level` and `reference` through to the UI so the frontend can show provenance
  without a second query.

Tested in `tests/test_pathway.py` (11 tests).

---

## 6. `app/main.py`

```python
app = FastAPI(title="PhytoFusion AI", version=__version__)

GET  /health                    -> {"status": "ok", "version": ...}
POST /api/genebridge/assess     -> AssessResponse
```

Pydantic models mirror the dataclass `Literal`s, so an out-of-vocabulary value — including anything
numeric like `"95%"` — is rejected with HTTP 422 before reaching `assess`. The handler converts the
request to `AssessmentInput` and returns the `Assessment`; FastAPI serialises the dataclass via
`response_model=AssessResponse`.

Tested in `tests/test_api.py` (10 tests) with `TestClient`, covering each missing field, an invalid
enum, and an assertion that no response field is a bare number.

---

## 7. `supabase/migrations/0001_init.sql`

13 tables, 3 enums (`evidence_level`, `gene_role`, `scenario_type`), `pgcrypto` UUID keys, and
`vector` for embeddings.

Shape: `species` → `genome_assemblies` → `chromosomes` / `genes`; `gene_comparisons` joins a host
gene to a donor gene; `pathways` + `pathway_edges` hold the graph; `compounds`; `evidence` +
`literature_chunks`; `finding_evidence` links evidence to a gene, comparison or pathway edge;
`crispr_scenarios` + `scenario_results`.

Constraints that encode the project rules:

- `evidence` has `check (pmid is not null or doi is not null)` — a source row cannot be anonymous.
- `gene_comparisons` stores the five dimensions as `check`-constrained text plus an
  `overall_level evidence_level`. `percent_identity numeric` is the one number in the schema and it
  is a measured BLAST output, not a compatibility judgement.
- `scenario_results.limitations` is `not null` — a result cannot be saved without them.
- `genes` is unique on `(assembly_id, gene_id)`; `gene_comparisons` on `(host_gene_id, donor_gene_id)`.
- Delete behaviour is explicit on every FK: cascade down ownership chains (species → assemblies →
  chromosomes/genes → comparisons, scenarios → results) and `set null` for optional references
  (`pathway_edges`, `donor_species_id`). The local schema run caught a missing rule here, where
  deleting a species failed because `gene_comparisons` still referenced its genes.
- RLS is enabled on all 13 tables in a `do $$ ... foreach ... $$` block with a `public read` policy
  each. Writes require the service-role key, i.e. the backend.
- `match_literature(query_embedding vector(1536), match_count int default 5)` returns rows ordered by
  cosine distance with `1 - (embedding <=> query)` as similarity; an HNSW index backs it.

Embedding dimension is hard-coded at 1536 in the column, the index and the function — change all
three together if the embedding model changes.

---

## 8. `supabase/tests/schema_test.sql`

Six sections in a single transaction ending in `rollback`, so it leaves no rows behind and can run
against a dev database. A `pg_temp.expect_error(stmt, label)` helper executes a statement and fails
the run if it *succeeds*.

1. All 13 tables exist and each has `relrowsecurity` set.
2. `evidence` without PMID or DOI is rejected; with one, accepted.
3. An invalid enum value is rejected.
4. A free-form value in `sequence_relationship` is rejected; duplicate comparison and duplicate gene
   id are rejected.
5. Two orthogonal unit vectors are inserted and `match_literature` must return the nearer one first.
6. Deleting a species removes its assemblies.

Run with `psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f supabase/tests/schema_test.sql`.

---

## 9. Test and lint configuration

`pyproject.toml` drives everything, so local and CI runs are identical:

- `addopts = "-ra --strict-markers --cov=app --cov-report=term-missing --cov-fail-under=85"` — the
  coverage gate fires on a bare `pytest`.
- `[tool.coverage.run] branch = true` — branch coverage, which matters for the classification logic.
- `markers = ["integration: ..."]` with `--strict-markers` so a typo'd marker errors.
- ruff: line length 100, target py311, rules `E, F, I, B, UP, SIM`.

Current state: 158 backend tests at ~99% coverage of `app/`, ruff clean; 18 frontend tests.

---

## 10. CI/CD

`ci.yml` runs on push to `main`, on PRs, and via `workflow_call` from `deploy.yml`. Jobs:
`backend-lint`, `backend-test` (3.11 + 3.12 matrix), `schema-test` (service container
`pgvector/pgvector:pg16`, applies migrations, runs the schema tests, then drops and recreates
`public` and re-applies to prove a clean build), `docker-build` (builds and curls `/health` in the
container, GHA layer cache), `frontend` (detects `frontend/package.json` and skips until it exists),
`security` (`pip-audit` + gitleaks), `science-guardrails`, and `ci-passed` as the single required
check.

`science-guardrails` greps `backend/app` and `frontend/src` for numeric compatibility/success/
efficacy claims and for "has been engineered" / "proven effective" / "cures" wording. It scans app
code only — tests and docs state the rules and would self-trigger.

`deploy.yml` targets Supabase only. On a `v*` tag or manual dispatch it re-runs CI, links the project,
shows `supabase db push --dry-run`, and applies migrations only on a tag or explicit
`dry_run: false`, gated by the `production` GitHub environment. No AWS.

Verified locally: backend tests, ruff, workflow YAML parsing, guardrail greps, and schema sections
1–4 and 6 against Postgres 14 with the pgvector parts stubbed out (pgvector is not installed locally).
Not yet verified anywhere: the vector search test, the Docker build, and the workflows themselves.

---

## 10b. `app/comparison.py` (engine 2)

Pure parsing and classification plus one thin subprocess wrapper.

- `read_fasta` returns `{id: sequence}` (id is the first header token); rejects duplicate ids,
  empty headers and sequence before a header, with line numbers.
- `parse_blast_tabular` reads `outfmt 6` with the fields in `BLAST_FIELDS`
  (`qseqid sseqid pident length evalue bitscore`) into `BlastHit`s and raises on malformed rows.
- `best_hits` keeps the highest bitscore per query (ties: lower e-value, then subject id, so results
  are deterministic). `reciprocal_best_hits` returns sorted mutual pairs, the usual starting point
  for candidate orthologs.
- `classify_sequence_relationship(hit)` maps a hit to `related` / `weakly_related` / `unknown`.
  Defaults (identity >= 40 and e-value <= 1e-10 for related; e-value <= 1e-3 for weak) are keyword
  parameters. They are conventional starting values, not claims about these species; cite whatever
  the team chooses. No hit means `unknown`.
- `map_genes_to_chromosomes` returns `None` for a gene that is not in the annotation instead of
  guessing.
- `run_blastp(query, subject, runner=..., which=...)` shells out to `blastp`, with the runner and
  `which` injectable so tests do not need BLAST+. It raises a clear error when the binary is missing
  or exits non-zero. It has not been run against a real BLAST+ install yet.

## 10c. `app/crispr.py` (engine 5)

`simulate(ScenarioInput) -> ScenarioResult`. Input: scenario type (`host_modification` or
`donor_integration`), host and optional donor species, target gene id, optional chromosome,
documented function, pathway, references, and a GeneBridge `Assessment`.

- It adds no biology of its own. The documented function and pathway are restated from what the
  caller supplies; when they are absent the result says so and lists them under missing information.
- Consequences are generic and conditional ("could alter ... direction and size cannot be
  predicted"); integration adds the standing note that large insertions remain technically hard.
- `limitations` always contains at least the three base statements (no editing performed,
  qualitative only, efficacy not assessed).
- No references forces `evidence_level` to `limited`; otherwise it follows the assessment.
- `donor_integration` without a donor species, or empty host or gene fields, raise `ValueError`
  (the API returns 422).
- `render_report_markdown` produces the virtual plant report. A test asserts it contains no
  percentages or forbidden claim wording.

## 10d. New endpoints

| Method | Path | Notes |
|---|---|---|
| POST | `/api/comparison/classify` | `pident` in 0-100 and `evalue` >= 0, else 422 |
| POST | `/api/scenarios/simulate` | returns the result plus `report_markdown` |

CORS allows `http://localhost:5173` by default; set `CORS_ORIGINS` (comma separated) to change it.

## 10e. Frontend (`frontend/`)

Vite + React 18 + TypeScript (strict), Cytoscape for graphs, plain CSS with semantic tokens and light and dark themes (see [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md)). A landing page (`#/about`, the default) explains the project and leads into the app. The app has four top-level steps (Home, Genomes, Compare, Simulate) over seven hash-routed views: `#/dashboard`, `#/genome`, `#/genebridge`, `#/pathway`, `#/evidence` (tabs under Compare), `#/crispr`, `#/report` (tabs under Simulate). `router.ts` owns the grouping. Screens load from the database endpoints (503 shows setup guidance, not an error) and fall back to local files where that makes sense.
Scripts: `dev`, `build` (type-check then bundle), `lint` (`tsc --noEmit`), `test` (vitest).

| File | Role |
|---|---|
| `src/api.ts` | typed fetch client; `VITE_API_URL` overrides the default `http://localhost:8000` |
| `src/types.ts` | `OPTIONS` constant drives both the select inputs and the `AssessInput` type |
| `src/gff3.ts` | browser GFF3 parser mirroring the Python one (strict, line-numbered errors); also reads `#OriSeqID` comments into friendlier sequence names |
| `src/helix.ts` | pure helix geometry for the 3D view (point on a strand, turns, gene position), unit-tested |
| `src/components/Genome3D.tsx` | the lazy-loaded `three.js` helix view (default export, loaded with `React.lazy`) |
| `src/mapScale.ts` | pure map helpers: nice axis ticks, nearest gene for hover, main-vs-scaffold split, gene-density bins (all unit-tested) |
| `src/pathway.ts` | graph validation: an edge without a reference or valid evidence level is rejected on load |
| `src/screens/*` | the six screens |
| `src/components/*` | evidence badge, shared assessment fields, local file loader |

Genome Explorer and Pathway Explorer read files in the browser (nothing is uploaded), so the app
contains no sample genes, pathways or PMIDs. CRISPR Studio autofills the chromosome from the loaded
genome when the gene id matches. The Virtual Plant Report renders the last scenario and offers a
Markdown download. Verified: type-check, 74 vitest tests and a production build. The UI has not been
exercised in a browser yet, and there are no component tests.

## 10f. Persistence layer

| Module | Role |
|---|---|
| `app/store.py` | `Store` protocol with two implementations: `SupabaseStore` (PostgREST + Storage over `httpx`, paged and chunked) and `InMemoryStore` (tests). The rest of the code never imports Supabase directly, so the later AWS move means one new class. |
| `app/repository.py` | The only code that knows the table layout: genomes, evidence, literature, comparisons, pathways, scenarios. Writes are upserts on stable keys, so re-running a seed is safe. |
| `app/ingestion/seed.py` | CLI that loads a GFF3 (plus optional protein FASTA and a `gene_id,family` CSV) into the database. Dry run unless `--apply`. Families are never inferred. |
| `app/pipeline.py` | BLASTs donor candidates against the host proteome in both directions. Only the **sequence** dimension is derived; the other four stay at conservative defaults (`predicted`, `unknown`, `unavailable`, `uncertain`) unless evidence-backed overrides are given. |
| `app/literature.py` | Chunking and an OpenAI-compatible embeddings client. Retrieval returns passages verbatim with their PMID/DOI. It never generates text, so it cannot invent a gene function. |
| `app/routes.py` | `/api/stats`, `/species`, `/genome/{id}`, `/evidence`, `/literature`, `/literature/search`, `/pipeline/compare`, `/comparisons`, `/pathways`, `/scenarios`. They answer 503 when Supabase is not configured, 502 when the database fails, and 422 or 404 for bad input. |

Retries: `SupabaseStore` retries temporary failures (HTTP 429, 5xx and Cloudflare 520-524 such as a 522 timeout, plus dropped connections) up to 4 times with a growing pause. Only reads, upserts, counts and file uploads are retried. A plain insert never is, because a timeout does not say whether the rows were written. Error messages are collapsed and shortened, so an HTML error page no longer floods the terminal.

Sequence names: the seed script reads `#OriSeqID=Sbai1<TAB>Accession=GWHAOTO00000001` comments (as in Genome Warehouse files) and stores the friendly name as `chromosomes.name` and the file's own id as `chromosomes.accession` (migration 0004). If two sequences would get the same name, those keep their accession as the name, so nothing is merged.

Migration `0003_persistence_columns.sql` adds `pathways.graph`, `scenario_results.report_markdown` and
`result`, and unique constraints on `evidence.pmid` and `evidence.doi`. Run the API with
`uvicorn app.main:app --env-file ../.env`. Status: tested against in-memory and mocked HTTP only;
nothing has been written to the hosted database from code yet, and migration 0003 is not applied.

## 11. Extending

**A new engine module** — pure functions over dataclasses, no DB calls inside the logic; return
categorical values and a list of what is missing; add tests in the same commit.

**Persistence** — add new tables to `Repository` and keep SQL knowledge out of routes and engines.
Use `InMemoryStore` in tests.

**Schema change** — new numbered file in `supabase/migrations/`, never edit an applied one, and
extend `schema_test.sql` in the same PR.

**Frontend** — add screens in `frontend/src/screens/` and register them in `App.tsx`. Export a
pathway from Python with `json.dump(graph.to_cytoscape(), f)` to load it in Pathway Explorer.
