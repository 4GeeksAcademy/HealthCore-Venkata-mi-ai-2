import { ReactNode } from "react";
import { ErrorActions } from "@/components/async/ErrorActions";

interface AsyncStateProps {
  loading: boolean;
  error: string | null;
  children: ReactNode;
  loadingText?: string;
  emptyState?: ReactNode;
  isEmpty?: boolean;
  onRetry?: () => void;
  homeHref?: string;
  supportHint?: string;
}

export function AsyncState({
  loading,
  error,
  children,
  loadingText = "Loading data...",
  emptyState,
  isEmpty = false,
  onRetry,
  homeHref = "/",
  supportHint = "If this continues, contact HealthCore Digital support.",
}: AsyncStateProps) {
  if (loading) {
    return (
      <div className="feedback info" role="status" aria-live="polite">
        {loadingText}
      </div>
    );
  }

  if (error) {
    return (
      <div className="feedback error" role="alert">
        <p>{error}</p>
        <ErrorActions onRetry={onRetry} homeHref={homeHref} supportHint={supportHint} />
      </div>
    );
  }

  if (isEmpty && emptyState) {
    return <>{emptyState}</>;
  }

  return <>{children}</>;
}
