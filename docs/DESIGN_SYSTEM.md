# Design system

Chosen with the `ui-ux-pro-max` skill (installed in `.agents/skills/ui-ux-pro-max`), then checked
against this product. The skill's first suggestion for "scientific genomics dashboard" was
Neumorphism with an orange-on-dark palette. We did **not** use it: its own data flags Neumorphism as
`accessibility risk: high` and suited to wellness apps, which is wrong for a dense data tool.

## Decisions

| Area | Choice | Why |
|---|---|---|
| Style | **Data-Dense Dashboard** (skill: `data-dense-dashboard`, accessibility risk low) | Tables, KPI cards, compact rows, sticky headers: what a researcher needs |
| Palette | **Research Lab**: navy `#1E3A5F`, blue `#2563EB`, amber `#A16207`, background `#F8FAFC` | Institutional and calm. Dark theme values were derived by us (the palette is light only) |
| Type | **Fira Sans** (UI) + **Fira Code** (ids, numbers) | Skill pairing for dashboards and technical data |
| Spacing | 4 / 8 / 12 / 16 / 24 / 32 px, 36 px table rows, 56 px header, 232 px sidebar | Skill's dense-dashboard variables |
| Icons | One inline SVG set: 20 px, 1.75 stroke, outline | No emoji as icons; consistent weight |
| Motion | Subtle: 150 ms hovers, skeleton shimmer, nothing decorative; `prefers-reduced-motion` respected | Skill's low-motion tier |

All colours are semantic tokens in `frontend/src/styles.css`, mapped for light and dark.

## Accessibility checks (measured, not assumed)

| Pair | Light | Dark | Needs |
|---|---|---|---|
| Text on background | 17.1 | 15.9 | 4.5 |
| Muted text on surface | 7.6 | 7.9 | 4.5 |
| Primary on surface | 11.5 | 8.2 | 4.5 |
| Link/secondary on surface | 5.2 | 6.7 | 4.5 |
| Evidence strong / moderate / limited on surface | 5.0 / 4.9 / 6.5 | 10.0 / 8.2 / 6.3 | 4.5 |
| Control border on surface (`--border-strong`) | 4.8 | 4.5 | 3.0 |

Decorative card borders (`--border`) are about 1.5:1 on purpose; every control uses `--border-strong`.

## Data marks (dataviz skill)

- **Colours:** gene marks use the validated categorical slots `--viz-1` blue and `--viz-2` orange
  (light `#2a78d6` / `#eb6834`, dark `#3987e5` / `#d95926`). Our first choice, the navy brand colour,
  **failed** the skill's validator (too dark, too low chroma, so it reads grey), and so did the
  lighter dark-mode blue. Both pairs now pass all five checks on the real surfaces.
- **Chromosome map:** thin marks to scale, a Mb axis, a legend, and a hover readout (gene,
  coordinates, notes) whose hit area is wider than the mark. The gene table beside it holds every
  value, its rows are keyboard-focusable, and focusing a row marks the gene on the map, so nothing
  needs the pointer.
