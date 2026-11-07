PhytoFusion AI – End-to-End Project Plan (Option A)
Selected direction: Genetic Trait Integration
EthnoHack – Track 2
Project objective: Develop an AI-powered computational biotechnology platform that investigates how selected genetic characteristics from two medicinal plants could theoretically be integrated into one host plant using CRISPR-based genetic engineering.
I would divide the project into two major workstreams:
Scientific part: Establish the biological foundation, choose the two herbs, investigate their chromosomes, genes, metabolic pathways and genetic compatibility, and define the hypothetical genetic-engineering scenario.
Technical part: Build the data pipelines, comparative genomics engine, CRISPR simulation, AI analysis, backend and interactive frontend.
The important thing is that the two parts must work together. We should not build an attractive application first and then try to find scientific information to justify it.
PART 1 – SCIENTIFIC PLAN
Research and biological foundation
1. Define the scientific objective
First, we need a specific research question.
I propose:
Can comparative genomics and AI-assisted analysis identify compatible genetic characteristics from two medicinal plant species that could theoretically be integrated into a single host plant using CRISPR-based genome engineering, potentially expanding its natural-product profile?
We are investigating three things:
Can we identify useful genetic characteristics in two medicinal plants?
Are the genes and associated metabolic pathways compatible enough to justify a genetic-engineering hypothesis?
Could a hypothetical engineered plant produce an altered or expanded natural-compound profile?
The objective is not to claim that we can create a more effective medicine. We are investigating the potential to alter natural-product production. Therapeutic efficacy would require separate experimental evidence.
2. Select the two medicinal plants
I recommend an important improvement to our original selection.
Instead of Salvia miltiorrhiza and Dendrobium officinale, I would use two species from the same genus:
Chinese Skullcap Extract 10:1 — Calming & Immune Support – Ecogenya
Plant A – Scutellaria baicalensis
Host plant
Known for flavonoid compounds, including baicalein, baicalin and wogonin.
It has a chromosome-level reference genome assembled into nine chromosomes.
PubMed Central (PMC)+1
barbed skullcap (Scutellaria barbata) - Botanical Realm
Plant B – Scutellaria barbata
Donor / comparison plant
Known for clerodane diterpenoids and other natural compounds.
Its reference genome has also been assembled at chromosome level, into 13 pseudochromosomes.
PubMed+1
Why these two?
There is already published research directly comparing their genomes and natural-product biosynthesis.
Researchers have identified differences in genes involved in flavonoid biosynthesis, including PAL, CHS, 4CL and CYP82D gene families. They have also documented differences in chromosome organization and gene duplication.
PubMed+1
This provides something extremely valuable for your hackathon: actual scientific research on the exact two species you want to compare.
Proposed genetic-engineering hypothesis
Use S. baicalensis as the hypothetical host and investigate selected genetic characteristics from S. barbata.
One particularly interesting research direction is the clerodane diterpenoid pathway.
A 2023 study identified and functionally characterized diterpene synthases in these species, including SbarKPS1, SbarKPS2 and SbaiKPS1. The researchers found functional differences between the enzymes.
PubMed+1
This gives us a concrete candidate family to investigate rather than choosing genes randomly.
Our hypothesis would be:
Could a selected genetic characteristic associated with clerodane diterpene production in S. barbata be theoretically integrated into the genetic and metabolic system of S. baicalensis to alter its diterpenoid production profile while retaining its existing flavonoid characteristics?
That becomes our central scientific investigation.
3. Understand the chromosomes and genomes
Frontiers | The near-complete genome assembly of Ampelopsis grossedentata provides insights into its origin, evolution, and the regulation of flavonoid biosynthesis
frontiersin.org
Before discussing genetic integration, we need to understand the genomes.
For both plants, we need to collect:
Information
Why we need it
Genome assembly
The reference DNA sequence
Chromosome information
Understand genomic organization
Gene annotations
Identify genes and their functions
Protein sequences
Compare encoded proteins
Gene locations
Locate candidate genes on chromosomes
Gene expression
Understand where and when genes are active

Our scientific team should produce two chromosome maps.
One for S. baicalensis and another for S. barbata.
Then we identify where the relevant metabolic genes are located.
Important distinction: We are not combining the chromosomes of the two plants. We are investigating selected genes or genetic characteristics, potentially incorporated into a host genome. Their different chromosome organizations make compatibility assessment particularly important.
4. Identify the relevant genes
This is one of the most important scientific tasks.
We should not attempt to study every gene in either plant. We should focus on the genes associated with the natural products we are investigating.
I would divide them into three categories:
Gene group
Scientific purpose
Biosynthetic genes
Participate in producing natural compounds
Regulatory genes
Influence the expression of other genes
Enzyme-encoding genes
Encode proteins that catalyse metabolic reactions

