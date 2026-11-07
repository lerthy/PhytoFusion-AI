import { OPTIONS, type AssessInput } from "../types";
import { Field } from "./ui";

const LABELS: Record<keyof AssessInput, string> = {
  sequence: "Sequence relationship",
  functional: "Functional evidence",
  pathway: "Pathway completeness",
  expression: "Expression compatibility",
  context: "Genomic context",
};

interface Props {
  value: AssessInput;
  onChange: (next: AssessInput) => void;
}

export function AssessmentFields({ value, onChange }: Props) {
  return (
    <div className="grid">
      {(Object.keys(OPTIONS) as (keyof AssessInput)[]).map((key) => (
        <Field key={key} label={LABELS[key]}>
          {(a11y) => (
            <select {...a11y} value={value[key]} onChange={(e) => onChange({ ...value, [key]: e.target.value } as AssessInput)}>
              {OPTIONS[key].map((option) => (
                <option key={option} value={option}>{option.replace("_", " ")}</option>
              ))}
            </select>
          )}
        </Field>
      ))}
    </div>
  );
}
