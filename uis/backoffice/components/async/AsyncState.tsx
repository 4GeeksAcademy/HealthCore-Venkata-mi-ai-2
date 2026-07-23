import { ReactNode } from "react";

interface AsyncStateProps {
  loading: boolean;
  error: string | null;
  children: ReactNode;
  loadingText?: string;
  emptyState?: ReactNode;
  isEmpty?: boolean;
}

export function AsyncState({
  loading,
  error,
  children,
  loadingText = "Loading data...",
  emptyState,
  isEmpty = false,
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
        {error}
      </div>
    );
  }

  if (isEmpty && emptyState) {
    return <>{emptyState}</>;
  }

  return <>{children}</>;
}