For the initial investigation, we should examine:
PAL: Phenylalanine ammonia-lyase.
CHS: Chalcone synthase.
4CL: 4-coumarate-CoA ligase.
CHI: Chalcone isomerase.
CYP82D: Flavone hydroxylase family.
KPS: Kaurene/clerodane-related diterpene synthase family, including the published KPS candidates.
These genes have different biological functions. We should not assume they are interchangeable.
Our priority is to identify the donor and host candidate genes with the strongest available experimental evidence.
5. Compare the genetic characteristics
Genome Context Viewer
gcv-arabidopsis.ncgr.org
Now we investigate whether selected genes from both plants are related and what their functional differences are.
Our scientific analysis should examine:
A. Genetic similarity
Are the candidate genes related? Do they encode similar proteins?
B. Functional similarity
Do their encoded proteins have comparable biological functions, or have they developed different functions?
C. Chromosomal context
Where are the genes located? Are they associated with gene clusters or duplicated regions?
D. Expression evidence
Are they expressed in the same tissues? Are relevant expression datasets available?
E. Metabolic compatibility
Would the host plant have the necessary precursor compounds, enzymes and downstream metabolic machinery?
This last question is especially important.
Even if a donor gene encodes a useful enzyme, the host might not possess everything needed for the complete metabolic pathway.
6. Investigate CRISPR-based genetic integration
CRISPR Gene Editing: How This Breakthrough Works
wellri.com
This is where our project becomes different from a normal comparative genomics project.
We will develop two hypothetical engineering scenarios:
Scenario
Concept
Host genome modification
Explore how a selected endogenous host gene or regulatory characteristic could be modified
Donor genetic integration
Evaluate the hypothetical introduction of a selected donor genetic characteristic into the host genome

A key scientific distinction: ordinary CRISPR knockout or editing and inserting a donor gene are not the same operation.
Introducing larger DNA sequences into plant genomes remains technically challenging, even with modern CRISPR-assisted approaches.
PMC+1
Our prototype should therefore evaluate the feasibility of these scenarios computationally, not claim that an insertion has actually happened.
The CRISPR module will examine:
The candidate gene and its documented function.
Its relationship to the host genome.
Its metabolic pathway dependencies.
The hypothetical consequences of the proposed modification.
The scientific evidence and unresolved risks.
We will not attempt actual biological editing during the hackathon.
7. Define the scientific validation criteria
We need a methodology that prevents the AI from inventing compatibility.
I recommend evaluating each candidate using five dimensions:
Dimension
What we evaluate
Sequence evidence
How closely related are the genes?
Functional evidence
Is the biological function experimentally documented?
Pathway compatibility
Does the host contain the necessary pathway components?
Expression evidence
Is there evidence of relevant tissue expression?
Genomic context
What do chromosome location and gene organization tell us?

The system should produce an evidence-based classification:
Strong evidence: Multiple supporting genomic and functional studies.
Moderate evidence: Some supporting research, but important uncertainties remain.
Limited evidence: Mostly computational predictions or missing biological information.
These are evidence classifications, not probabilities that genetic engineering will succeed.
Scientific deliverables
At the end of Part 1, we should have:
A research report describing both medicinal plants.
Two genome and chromosome references.
A curated list of relevant genes.
A gene comparison table.
A metabolic pathway diagram.
A selected genetic integration hypothesis.
A CRISPR scenario and feasibility assessment.
A scientific limitations and validation report.
This becomes the scientific foundation of our application and pitch.
PART 2 – TECHNICAL PLAN
Software engineering, AI and computational biology
This is where we turn the scientific research into a working product.
1. Define the technical architecture
I recommend building five core engines that communicate with each other.
PhytoFusion AI – Technical Architecture
Scientific data sources
Genome databases, research papers, gene annotations and compound databases
Engine 1 – Data ingestion
Download, clean, validate and normalize genome datasets
Engine 2
Comparative genomics
Gene and chromosome comparison
Engine 3
Pathway intelligence
Genes, enzymes and compounds
Engine 4 – AI + GeneBridge
Evidence retrieval, gene relationship assessment and compatibility analysis
Engine 5 – CRISPR scenario simulator
Explore hypothetical genetic modifications and their predicted consequences
PhytoFusion AI web application
Interactive chromosome explorer, pathway visualization and virtual engineered-plant report
2. Build Engine 1 – Scientific Data Ingestion
Purpose: Collect all the scientific information our application needs.
We should avoid downloading enormous raw sequencing datasets unnecessarily. For the prototype, start with already assembled genomes and annotated gene files.
Recommended sources:
Resource
Data we need
Genome Warehouse
Genome sequences and annotations
NCBI Datasets
Genome and gene information
PubMed
Scientific publications
PubChem
Natural-compound information

