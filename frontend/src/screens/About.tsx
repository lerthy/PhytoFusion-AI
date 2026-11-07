import { Icon } from "../components/Icon";

interface Props {
  onStart: () => void;
}

const STEPS = [
  { n: 1, title: "Look at the genomes", text: "Open the two plants and see where the genes you care about sit on their chromosomes." },
  { n: 2, title: "Compare genes", text: "Find the host gene most like a donor gene, and see how well that match is supported." },
  { n: 3, title: "Try a scenario", text: "Explore a hypothetical gene transfer, with what it could mean and what is still unknown." },
];

// Illustrative bar heights (not real chromosome lengths). Only the counts, 13 and 9, are real.
const DONOR = [150, 142, 136, 128, 122, 118, 110, 104, 96, 90, 82, 74, 66];
const HOST = [170, 156, 146, 134, 124, 112, 100, 88, 76];
const BAR = 12, GAP = 7, TOP = 70, DONOR_X = 8, HOST_X = 348;
const barX = (start: number, i: number) => start + i * (BAR + GAP);

/** A karyogram-style schematic of the case study. Motion (one sequence, on load): the chromosomes grow in,
 *  then a dot carries the gene along the dashed route while the host's open slot breathes. */
function HeroFigure() {
  const donorGene = 3, hostSlot = 4;
  const x1 = barX(DONOR_X, donorGene) + BAR / 2, x2 = barX(HOST_X, hostSlot) + BAR / 2;
  const route = `M${x1} ${TOP - 4}C${x1} 6 ${x2} 6 ${x2} ${TOP - 6}`;
  const delay = (i: number) => ({ animationDelay: `${i * 55}ms` });
  return (
    <figure className="fig">
      <svg viewBox="0 0 520 290" role="img" aria-label="Schematic: the donor plant has 13 chromosomes, the host plant has 9. One donor gene is shown moving toward a host chromosome.">
        {DONOR.map((h, i) => <rect key={`d${i}`} className="fig-bar donor" style={delay(i)} x={barX(DONOR_X, i)} y={TOP} width={BAR} height={h} rx={6} />)}
        {HOST.map((h, i) => <rect key={`h${i}`} className="fig-bar host" style={delay(i + 4)} x={barX(HOST_X, i)} y={TOP} width={BAR} height={h} rx={6} />)}
        <rect className="fig-gene" x={barX(DONOR_X, donorGene)} y={TOP + 38} width={BAR} height={9} rx={2} />
        <rect className="fig-slot" x={barX(HOST_X, hostSlot) - 2} y={TOP + 52} width={BAR + 4} height={13} rx={3} />
        <path className="fig-route" d={route} />
        <path className="fig-arrow" d={`M${x2 - 5} ${TOP - 14}L${x2} ${TOP - 5}L${x2 + 5} ${TOP - 14}`} />
        <circle className="fig-dot" r="5" style={{ offsetPath: `path("${route}")` }} />
        <text className="fig-label" x={DONOR_X} y="272" textAnchor="start"><tspan fontStyle="italic">S. barbata</tspan> · 13 chromosomes</text>
        <text className="fig-label" x={HOST_X + 164} y="272" textAnchor="end"><tspan fontStyle="italic">S. baicalensis</tspan> · 9 chromosomes</text>
        <text className="fig-role" x={DONOR_X} y="24">Donor</text>
        <text className="fig-role" x={HOST_X + 164} y="24" textAnchor="end">Host</text>
      </svg>
      <figcaption>Schematic. The chromosome counts are real; bar lengths and the gene’s position are only illustrative.</figcaption>
    </figure>
  );
}

/** The front door: what this is, how it works, what it will not claim. Then one button into the app. */
export function About({ onStart }: Props) {
  return (
    <div className="landing">
      <header className="landing-top">
        <div className="landing-top-in">
          <span className="brand"><span className="logo"><Icon name="dna" size={24} /></span>PhytoFusion AI</span>
          <button className="btn secondary" onClick={onStart}>Open the app</button>
        </div>
      </header>

      <main id="content">
        <section className="hero" aria-labelledby="page-title">
          <div className="wrap hero-grid">
            <div className="hero-copy">
              <h1 id="page-title" tabIndex={-1}>Explore, on paper, what moving a gene between two medicinal plants could mean</h1>
              <p className="lead">
                PhytoFusion AI compares the genes of two related medicinal plants and helps you reason about a
                hypothetical CRISPR gene transfer: what the evidence supports, and what is still unknown.
              </p>
              <div className="row">
                <button className="btn accent big-btn" onClick={onStart}>Open the app</button>
                <a className="btn secondary big-btn" href="#how">How it works</a>
              </div>
            </div>
            <HeroFigure />
          </div>
        </section>

        <section className="band" aria-labelledby="idea">
          <div className="wrap">
            <h2 id="idea">The case study</h2>
            <div className="species">
              <article className="species-card host">
                <p className="role">Host · would receive the gene</p>
                <h3><em>Scutellaria baicalensis</em></h3>
                <p className="common">Chinese skullcap</p>
                <p className="count"><span>9</span> chromosomes</p>
                <p>Known for flavonoids such as baicalein, baicalin and wogonin.</p>
              </article>
              <article className="species-card donor">
                <p className="role">Donor · where the gene comes from</p>
                <h3><em>Scutellaria barbata</em></h3>
                <p className="common">Barbed skullcap</p>
                <p className="count"><span>13</span> chromosomes</p>
                <p>Known for clerodane diterpenoids.</p>
              </article>
            </div>
            <p className="prose">
              The question is a careful one: could a gene linked to diterpenoid production in <em>S. barbata</em> be
              added, in theory, to <em>S. baicalensis</em> without losing what the host already makes? The two plants
              organise their genes on different numbers of chromosomes, which is why compatibility has to be checked
              gene by gene. Published genomes exist for both, so the comparison uses real data.
            </p>
          </div>
        </section>

        <section className="wrap section" id="how" aria-labelledby="how-title">
          <h2 id="how-title">How it works</h2>
          <ol className="timeline">
            {STEPS.map((s) => (
              <li key={s.n}>
                <span className="dot" aria-hidden="true">{s.n}</span>
                <h3>{s.title}</h3>
                <p>{s.text}</p>
              </li>
            ))}
          </ol>
        </section>

        <section className="band" aria-labelledby="honest">
          <div className="wrap">
            <h2 id="honest">Honest by design</h2>
            <div className="plain-cols">
              <div className="honest do">
                <h3><Icon name="check" />What it does</h3>
                <ul>
                  <li>Ties every finding to a published source (a PMID or DOI).</li>
                  <li>Says “unknown” when something is unknown, and lists what is missing.</li>
                  <li>Rates support as strong, moderate or limited, never as a score.</li>
                </ul>
              </div>
              <div className="honest dont">
                <h3><Icon name="alert" />What it is not</h3>
                <ul>
                  <li>It does not edit any genome. No engineered plant exists.</li>
                  <li>It does not predict that a transfer would work.</li>
                  <li>It makes no claim about how well a medicine would work. That needs lab evidence.</li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        <section className="wrap section" aria-labelledby="ready">
          <div className="cta">
            <div>
              <h2 id="ready">Ready to look?</h2>
              <p>It takes three steps, and you can stop at any of them.</p>
            </div>
            <button className="btn accent big-btn" onClick={onStart}>Open the app</button>
          </div>
        </section>
      </main>

      <footer className="landing-foot">Built for EthnoHack, Track 2. Hypothetical, computational scenarios only.</footer>
    </div>
  );
}
