const PATHS = {
  dashboard: <><rect x="3" y="3" width="7" height="9" /><rect x="14" y="3" width="7" height="5" /><rect x="14" y="12" width="7" height="9" /><rect x="3" y="16" width="7" height="5" /></>,
  dna: <><path d="M6 3c0 5 12 6 12 9s-12 4-12 9" /><path d="M18 3c0 5-12 6-12 9s12 4 12 9" /><path d="M8 6.5h8M8 17.5h8M7 12h10" /></>,
  compare: <path d="M4 8h14M14 4l4 4-4 4M20 16H6M10 12l-4 4 4 4" />,
  network: <><circle cx="6" cy="6" r="2.5" /><circle cx="18" cy="8" r="2.5" /><circle cx="10" cy="18" r="2.5" /><path d="M8.3 6.6l7.3 1M7 8.3l2.2 7.3M11.5 16.2l5-6" /></>,
  scissors: <><circle cx="6" cy="6" r="3" /><circle cx="6" cy="18" r="3" /><path d="M20 4 8.1 15.9M14.5 14.5 20 20M8.1 8.1 12 12" /></>,
  report: <><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" /><path d="M14 3v5h5M9 13h6M9 17h6" /></>,
  book: <><path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2z" /><path d="M4 19V5M9 7h6" /></>,
  check: <path d="M5 12l5 5 9-10" />,
  minus: <path d="M5 12h14" />,
  alert: <><path d="M12 3l10 18H2z" /><path d="M12 10v5M12 18h.01" /></>,
  info: <><circle cx="12" cy="12" r="9" /><path d="M12 11v6M12 8h.01" /></>,
  x: <path d="M6 6l12 12M18 6 6 18" />,
  database: <><ellipse cx="12" cy="5" rx="8" ry="3" /><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3" /></>,
  upload: <path d="M12 16V4M7 9l5-5 5 5M4 20h16" />,
  search: <><circle cx="11" cy="11" r="7" /><path d="m20 20-4-4" /></>,
  download: <path d="M12 4v12M7 11l5 5 5-5M4 20h16" />,
} as const;

export type IconName = keyof typeof PATHS;

/** One icon style throughout: 20px, 1.75 stroke, outline. Decorative unless `label` is given. */
export function Icon({ name, size = 20, label }: { name: IconName; size?: number; label?: string }) {
  return (
    <svg
      className="icon"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      strokeLinecap="round"
      strokeLinejoin="round"
      role={label ? "img" : undefined}
      aria-label={label}
      aria-hidden={label ? undefined : true}
      focusable="false"
    >
      {PATHS[name]}
    </svg>
  );
}
