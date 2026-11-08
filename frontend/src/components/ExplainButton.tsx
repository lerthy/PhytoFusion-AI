import { useState } from "react";
import { ApiError, explainResult } from "../api";
import { Icon } from "./Icon";
import { Button } from "./ui";

/**
 * Asks the backend for a short plain-language explanation of facts already on screen.
 * The text is AI-written, always labelled, and never replaces the facts or the evidence level.
 */
export function ExplainButton({ kind, facts }: { kind: "comparison" | "report"; facts: Record<string, unknown> }) {
  const [text, setText] = useState<string | null>(null);
  const [model, setModel] = useState("");
  const [note, setNote] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const run = async () => {
    setBusy(true);
    setNote(null);
    try {
      const out = await explainResult(kind, facts);
      setText(out.text);
      setModel(out.model);
    } catch (e) {
      setText(null);
      if (e instanceof ApiError && e.status === 503 && /not configured/i.test(e.message)) {
        setNote("AI explanations are not switched on for this server yet.");
      } else if (e instanceof ApiError && e.status === 429) {
        setNote("Too many explanations were asked for. Try again later.");
      } else if (e instanceof ApiError && e.status === 502) {
        setNote("The AI declined to explain this one. The facts above still stand on their own.");
      } else {
        setNote(e instanceof Error ? e.message : "The explanation could not be made.");
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="explain">
      <Button variant="secondary" small busy={busy} onClick={run}>Explain in plain words</Button>
      {busy && <span className="muted" role="status"> Writing…</span>}
      {note && <p className="muted explain-note" role="status">{note}</p>}
      {text && (
        <div className="explain-card" role="status">
          <p>{text}</p>
          <p className="muted explain-note"><Icon name="info" size={14} /> Written by an AI model{model ? ` (${model})` : ""} from the facts shown here. Check it against the sources.</p>
        </div>
      )}
    </div>
  );
}
