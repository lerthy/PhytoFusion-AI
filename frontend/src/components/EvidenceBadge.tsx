import type { Level } from "../types";
import { Icon } from "./Icon";

const ICON = { strong: "check", moderate: "minus", limited: "alert" } as const;

/** Icon + word + colour, so the level is never conveyed by colour alone. */
export function EvidenceBadge({ level }: { level: Level }) {
  return (
    <span className={`badge ${level}`} title="An evidence class, not a success probability">
      <Icon name={ICON[level]} size={14} />
      {level} evidence
    </span>
  );
}
