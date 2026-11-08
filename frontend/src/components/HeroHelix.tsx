import { useEffect, useRef } from "react";
import * as THREE from "three";
import { helixPoint } from "../helix";

const css = (name: string, fallback: string) => getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback;

const STEPS = 110;       // rungs along the helix
const TURNS = 4.2;
const HEIGHT = 11;
const RADIUS = 1.45;
const GENE = [0.56, 0.67]; // the highlighted stretch (a stand-in for one gene), as a fraction of the length
const BUILD_MS = 2200;

/**
 * A decorative DNA double helix for the About page. It builds up once, then turns slowly.
 * The orange stretch stands for "one donor gene". It carries no data: the real, to-scale view is on Genomes.
 * Stops when scrolled out of view, when the tab is hidden, when paused, and under reduced motion.
 */
export default function HeroHelix({ paused }: { paused: boolean }) {
  const mount = useRef<HTMLDivElement>(null);
  const pausedRef = useRef(paused);
  pausedRef.current = paused;

  useEffect(() => {
    const host = mount.current;
    if (!host) return;
    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    } catch {
      return; // no WebGL: the page reads fine without the picture
    }
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    host.appendChild(renderer.domElement);
    renderer.domElement.setAttribute("aria-hidden", "true");

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(30, 1, 0.1, 100);
    camera.position.set(0, 0, 20.5);
    scene.add(new THREE.AmbientLight(0xffffff, 1.1));
    const key = new THREE.DirectionalLight(0xffffff, 2.2);
    key.position.set(4, 6, 8);
    scene.add(key);

    const group = new THREE.Group();
    group.rotation.z = -0.42;
    scene.add(group);

    const mint = new THREE.Color(css("--hero-mint", "#6fcaa2"));
    const pale = new THREE.Color(css("--hero-muted", "#b8cfc3"));
    const orange = new THREE.Color(css("--accent", "#eb6834"));

    const ball = new THREE.SphereGeometry(0.13, 16, 16);
    const strandMat = new THREE.MeshStandardMaterial({ color: mint, roughness: 0.4, metalness: 0.1 });
    const geneMat = new THREE.MeshStandardMaterial({ color: orange, roughness: 0.35, metalness: 0.1, emissive: orange, emissiveIntensity: 0.35 });
    const strands = new THREE.InstancedMesh(ball, strandMat, STEPS * 2);
    const genes = new THREE.InstancedMesh(ball, geneMat, STEPS * 2);
    const shape = { height: HEIGHT, turns: TURNS, radius: RADIUS };
    const m = new THREE.Matrix4();
    const rungPositions: number[] = [];
    const rungColors: number[] = [];
    const isGene: boolean[] = [];
    let geneCount = 0;
    for (let i = 0; i < STEPS; i++) {
      const t = i / (STEPS - 1);
      const inGene = t >= GENE[0] && t <= GENE[1];
      const a = helixPoint(t, 0, shape), b = helixPoint(t, 1, shape);
      // helixPoint runs along x; stand the axis up
      const pa = new THREE.Vector3(a[1], a[0], a[2]), pb = new THREE.Vector3(b[1], b[0], b[2]);
      for (const [s, p] of [[0, pa], [1, pb]] as const) {
        const scale = inGene ? 1.5 : 1;
        m.compose(p, new THREE.Quaternion(), new THREE.Vector3(scale, scale, scale));
        (inGene ? genes : strands).setMatrixAt((inGene ? geneCount++ : i * 2 + s) , m);
      }
      isGene.push(inGene);
      if (i % 3 === 0) {
        rungPositions.push(pa.x, pa.y, pa.z, pb.x, pb.y, pb.z);
        const c = inGene ? orange : pale;
        rungColors.push(c.r, c.g, c.b, c.r, c.g, c.b);
      }
    }
    // Instances for gene steps are packed first in `genes`; blank the matching slots in `strands`.
    const zero = new THREE.Matrix4().makeScale(0, 0, 0);
    for (let i = 0; i < STEPS; i++) if (isGene[i]) { strands.setMatrixAt(i * 2, zero); strands.setMatrixAt(i * 2 + 1, zero); }
    strands.count = 0;
    genes.count = 0;
    group.add(strands, genes);

    const rungGeo = new THREE.BufferGeometry();
    rungGeo.setAttribute("position", new THREE.Float32BufferAttribute(rungPositions, 3));
    rungGeo.setAttribute("color", new THREE.Float32BufferAttribute(rungColors, 3));
    const rungs = new THREE.LineSegments(rungGeo, new THREE.LineBasicMaterial({ vertexColors: true, transparent: true, opacity: 0.38 }));
    group.add(rungs);
    const rungVerts = rungPositions.length / 3;

    const resize = () => {
      const w = host.clientWidth || 1, h = host.clientHeight || 1;
      renderer.setSize(w, h, false);
      renderer.domElement.style.width = "100%";
      renderer.domElement.style.height = "100%";
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
    };
    const observer = new ResizeObserver(() => { resize(); if (reduce) draw(1); });
    observer.observe(host);

    let tiltX = 0, targetTiltX = 0;
    const onMove = (e: PointerEvent) => {
      const r = host.getBoundingClientRect();
      targetTiltX = ((e.clientY - r.top) / r.height - 0.5) * 0.3;
    };
    if (!reduce) window.addEventListener("pointermove", onMove);

    const ease = (x: number) => 1 - Math.pow(1 - x, 3);
    const draw = (progress: number) => {
      const p = ease(Math.min(1, progress));
      strands.count = Math.floor(STEPS * 2 * p);
      // the gene appears once the build passes it, then holds
      genes.count = p > 0.72 ? geneCount : 0;
      rungs.geometry.setDrawRange(0, Math.floor(rungVerts * p / 2) * 2);
      renderer.render(scene, camera);
    };

    let raf = 0, last = performance.now(), start = last, visible = true;
    const frame = (now: number) => {
      raf = requestAnimationFrame(frame);
      if (!visible || document.hidden) { last = now; return; }
      const dt = Math.min(0.05, (now - last) / 1000);
      last = now;
      if (!pausedRef.current) group.rotation.y += dt * 0.32;
      tiltX += (targetTiltX - tiltX) * 0.05;
      group.rotation.x = tiltX;
      draw((now - start) / BUILD_MS);
    };

    resize();
    if (reduce) {
      group.rotation.y = 0.6;
      draw(1);
    } else {
      raf = requestAnimationFrame(frame);
    }
    const io = new IntersectionObserver(([entry]) => { visible = entry.isIntersecting; }, { threshold: 0.05 });
    io.observe(host);

    return () => {
      cancelAnimationFrame(raf);
      observer.disconnect();
      io.disconnect();
      window.removeEventListener("pointermove", onMove);
      ball.dispose(); rungGeo.dispose(); strandMat.dispose(); geneMat.dispose(); rungs.material.dispose();
      renderer.dispose();
      renderer.domElement.remove();
    };
  }, []);

  return <div ref={mount} className="hero-helix" />;
}