- **Real genomes are dense.** A real annotation has thousands of genes per chromosome, where
  one mark per gene merges into a solid bar (the skill's "thick saturated blocks" anti-pattern).
  Above 150 genes on a sequence the map switches to **gene density**: 240 windows per track, one
  hue from light to dark, with the window size and the maximum count in the legend. Sparse data
  still gets individual marks. Found while loading the real *S. baicalensis* file (30,313 genes).
- **Small scaffolds hidden by default.** Real assemblies include many tiny unplaced scaffolds (80 of
  89 sequences in that file). The map shows the sequences that are at least 10% of the longest,
  with a "Show all" toggle, and uses the file's `#OriSeqID` names (`Sbai1`) instead of accessions.
- **3D view (Genomes, "3D" tab):** one chromosome drawn as a double helix with `three.js`,
  lazy-loaded (a separate ~141 kB download, fetched only when the tab is opened). Position along the
  helix is real and to scale; **the twist is decorative** (a real helix would have millions of
  turns) and the caption says so. Dense chromosomes colour one strand by gene density (the same
  light-to-dark blue as the 2D map); sparse ones get a bead per gene; search matches are larger and
  orange. Rendering is on demand with no auto-spin. Hover finds the nearest gene within 10 px and
  moves a marker to it. The canvas is keyboard-focusable and labelled, and the 2D map and gene table
  carry the same data, because 3D distorts quantities and is a visual aid, not the precise view.
- **Pathway graph:** genes are blue diamonds, compounds are pale rounded squares with a border
  (shape and fill, not colour alone); labels sit on a halo; evidence is line style plus colour, with
  the steps table underneath.

## Avoiding the template look (artifact-design skill)

Removed an accent bar on the report banner (now a tinted box with an icon), left-aligned the closing
call to action, replaced a stack of identical white cards on the About page with plain columns and
species blocks, and made the report a headline plus plain sections with only the limits tinted. The
About hero is a schematic of the case study (13 donor and 9 host chromosomes, both real counts;
bar lengths and the gene position are labelled illustrative).

## Front door

`#/about` is the landing page and the default for an empty or unknown URL. It follows the skill's
"Minimal Single Column" pattern (hero, short idea, three steps, what it does and does not do, one
call to action) with 65-75 character text lines and 16 px+ body text on phones. It sits outside the
app navigation: its only exits are "Open the app" buttons, which lead to Home. Inside the app, the
brand links back to it. The skill's other landing patterns (before/after slider, AI input hero) did
not fit this product and were not used.

## Simplicity rules (from the skill's UX guidance)

- **Four top-level steps, no sidebar:** Home, 1 Genomes, 2 Compare, 3 Simulate. The skill caps primary
  navigation at five items. Evidence and Pathways are tabs under Compare; Report is a tab under
  Simulate. Old links such as `#/pathway` still work.
- **One main action per screen**, and plain-language wording (for example "Find the closest match in
  the host plant", "What we don't know") instead of bioinformatics terms.
- **Progressive disclosure:** advanced or rarely needed controls sit in collapsed "more" sections
  (rating a gene pair by hand, saved items, saving a pathway, optional scenario facts, searching
  papers). The simple path works without opening any of them.
- **Step progress:** the numbered steps in the top bar show where you are; the back button and deep
  links behave predictably.

## Rules the UI follows

- **Colour is never the only signal.** Evidence levels are icon + word + colour; pathway edges also
  differ by line style (solid, dotted, dashed); reciprocal hits say "yes/no".
- Every input has a visible label. Errors appear next to the field and are linked with
  `aria-describedby`; the form summary says what to fix.
- Visible focus ring on everything interactive; the skip link and screen-change focus move to the
  page title; the nav uses `aria-current`.
- Wide tables scroll inside a keyboard-focusable region. Charts and graphs have a table with the same
  data underneath.
- Empty, loading and error states exist for every data view, and a missing database or embeddings
  service (HTTP 503) explains what to configure instead of showing a generic failure.
- Touch targets are at least 44 px below 860 px width; no horizontal page scroll.
- Language: "hypothetical", "computational", "evidence level". Never a compatibility or success score. The only percentage shown is measured protein similarity, labelled as such, with a note that it does not mean the gene would work.

## Verified and not verified
- Looked at in headless Chrome (desktop 1280 px, phone 390 px, light and dark) with sample genome and
  pathway files. That pass found and fixed: a needless "database not configured" warning on screens
  that work without it, a missing full stop in that warning, the top navigation cutting off
  "Simulate" on phones, a clipped label in the About schematic, a dead Compare form when no genomes
  are stored, and a map tooltip hanging off the card.
- Not checked: tablet widths, every screen in dark and phone, real genome data (the sample genes
  used for screenshots were made up for testing only and are not in the repo), screen readers.
- No automated accessibility or visual tests. Add Playwright + axe when time allows.
