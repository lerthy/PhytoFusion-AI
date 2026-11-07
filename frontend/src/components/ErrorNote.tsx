import { ApiError } from "../api";
import { Alert } from "./ui";

const sentence = (text: string) => (/[.!?]$/.test(text.trim()) ? text.trim() : `${text.trim()}.`);

/**
 * 503 = the server is up but a backing service is not configured. For optional lists (saved items)
 * pass `quiet` so a missing database is silent: the screen still works from files and fresh input.
 */
export function ErrorNote({ error, quiet }: { error: Error | null; quiet?: boolean }) {
  if (!error) return null;
  if (error instanceof ApiError && error.notConfigured) {
    if (quiet) return null;
    return (
      <Alert kind="warn" title="Not available yet">
        {sentence(error.message)} Add the missing values to <code>.env</code> and restart the backend.
      </Alert>
    );
  }
  return <Alert kind="error" title="Something went wrong">{sentence(error.message)}</Alert>;
}
