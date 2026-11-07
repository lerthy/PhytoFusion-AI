import { useState } from "react";
import { Field } from "./ui";

interface Props {
  label: string;
  accept: string;
  hint?: string;
  onText: (text: string, fileName: string) => void;
}

/** Reads a local file in the browser; nothing is uploaded anywhere. */
export function FileLoader({ label, accept, hint, onText }: Props) {
  const [error, setError] = useState<string | null>(null);
  return (
    <Field label={label} hint={hint ?? "Read locally in your browser. Nothing is uploaded."} error={error}>
      {(a11y) => (
        <input
          {...a11y}
          type="file"
          accept={accept}
          onChange={async (e) => {
            const file = e.target.files?.[0];
            if (!file) return;
            try {
              setError(null);
              onText(await file.text(), file.name);
            } catch (err) {
              setError(err instanceof Error ? err.message : String(err));
            }
          }}
        />
      )}
    </Field>
  );
}
