# Sources

Where the science in this project comes from. Every finding in the app must trace to a PMID or DOI.

## The key paper (KPS genes)

**Qiu T, Li Y, Wu H, Yang H, Peng Z, Du Z, Wu Q, Wang H, Shen Y, Huang L.** *Tandem duplication and
sub-functionalization of clerodane diterpene synthase originate the blooming of clerodane
diterpenoids in Scutellaria barbata.* The Plant Journal 116(2):375-388, 2023.

- PubMed: <https://pubmed.ncbi.nlm.nih.gov/37395679/> (PMID **37395679**)
- DOI: <https://doi.org/10.1111/tpj.16377>
- Publisher page: <https://onlinelibrary.wiley.com/doi/10.1111/tpj.16377>
- Access: subscription only (not in PubMed Central). We read the abstract-level summary and the NCBI
  records below, not the full text.

What the abstract reports: SbarKPS1 is a monofunctional (-)-kolavenyl diphosphate synthase. SbarKPS2
and SbaiKPS1 mainly produce neo-cleroda-4(18),13E-dienyl diphosphate with a small amount of (-)-KPP.
SbarKPS1 and SbarKPS2 are a tandem gene pair with high sequence identity. Suggested evidence level for
the app: **moderate** (one experimental study).

## Genome papers and records

- **Comparative Genome Analysis of *Scutellaria baicalensis* and *Scutellaria barbata* Reveals the
  Evolution of Active Flavonoid Biosynthesis.** Genomics, Proteomics & Bioinformatics 18(3):230, 2020.
  <https://pmc.ncbi.nlm.nih.gov/articles/PMC7801248/>
  Data availability: Genome Warehouse GWHAOTO00000000 (*S. baicalensis*) and GWHAOTP00000000
  (*S. barbata*); CoGe genome ID 54176; raw reads CRA001730.
- **Genome Warehouse, host:** <https://ngdc.cncb.ac.cn/gwh/Assembly/10411/show> (GWHAOTO00000000,
  *S. baicalensis*, 30,313 genes in our GFF).
- **Genome Warehouse, donor:** <https://ngdc.cncb.ac.cn/gwh/Assembly/10412/show> (GWHAOTP00000000,
  *S. barbata*, 34,909 genes in our GFF).
- Downloads used: `GWHAOTO00000000.gff`, `GWHAOTP00000000.gff` and the two `.Protein.faa` files from
  <https://download.cncb.ac.cn/gwh/Plants/>.
- Related, **not read**: *The genomes of medicinal skullcaps reveal the polyphyletic origins of clerodane
  diterpene biosynthesis in the family Lamiaceae*, Molecular Plant 2023,
  <https://www.cell.com/molecular-plant/fulltext/S1674-2052(23)00006-0>. It describes newer
  chromosome-level assemblies, which may use different gene IDs than our files.

## The paper's protein sequences at NCBI

Deposited with the paper (their records cite PMID 37395679):

- SbarKPS1: <https://www.ncbi.nlm.nih.gov/protein/WJZ49119.1> (WJZ49119.1, 809 aa)
- SbarKPS2: <https://www.ncbi.nlm.nih.gov/protein/WJZ49120.1> (WJZ49120.1, 808 aa)

No *S. baicalensis* sequence is linked to the paper, so SbaiKPS1 can only be found by similarity.

## How the KPS genes were matched to our annotation

The annotation files use IDs like `Sbar9A9T61`, not the paper's names. We ran BLAST (`blastp`, 2.17.0+)
with the two NCBI sequences against the protein sets of our two genomes and took the best hits.

| Paper's name | Gene in our files | Identity | Confidence |
|---|---|---|---|
| SbarKPS2 | `Sbar9A9T61` | 100% (identical, 808 aa) | Confirmed: same protein |
| SbarKPS1 | `Sbar9A10T43` | 94.8% (our model is 853 aa, the paper's 809) | Best match, not identical |
| SbaiKPS1 | `Sbai8C203T0` | 84-89% (our model is short, 682 aa) | Best match only |

Sanity check: `Sbar9A9T61` (979,922-985,718) and `Sbar9A10T43` (1,017,746-1,024,094) are on the same
sequence (`Sbar9`) and strand, about 38 kb apart, which fits a tandem pair.

In the app's Compare screen these give: `Sbar9A9T61` → `Sbai8C203T0` at 89%, mutual best match;
`Sbar9A10T43` → `Sbai8C203T0` at 84%, not mutual.

**Open point for the science team:** the two non-identical matches are inferences from sequence
similarity. The paper's own table of gene IDs (full text or supporting information) would confirm them.
Describe them as "best matching genes in the annotation", not as proven identical.
