import { useEffect, useRef, useState } from "react";

// Illustrative bar heights (not real chromosome lengths). Only the counts, 13 and 9, are real.
const DONOR = [150, 142, 136, 128, 122, 118, 110, 104, 96, 90, 82, 74, 66];
const HOST = [170, 156, 146, 134, 124, 112, 100, 88, 76];
const BAR = 12, GAP = 7, TOP = 70, DONOR_X = 8, HOST_X = 348, GENE_AT = 3, SLOT_AT = 4;
const barX = (start: number, i: number) => start + i * (BAR + GAP);

const CHAPTERS = [
  { title: "Two plants, two genomes", text: "Scutellaria barbata keeps its genes on 13 chromosomes, Scutellaria baicalensis on 9. Published genomes exist for both, so the comparison uses real data." },
  { title: "Find the gene that matters", text: "A donor gene linked to diterpenoid production, such as a KPS gene, sits at a known position on one chromosome." },
  { title: "Ask what a transfer could mean", text: "In theory that gene could be added to the host. Where it would go is not chosen and nothing is edited. The app shows what the evidence supports and what is still unknown." },
];

const seg = (p: number, a: number, b: number) => Math.min(1, Math.max(0, (p - a) / (b - a)));

/**
 * The one scroll-driven moment on the About page: as you scroll through this section the chromosomes
 * grow, a donor gene lights up, then a dashed route draws to an open slot on the host.
 * Under reduced motion the section is not pinned and shows its final state.
 */
export function GeneJourney() {
  const section = useRef<HTMLElement>(null);
  const stage = useRef<HTMLDivElement>(null);
  const donorCount = useRef<SVGTSpanElement>(null);
  const hostCount = useRef<SVGTSpanElement>(null);
  const [chapter, setChapter] = useState(0);
  const [still, setStill] = useState(false);

  useEffect(() => {
    const el = section.current, st = stage.current;
    if (!el || !st) return;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let current = -1;
    let raf = 0;

    const apply = (p: number) => {
      const p1 = seg(p, 0, 0.3), p2 = seg(p, 0.3, 0.55), p3 = seg(p, 0.55, 0.95);
      st.style.setProperty("--p1", String(p1));
      st.style.setProperty("--p2", String(p2));
      st.style.setProperty("--p3", String(p3));
      if (donorCount.current) donorCount.current.textContent = String(Math.round(13 * p1));
      if (hostCount.current) hostCount.current.textContent = String(Math.round(9 * p1));
      const next = p < 0.3 ? 0 : p < 0.55 ? 1 : 2;
      if (next !== current) { current = next; setChapter(next); }
    };

    if (reduce) {
      setStill(true);
      apply(1);
      return;
    }
    const update = () => {
      raf = 0;
      const header = parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--landing-header-h")) || 64;
      const rect = el.getBoundingClientRect();
      const travel = rect.height - st.offsetHeight;
      apply(travel > 0 ? Math.min(1, Math.max(0, (header - rect.top) / travel)) : 1);
    };
    const onScroll = () => { if (!raf) raf = requestAnimationFrame(update); };
    update();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
      if (raf) cancelAnimationFrame(raf);
    };
  }, []);

  const x1 = barX(DONOR_X, GENE_AT) + BAR / 2, x2 = barX(HOST_X, SLOT_AT) + BAR / 2;
  const route = `M${x1} ${TOP - 4}C${x1} 6 ${x2} 6 ${x2} ${TOP - 6}`;

  return (
    <section ref={section} id="how" className={`journey-story ${still ? "still" : ""}`} aria-labelledby="how-title">
      <div ref={stage} className="journey-stage">
        <div className="journey-copy">
          <h2 id="how-title">How it works</h2>
          <ol className="journey-caps">
            {CHAPTERS.map((c, i) => (
              <li key={c.title} className={i === chapter ? "on" : ""} aria-current={i === chapter ? "step" : undefined}>
                <span className="cap-n" aria-hidden="true">{i + 1}</span>
                <h3>{c.title}</h3>
                <p>{c.text}</p>
              </li>
            ))}
          </ol>
          <div className="journey-dots" aria-hidden="true">
            {CHAPTERS.map((c, i) => <i key={c.title} className={i <= chapter ? "on" : ""} />)}
          </div>
        </div>

        <figure className="journey-fig">
          <svg viewBox="0 0 520 290" role="img" aria-label="Schematic: the donor plant has 13 chromosomes and the host plant 9. One donor gene is shown, then a dashed route to an open slot on a host chromosome, with the insertion site not chosen.">
            <defs>
              <mask id="journey-route-mask" maskUnits="userSpaceOnUse" x="0" y="0" width="520" height="290">
                <path d={route} pathLength={1} fill="none" stroke="white" strokeWidth="8" strokeDasharray="1" style={{ strokeDashoffset: "calc(1 - var(--p3, 0))" }} />
              </mask>
            </defs>
            {DONOR.map((h, i) => <rect key={`d${i}`} className="fig-bar donor g-bar" x={barX(DONOR_X, i)} y={TOP} width={BAR} height={h} rx={6} />)}
            {HOST.map((h, i) => <rect key={`h${i}`} className="fig-bar host g-bar" x={barX(HOST_X, i)} y={TOP} width={BAR} height={h} rx={6} />)}
            <rect className="fig-gene g-gene" x={barX(DONOR_X, GENE_AT)} y={TOP + 38} width={BAR} height={9} rx={2} />
            <rect className="fig-slot g-slot" x={barX(HOST_X, SLOT_AT) - 2} y={TOP + 52} width={BAR + 4} height={13} rx={3} />
            <path className="fig-route" d={route} mask="url(#journey-route-mask)" />
            <path className="fig-arrow g-arrow" d={`M${x2 - 5} ${TOP - 14}L${x2} ${TOP - 5}L${x2 + 5} ${TOP - 14}`} />
            <circle className="fig-dot g-dot" r="5" style={{ offsetPath: `path("${route}")` }} />
            <text className="fig-label" x={DONOR_X} y="272"><tspan fontStyle="italic">S. barbata</tspan> · <tspan ref={donorCount}>13</tspan> chromosomes</text>
            <text className="fig-label" x={HOST_X + 164} y="272" textAnchor="end"><tspan fontStyle="italic">S. baicalensis</tspan> · <tspan ref={hostCount}>9</tspan> chromosomes</text>
            <text className="fig-role" x={DONOR_X} y="24">Donor</text>
            <text className="fig-role" x={HOST_X + 164} y="24" textAnchor="end">Host</text>
          </svg>
          <ul className="journey-legend">
            <li className="lg-gene"><i aria-hidden="true" />One KPS gene on a donor chromosome</li>
            <li className="lg-slot"><i aria-hidden="true" />Insertion site: not chosen</li>
          </ul>
          <p className="journey-note">Schematic. The chromosome counts are real; bar lengths and positions are illustrative.</p>
        </figure>
      </div>
    </section>
  );
}
