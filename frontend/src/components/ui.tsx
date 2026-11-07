import { Component, useId, type ErrorInfo, type ReactNode } from "react";
import { Icon, type IconName } from "./Icon";

export function PageHead({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="page-head">
      <h2 id="page-title" tabIndex={-1}>{title}</h2>
      {children && <p>{children}</p>}
    </div>
  );
}

export function Card({ title, icon, sub, children }: { title?: string; icon?: IconName; sub?: string; children: ReactNode }) {
  return (
    <section className="card">
      {title && <h3>{icon && <Icon name={icon} />}{title}</h3>}
      {sub && <p className="sub">{sub}</p>}
      {children}
    </section>
  );
}

interface FieldProps {
  label: string;
  hint?: string;
  error?: string | null;
  children: (props: { id: string; "aria-describedby"?: string; "aria-invalid"?: boolean }) => ReactNode;
}

/** Visible label, optional hint, and an error shown next to the field and linked via aria-describedby. */
export function Field({ label, hint, error, children }: FieldProps) {
  const id = useId();
  const describedBy = [hint ? `${id}-hint` : null, error ? `${id}-err` : null].filter(Boolean).join(" ") || undefined;
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      {children({ id, "aria-describedby": describedBy, "aria-invalid": error ? true : undefined })}
      {hint && <span className="hint" id={`${id}-hint`}>{hint}</span>}
      {error && (
        <span className="err" id={`${id}-err`} role="alert">
          <Icon name="alert" size={14} />{error}
        </span>
      )}
    </div>
  );
}

export function Button({ busy, variant, small, children, ...rest }: React.ButtonHTMLAttributes<HTMLButtonElement> & { busy?: boolean; variant?: "secondary"; small?: boolean }) {
  return (
    <button {...rest} className={`btn ${variant ?? ""} ${small ? "small" : ""}`} disabled={rest.disabled || busy} aria-busy={busy || undefined}>
      {busy && <span className="spinner" aria-hidden="true" />}
      {children}
    </button>
  );
}

export function Alert({ kind = "info", title, children }: { kind?: "info" | "warn" | "error"; title?: string; children?: ReactNode }) {
  const icon: IconName = kind === "info" ? "info" : "alert";
  return (
    <div className={`alert ${kind}`} role={kind === "error" ? "alert" : "status"}>
      <Icon name={icon} />
      <div>
        {title && <div className="alert-title">{title}</div>}
        {children}
      </div>
    </div>
  );
}

export function EmptyState({ icon = "info", title, children }: { icon?: IconName; title: string; children?: ReactNode }) {
  return (
    <div className="empty">
      <Icon name={icon} size={28} />
      <h4>{title}</h4>
      {children && <div>{children}</div>}
    </div>
  );
}

export function Skeleton({ lines = 3 }: { lines?: number }) {
  return (
    <div role="status" aria-label="Loading" style={{ display: "grid", gap: 10 }}>
      {Array.from({ length: lines }, (_, i) => (
        <div key={i} className="skeleton" style={{ width: `${90 - i * 12}%` }} />
      ))}
    </div>
  );
}

export function TableWrap({ label, children }: { label: string; children: ReactNode }) {
  // Focusable so keyboard users can scroll wide tables.
  return <div className="table-wrap" role="region" aria-label={label} tabIndex={0}>{children}</div>;
}

export class ErrorBoundary extends Component<{ children: ReactNode }, { error: Error | null }> {
  state = { error: null as Error | null };
  static getDerivedStateFromError(error: Error) { return { error }; }
  componentDidCatch(error: Error, info: ErrorInfo) { console.error(error, info.componentStack); }
  render() {
    if (this.state.error) {
      return (
        <Alert kind="error" title="This screen hit an unexpected error">
          {this.state.error.message}{" "}
          <button className="btn small secondary" onClick={() => this.setState({ error: null })}>Try again</button>
        </Alert>
      );
    }
    return this.props.children;
  }
}

/** Progressive disclosure: advanced or rarely needed content, collapsed by default. */
export function More({ summary, children, open }: { summary: string; children: ReactNode; open?: boolean }) {
  return (
    <details className="more" open={open}>
      <summary>{summary}</summary>
      <div className="body">{children}</div>
    </details>
  );
}