A useful starting point is the comparative-genomics paper that deposited the assemblies in Genome Warehouse:
S. baicalensis: GWHAOTO00000000
S. barbata: GWHAOTP00000000
The paper also provides access to the genome data through CoGe.
Oxford Academic+1
The files to obtain:
File
Format
Purpose
Genome
FASTA
DNA sequence
Annotation
GFF3
Chromosomes, gene positions and annotations
Proteins
FASTA
Protein sequence comparison
Coding sequences
FASTA
Gene sequence information
Literature metadata
CSV/JSON
Supporting scientific evidence

Create a Python ingestion script that:
Loads both plant datasets.
Checks their assembly identifiers and metadata.
Extracts chromosome information.
Reads gene annotations.
Normalizes gene identifiers.
Stores the relevant data for analysis.
Deliverable: Two structured genome datasets ready for processing.
3. Build Engine 2 – Comparative Genomics Engine
Frontiers | Genome-wide analysis of the Cannabis sativa cytochrome P450 monooxygenase superfamily and uncovering candidate genes for improved herbicide tolerance
frontiersin.org
This is responsible for comparing the genetic information from both plants.
Technology:
Python.
Biopython.
BLAST+.
GFF3 parsing tools.
Pandas.
The engine should perform four main operations:
A. Gene identification
Load the curated genes involved in the pathways being investigated.
B. Sequence comparison
Compare protein sequences to identify related genes and potential orthologs.
C. Chromosome mapping
Identify where the selected genes are located in each genome.
D. Gene relationship analysis
Identify gene families, duplications, genomic organization and available synteny evidence.
The output should be something like:
Information
Host
Donor
Species
S. baicalensis
S. barbata
Candidate gene
SbaiKPS1
SbarKPS1
Chromosome
Retrieved from annotation
Retrieved from annotation
Protein function
Published evidence
Published evidence
Expression
Available evidence
Available evidence

The example above is a candidate comparison, not an assertion that the genes have interchangeable functions.
Deliverable: A comparative genomics engine that generates structured gene comparisons.
4. Build Engine 3 – Metabolic Pathway Intelligence
Exploring photosynthesis evolution by comparative analysis of metabolic networks between chloroplasts and photosynthetic bacteria | BMC Genomics | Springer Nature Link
link.springer.com
This engine translates genetic information into biological meaning.
We need to connect:
Gene → Protein/Enzyme → Reaction → Compound → Pathway
For example, the system should distinguish:
The enzymes associated with the host plant's flavonoid production.
The donor plant's diterpenoid biosynthesis.
Their shared precursor metabolism.
Their distinct downstream pathways.
The biological steps that remain unknown.
Use NetworkX for the first version of the graph. You can later move to Neo4j if needed.
Every graph relationship should have a source and evidence classification.
Deliverable: An interactive metabolic pathway graph with links back to the scientific evidence.
5. Build Engine 4 – GeneBridge AI
Main AI innovation
This should be one of the most important parts of the project.
GeneBridge will analyze the data generated by the previous engines.
It will answer questions such as:
Which donor genes have relevant evidence?
Which host genes are related?
What metabolic dependencies exist?
Which genetic characteristics are potentially compatible?
What important information is missing?
What are the main scientific limitations?
I recommend combining two approaches.
A. Comparative analysis engine
Use the actual genomic data and transparent computational methods.
B. Literature intelligence using RAG
Use scientific literature to retrieve relevant findings.
The RAG system should:
Retrieve relevant scientific papers.
Extract information about genes and their functions.
Connect findings to the genomic data.
Retain PMID/DOI references.
Present evidence and uncertainty.
The important part is that the AI cannot make up gene functions or invent experimental results.
Gene compatibility assessment
The system should produce an assessment containing:
Assessment
Example output
Sequence relationship
Related / weakly related / unknown
Functional evidence
Experimentally characterized / predicted
Pathway completeness
Supported / incomplete / unknown
Expression compatibility
Supporting / conflicting / unavailable
Genomic context
Characterized / uncertain

