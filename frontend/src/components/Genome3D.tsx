import { useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import type { GeneRecord } from "../gff3";
import { bpPerDisplayedTurn, geneT, helixPoint, turnsFor, type HelixShape } from "../helix";
import { binCounts, DENSE_GENES_PER_SEQUENCE, formatBp, groupByChromosome, mainSequences } from "../mapScale";
import { Alert, Field } from "./ui";

interface Props {
  lengths: Record<string, number>;
  genes: GeneRecord[];
  hits: Set<string>;
  names?: Record<string, string>;
  label: string;
}

const HEIGHT = 380;
const HIT_PX = 10;
const BINS = 160; // density windows along the chromosome
const css = (name: string) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

/**
 * A chromosome drawn as a double helix with its genes as beads.
 * Position along the helix is real and to scale. The twist is decorative (one turn is many Mb).
 * Rendered on demand, never auto-spinning. The 2D map and the gene table hold the same data.
 */
export default function Genome3D({ lengths, genes, hits, names = {}, label }: Props) {
  const mount = useRef<HTMLDivElement>(null);
  const { main } = useMemo(() => mainSequences(lengths), [lengths]);
  const choices = useMemo(() => [...main].sort((a, b) => lengths[b] - lengths[a]), [main, lengths]);
  const [chr, setChr] = useState(choices[0] ?? "");
  const [tip, setTip] = useState<{ gene: GeneRecord; x: number; y: number } | null>(null);
  const [noGl, setNoGl] = useState(false);
  const [themeTick, setThemeTick] = useState(0);
  const byChr = useMemo(() => groupByChromosome(genes), [genes]);

  const current = choices.includes(chr) ? chr : (choices[0] ?? "");
  const length = lengths[current] ?? 1;
  const list = byChr.get(current) ?? [];
  const turns = turnsFor(length);
  const dense = list.length > DENSE_GENES_PER_SEQUENCE;
  const nameOf = (id: string) => names[id] ?? id;

  // Re-read the colour tokens when the OS theme changes.
  useEffect(() => {
    const query = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = () => setThemeTick((n) => n + 1);
    query.addEventListener("change", onChange);
    return () => query.removeEventListener("change", onChange);
  }, []);

  useEffect(() => {
    const host = mount.current;
    if (!host || !current) return;
    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    } catch {
      setNoGl(true);
      return;
    }
    setNoGl(false);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    host.appendChild(renderer.domElement);
    const canvas = renderer.domElement;
    canvas.tabIndex = 0;
    canvas.setAttribute("role", "img");
    canvas.setAttribute("aria-label", `3D helix of ${nameOf(current)} with ${list.length} genes. Drag to rotate, scroll to zoom. The gene table lists the same genes.`);
    canvas.style.display = "block";
    canvas.style.touchAction = "none";

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(38, 1, 0.1, 100);
    camera.position.set(0, 6, 15);
    const controls = new OrbitControls(camera, canvas);
    controls.enableDamping = false;
    controls.minDistance = 4;
    controls.maxDistance = 30;
    controls.listenToKeyEvents(canvas);
    scene.add(new THREE.AmbientLight(0xffffff, 1.1));
    const sun = new THREE.DirectionalLight(0xffffff, 1.6);
    sun.position.set(5, 8, 6);
    scene.add(sun);

    const shape: HelixShape = { height: 11, turns, radius: 1.35 };
    const strandColor = new THREE.Color(css("--border-strong"));
    const geometries: THREE.BufferGeometry[] = [];
    const materials: THREE.Material[] = [];
    const own = <T extends THREE.BufferGeometry | THREE.Material>(x: T): T => {
      (x instanceof THREE.BufferGeometry ? geometries : materials).push(x as never);
      return x;
    };

    const samples = Math.max(240, turns * 48);
    for (const strand of [0, 1] as const) {
      const pts = Array.from({ length: samples + 1 }, (_, i) => new THREE.Vector3(...helixPoint(i / samples, strand, shape)));
      const geometry = own(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), samples, 0.07, 8, false));
      let colored = false;
      if (strand === 0 && dense) {
        // Colour the strand by gene density (one hue, light to dark) instead of drawing thousands of beads.
        const counts = binCounts(list, length, BINS), top = Math.max(1, ...counts);
        const ring = 9; // radial segments + 1 vertices per ring
        const colors = new Float32Array(geometry.attributes.position.count * 3);
        const full = new THREE.Color(css("--viz-1")), base = full.clone().lerp(new THREE.Color(css("--surface-2")), 0.82), mix = new THREE.Color();
        for (let i = 0; i <= samples; i++) {
          mix.copy(base).lerp(full, counts[Math.min(BINS - 1, Math.floor((i / samples) * BINS))] / top);
          for (let j = 0; j < ring; j++) mix.toArray(colors, (i * ring + j) * 3);
        }
        geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
        colored = true;
      }
      scene.add(new THREE.Mesh(geometry, own(new THREE.MeshStandardMaterial({ color: colored ? 0xffffff : strandColor, vertexColors: colored, roughness: 0.6 }))));
    }
    const rungs: number[] = [];
    for (let i = 0; i <= turns * 9; i++) {
      const t = i / (turns * 9);
      rungs.push(...helixPoint(t, 0, shape), ...helixPoint(t, 1, shape));
    }
    const rungGeometry = own(new THREE.BufferGeometry());
    rungGeometry.setAttribute("position", new THREE.Float32BufferAttribute(rungs, 3));
    scene.add(new THREE.LineSegments(rungGeometry, own(new THREE.LineBasicMaterial({ color: strandColor, transparent: true, opacity: 0.45 }))));

    // Genes: one instanced mesh. Search matches are larger and use the second colour.
    const positions = list.map((g) => new THREE.Vector3(...helixPoint(geneT(g, length), 0, { ...shape, radius: shape.radius * 1.14 })));
    const drawn = [...list.keys()].filter((i) => !dense || hits.has(list[i].geneId));
    const beads = new THREE.InstancedMesh(own(new THREE.SphereGeometry(0.085, 10, 8)), own(new THREE.MeshStandardMaterial({ roughness: 0.4 })), Math.max(1, drawn.length));
    const matrix = new THREE.Matrix4(), c1 = new THREE.Color(css("--viz-1")), c2 = new THREE.Color(css("--viz-2"));
    drawn.forEach((gi, k) => {
      const hit = hits.has(list[gi].geneId);
      matrix.compose(positions[gi], new THREE.Quaternion(), new THREE.Vector3().setScalar(hit ? 2.2 : 1));
      beads.setMatrixAt(k, matrix);
      beads.setColorAt(k, hit ? c2 : c1);
    });
    beads.count = drawn.length;
    beads.instanceMatrix.needsUpdate = true;
    if (beads.instanceColor) beads.instanceColor.needsUpdate = true;
    scene.add(beads);

    const marker = new THREE.Mesh(own(new THREE.SphereGeometry(0.17, 14, 10)), own(new THREE.MeshBasicMaterial({ color: new THREE.Color(css("--text")) })));
    marker.visible = false;
    scene.add(marker);

    const render = () => renderer.render(scene, camera);
    controls.addEventListener("change", render);
    const resize = () => {
      const w = Math.max(240, host.clientWidth);
      renderer.setSize(w, HEIGHT);
      camera.aspect = w / HEIGHT;
      camera.updateProjectionMatrix();
      render();
    };
    const observer = new ResizeObserver(resize);
    observer.observe(host);
    resize();

    // Hover: nearest gene on screen within HIT_PX, so the target is bigger than the bead.
    let frame = 0, last = -1;
    const probe = new THREE.Vector3();
    const onMove = (e: PointerEvent) => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => {
        const box = canvas.getBoundingClientRect();
        const px = e.clientX - box.left, py = e.clientY - box.top;
        let best = -1, bestDist = HIT_PX, bestDepth = Infinity;
        for (let i = 0; i < positions.length; i++) {
          probe.copy(positions[i]).project(camera);
          if (probe.z > 1) continue;
          const d = Math.hypot((probe.x * 0.5 + 0.5) * box.width - px, (-probe.y * 0.5 + 0.5) * box.height - py);
          if (d < bestDist || (d <= bestDist && probe.z < bestDepth)) { best = i; bestDist = d; bestDepth = probe.z; }
        }
        setTip(best >= 0 ? { gene: list[best], x: Math.min(Math.max(px, 110), box.width - 110), y: py } : null);
        if (best !== last) {
          last = best;
          marker.visible = best >= 0;
          if (best >= 0) marker.position.copy(positions[best]);
          render();
        }
      });
    };
    const onLeave = () => { setTip(null); last = -1; marker.visible = false; render(); };
    canvas.addEventListener("pointermove", onMove);
    canvas.addEventListener("pointerleave", onLeave);

    return () => {
      cancelAnimationFrame(frame);
      canvas.removeEventListener("pointermove", onMove);
      canvas.removeEventListener("pointerleave", onLeave);
      observer.disconnect();
      controls.removeEventListener("change", render);
      controls.dispose();
      beads.dispose();
      geometries.forEach((g) => g.dispose());
      materials.forEach((m) => m.dispose());
      renderer.dispose();
      canvas.remove();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [current, list, hits, dense, themeTick]);

  if (noGl) return <Alert kind="warn" title="3D is not available here">This browser cannot draw 3D graphics. The 2D map and the table show the same genes.</Alert>;

  return (
    <div className="g3d">
      <Field label="Chromosome">
        {(a) => (
          <select {...a} value={current} onChange={(e) => { setChr(e.target.value); setTip(null); }}>
            {choices.map((c) => <option key={c} value={c}>{nameOf(c)} · {formatBp(lengths[c])} · {(byChr.get(c)?.length ?? 0).toLocaleString()} genes</option>)}
          </select>
        )}
      </Field>
      <div className="g3d-stage" style={{ height: HEIGHT }} ref={mount}>
        {tip && (
          <div className="map-tip" style={{ left: tip.x, top: tip.y - 10 }}>
            <strong>{tip.gene.geneId}</strong>
            <span>{nameOf(tip.gene.chromosome)}: {tip.gene.start.toLocaleString()}–{tip.gene.end.toLocaleString()}</span>
            {(tip.gene.family || tip.gene.description) && <span> · {[tip.gene.family, tip.gene.description].filter(Boolean).join(" · ")}</span>}
          </div>
        )}
      </div>
      <div className="map-legend" aria-hidden="true">
        {dense ? (
          <span><i className="ramp" />Gene density along the strand, few to many</span>
        ) : (
          <span><i style={{ background: "var(--viz-1)" }} />Gene</span>
        )}
        {hits.size > 0 && <span><i style={{ background: "var(--viz-2)" }} />Matches your search</span>}
        <span>Drag to rotate · scroll to zoom</span>
      </div>
      <p className="muted g3d-note">
        {label}: position along the helix is to scale, from 0 to {formatBp(length)}. The twist is decorative (one turn ≈ {formatBp(bpPerDisplayedTurn(length, turns))}),
        not a real DNA structure. Use the 2D map and the table for exact positions.
      </p>
    </div>
  );
}
