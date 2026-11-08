import { lazy, Suspense, useState } from "react";
import { GeneJourney } from "../components/GeneJourney";
import { Icon } from "../components/Icon";

const HeroHelix = lazy(() => import("../components/HeroHelix"));

interface Props {
  onStart: () => void;
}

const LINES = ["Explore, on paper,", "what moving a gene", "between two medicinal", "plants could mean"];

// Illustrative bar heights (not real chromosome lengths). Only the counts, 9 and 13, are real.
const HOST_BARS = [38, 35, 32, 30, 27, 24, 21, 19, 16];
const DONOR_BARS = [38, 36, 34, 32, 30, 28, 26, 24, 22, 20, 18, 16, 14];

function ChromRow({ bars, label }: { bars: number[]; label: string }) {
  return (
    <svg className="chrom-row" viewBox={`0 0 ${bars.length * 16} 40`} role="img" aria-label={label}>
      {bars.map((h, i) => <rect key={i} x={i * 16} y={40 - h} width={9} height={h} rx={4.5} />)}
    </svg>
  );
}

const DOES = [
  "Ties every finding to a published source (a PMID or DOI).",
  "Says “unknown” when something is unknown, and lists what is missing.",
  "Rates support as strong, moderate or limited, never as a score.",
];
const DOES_NOT = [
  "It does not edit any genome. No engineered plant exists.",
  "It does not predict that a transfer would work.",
  "It makes no claim about how well a medicine would work. That needs lab evidence.",
];

/** The front door: what this is, how it works, what it will not claim. Then one button into the app. */
export function About({ onStart }: Props) {
  const [paused, setPaused] = useState(false);
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
              <h1 id="page-title" tabIndex={-1}>
                {LINES.map((line, i) => (
                  <span key={line} className="line"><span style={{ animationDelay: `${120 + i * 90}ms` }}>{line}</span></span>
                ))}
              </h1>
              <p className="lead">
                PhytoFusion AI compares the genes of two related medicinal plants and helps you reason about a
                hypothetical CRISPR gene transfer: what the evidence supports, and what is still unknown.
              </p>
              <div className="row">
                <button className="btn accent big-btn" onClick={onStart}>Open the app</button>
                <a className="btn ghost big-btn" href="#how">See how it works</a>
              </div>
              <p className="hero-note">Free to try. Nothing is edited or built.</p>
            </div>
            <div className="hero-visual">
              <Suspense fallback={<div className="hero-helix" aria-hidden="true" />}>
                <HeroHelix paused={paused} />
              </Suspense>
              <button className="hero-pause" aria-pressed={paused} onClick={() => setPaused((v) => !v)}>
                {paused ? "Play motion" : "Pause motion"}
              </button>
            </div>
          </div>
        </section>

        <GeneJourney />

        <section className="case" aria-labelledby="idea">
          <div className="wrap">
            <h2 id="idea">Two skullcaps, one careful question</h2>
            <div className="spread">
              <article className="sp host">
                <p className="role">Host · would receive the gene</p>
                <h3>Scutellaria baicalensis</h3>
                <p className="common">Chinese skullcap</p>
                <p className="count"><b>9</b><span>chromosomes</span></p>
                <ChromRow bars={HOST_BARS} label="Nine chromosomes" />
                <p className="blurb">Known for flavonoids such as</p>
                <ul className="chips" aria-label="Compounds it is known for"><li>baicalein</li><li>baicalin</li><li>wogonin</li></ul>
              </article>
              <article className="sp donor">
                <p className="role">Donor · where the gene comes from</p>
                <h3>Scutellaria barbata</h3>
                <p className="common">Barbed skullcap</p>
                <p className="count"><b>13</b><span>chromosomes</span></p>
                <ChromRow bars={DONOR_BARS} label="Thirteen chromosomes" />
                <p className="blurb">Known for</p>
                <ul className="chips" aria-label="Compounds it is known for"><li>clerodane diterpenoids</li></ul>
              </article>
            </div>
            <div className="question">
              <h3>Could a gene linked to diterpenoid production in <em>S. barbata</em> be added, in theory, to <em>S. baicalensis</em> without losing what the host already makes?</h3>
              <p>The two plants organise their genes on different numbers of chromosomes, which is why compatibility has to be checked gene by gene.</p>
            </div>
          </div>
        </section>

        <section className="honest-sec" aria-labelledby="honest">
          <div className="wrap">
            <h2 id="honest">Honest by design</h2>
            <div className="promises">
              <div className="do">
                <h3>What it does</h3>
                <ul>{DOES.map((t) => <li key={t}><span className="ic"><Icon name="check" size={18} /></span><span>{t}</span></li>)}</ul>
              </div>
              <div className="dont">
                <h3>What it is not</h3>
                <ul>{DOES_NOT.map((t) => <li key={t}><span className="ic"><Icon name="x" size={18} /></span><span>{t}</span></li>)}</ul>
              </div>
            </div>
          </div>
        </section>

        <section className="closer" aria-labelledby="ready">
          <div className="wrap closer-in">
            <div>
              <h2 id="ready">Ready to look?</h2>
              <p>It takes three steps, and you can stop at any of them.</p>
            </div>
            <button className="btn accent big-btn" onClick={onStart}>Open the app</button>
          </div>
        </section>
      </main>

      <footer className="landing-foot">
        <div className="foot-in">
          <div>
            <p className="foot-brand"><span className="logo"><Icon name="dna" size={22} /></span>PhytoFusion AI</p>
            <p className="made">Made by <strong>Lerdi Salihi</strong> and <strong>Edina Suma</strong></p>
          </div>
          <p className="foot-note">Built for EthnoHack, Track 2. Hypothetical, computational scenarios only.</p>
        </div>
      </footer>
    </div>
  );
}