It then generates a clear explanation of whether a candidate deserves further investigation.
Don't use arbitrary percentages such as "95% genetic compatibility." We don't have the experimental data to justify that.
Deliverable: An AI-assisted research engine that produces explainable gene and pathway assessments.
6. Build Engine 5 – CRISPR Scenario Simulator
AI for CRISPR Screen Analysis in Functional Genomics | Technology Networks
technologynetworks.com
This is where the user interacts with the proposed engineering scenarios.
The simulator needs two scenario types:
Scenario A – Host gene modification
Explore how a hypothetical modification to a documented host gene could affect its associated pathway.
Scenario B – Donor gene integration
Explore a hypothetical scenario in which a selected donor genetic characteristic is introduced into the host genome.
The simulator will use the results from GeneBridge, not invent its own biological facts.
Its output should include:
Selected host plant.
Selected donor plant.
Candidate gene and chromosome location.
Documented biological function.
Relevant metabolic pathway.
Hypothetical engineering scenario.
Predicted qualitative consequences.
Potential compatibility issues.
Evidence and limitations.
For example, the user could select the SbarKPS1 candidate and inspect how its documented function compares with SbaiKPS1 in the host.
The application would then explain what the hypothetical integration might change, what additional pathway components may be necessary and what cannot currently be predicted.
The hackathon deliverable is a computational simulation, not actual CRISPR editing or a validated engineered organism.
Deliverable: A working virtual genetic-engineering scenario generator.
7. Build the actual web application
Now all five engines need a user interface.
I recommend six main screens.
Screen 1 – Dashboard
Olink Insight :: Behance
behance.net
Overview of both species, genome availability, research status and generated scenarios.
Screen 2 – Genome Explorer
Rice-Map: a new-generation rice genome browser | BMC Genomics | Springer Nature Link
link.springer.com
Interactive chromosome maps, gene locations and genomic annotations.
Screen 3 – GeneBridge
Aligning genomic regions, demo
training.ensembl.org
Side-by-side gene comparison, gene relationships and evidence assessments.
Screen 4 – Pathway Explorer
GraphOmics: an interactive platform to explore and integrate multi-omics data | BMC Bioinformatics | Springer Nature Link
link.springer.com
Visual connections between genes, enzymes and natural compounds.
Screen 5 – CRISPR Studio
Helix Studio - The Genome IDE for CRISPR & Prime Editing
helix-studio.com
Select the hypothetical engineering scenario and generate its computational assessment.
Screen 6 – Virtual Plant Report
Biologia Sintética: O que é, Como Funciona e Aplicações da Tecnologia
nexxant.com.br
Show the proposed virtual engineered plant, its predicted natural-product profile, scientific evidence and unresolved limitations.
8. Recommended technical stack
I would use the following technologies:
Layer
Technology
Frontend
React + TypeScript
Styling
Tailwind CSS
Backend
Python + FastAPI
Genome processing
Biopython
Sequence comparison
BLAST+
Data manipulation
Pandas
Pathway networks
NetworkX
Chemical information
RDKit + PubChem
AI / literature
RAG + LLM
Vector search
FAISS or pgvector
Database
PostgreSQL
Visualization
Plotly + Cytoscape.js
Deployment
AWS

For deployment, a practical architecture would be:
React frontend on S3 + CloudFront.
FastAPI backend using Docker on AWS ECS Fargate.
PostgreSQL for structured scientific metadata.
S3 for genome and annotation files.
For the hackathon, run everything locally with Docker Compose first. Deploy to AWS only once the prototype works.
9. Suggested database structure
Keep the data model relatively simple.
Table
Contents
species
Plant information
genome_assemblies
Assembly references
chromosomes
Chromosome metadata
genes
Gene IDs, positions, annotations
gene_comparisons
Relationships between candidate genes
pathways
Metabolic pathways
compounds
Natural compounds
evidence
Publication references and findings
crispr_scenarios
Hypothetical engineering scenarios
scenario_results
Simulation outputs and limitations

