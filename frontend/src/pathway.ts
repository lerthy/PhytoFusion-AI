export type Element = { data: Record<string, unknown> };

const LEVELS = ["strong", "moderate", "limited"];

/** Enforces the traceability rule on load: every edge needs a reference and an evidence level. */
export function validateElements(raw: unknown): Element[] {
  if (!Array.isArray(raw)) throw new Error("expected a JSON array of Cytoscape elements");
  const elements = raw as Element[];
  elements.forEach((el, i) => {
    const d = el?.data;
    if (!d || typeof d !== "object") throw new Error(`element ${i}: missing data`);
    if ("source" in d) {
      if (typeof d.reference !== "string" || !d.reference.trim()) {
        throw new Error(`edge ${i}: missing PMID/DOI reference`);
      }
      if (!LEVELS.includes(String(d.evidence_level))) {
        throw new Error(`edge ${i}: evidence_level must be one of ${LEVELS.join(", ")}`);
      }
    } else if (typeof d.id !== "string") {
      throw new Error(`node ${i}: missing id`);
    }
  });
  return elements;
}