One important design principle: every scientific finding in the application should be traceable to its source.
10. End-to-end implementation schedule
Your deadline is 8 November 2026 at 10:00 AM GMT+1. That gives the team approximately six days from November 2.
I would organize the work as follows.
Six-day execution plan
November 2 – Scientific scope
Scientific
Finalize both plant species.
Define the research question.
Select the primary metabolic pathway.
Collect the relevant publications.
Identify the candidate genes.
Output: Scientific research foundation.
November 3 – Genome data
Scientific + technical
Obtain genome assemblies.
Obtain FASTA, GFF3 and protein files.
Map chromosomes.
Prepare the gene dataset.
Output: Two processed genome datasets.
November 4 – Comparative genomics
Technical
Implement gene comparison.
Analyze candidate relationships.
Map relevant genes to chromosomes.
Build the first comparison tables.
Output: Working comparative genomics engine.
November 5 – Pathway and AI
Technical
Build the gene-to-compound graph.
Integrate scientific evidence.
Implement GeneBridge.
Generate compatibility assessments.
Output: Working pathway and AI analysis.
November 6 – CRISPR simulator
Technical
Implement both hypothetical scenarios.
Connect the simulator to GeneBridge.
Generate virtual engineering reports.
Connect FastAPI with the frontend.
Output: Working computational CRISPR prototype.
November 7 – Product and presentation
Final integration
Finish the six application screens.
Test the complete demonstration.
Finish GitHub README and documentation.
Record the pitch video.
Prepare the 10-slide presentation.
Output: Complete hackathon submission.
November 8 – Submission
Final deadline
Final checks and submission before 10:00 AM GMT+1.
11. How I would divide the work across your team
For a team of four or five, I recommend splitting responsibilities by expertise.
Person
Responsibility
Main deliverable
1
Scientific research
Plant biology, pathways, genes and publications
2
Bioinformatics
Genome ingestion, chromosomes and gene comparisons
3
AI / Backend
GeneBridge, RAG and CRISPR scenario engine
4
Frontend
React application and interactive visualizations
5
Integration / Research validation
Testing, scientific verification, documentation and pitch

If you have only two or three members, combine scientific research with bioinformatics, and backend with AI.
Everyone should understand the central scientific hypothesis, even if they work on different components.
12. What must actually work in the final demonstration?
This is the most important scope decision.
You do not have time to create a complete automated biotechnology research platform. Instead, build one convincing end-to-end use case.
Final prototype acceptance criteria
The following should all work when the judges test the application.
Prototype checklist
0/10
Load real genomic data from both medicinal plants
Display chromosome information and relevant gene locations
Compare at least one scientifically documented candidate gene relationship
Visualize the associated metabolic pathways
Show scientific references supporting the selected genes
Run a hypothetical CRISPR host-modification scenario
Run a hypothetical donor-gene integration scenario
Generate an evidence-based virtual plant report
Explain limitations and unresolved biological questions
Provide a reproducible public GitHub repository
13. What not to spend time on
For this particular deadline, I would avoid:
Training a new biological machine-learning model from scratch.
Downloading and processing enormous raw sequencing datasets when assembled genomes are available.
Building a generic AI chatbot.
Attempting to integrate entire chromosomes.
Claiming that a virtual plant has been genetically engineered.
Claiming improved medicinal effectiveness without experimental evidence.
Spending days perfecting frontend animations before the genomic analysis works.
A transparent computational model backed by published research is much stronger than an impressive-looking interface with unsupported predictions.
14. Final project definition
This is how I would summarize the whole project to your team.
PhytoFusion AI
Cross-Species Genetic Engineering Intelligence
Exploring the future of medicinal plants through comparative genomics, artificial intelligence and CRISPR.
Scientific foundation
Investigate genetic and metabolic characteristics of Scutellaria baicalensis and Scutellaria barbata, focusing on the potential integration of a selected donor genetic characteristic into a host plant.
Technical innovation
An AI-powered platform combining chromosome visualization, comparative genomics, metabolic pathway analysis, evidence retrieval and computational CRISPR scenario simulation.
Final outcome
A virtual genetically engineered plant design accompanied by a scientific feasibility assessment, predicted natural-product characteristics, evidence references and biological limitations.
My strongest recommendation: build the project around one scientific case study
Don't try to demonstrate that every gene from one herb can be transferred to another.
Build one deep case study around the Scutellaria pair:
S. baicalensis as the host + S. barbata as the donor → KPS gene-family comparison → hypothetical genetic integration → predicted diterpenoid pathway consequences.
Retain the host's flavonoid pathway as part of its baseline natural-product profile.
This gives you a coherent story:
We have two medicinal plants with different natural-product characteristics.
We investigate their chromosomes and genomes.
We identify candidate genes that may explain those differences.
We use comparative genomics and AI to evaluate their biological relationships.
We simulate a hypothetical CRISPR-assisted genetic integration.
We investigate what the resulting plant's natural-product profile could theoretically look like.
The real innovation is GeneBridge: a system that connects genomic evidence with hypothetical CRISPR engineering and natural-product discovery.
That is the component I would put at the center of your hackathon submission and pitch.


