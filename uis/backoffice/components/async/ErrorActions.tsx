import Link from "next/link";

interface ErrorActionsProps {
  onRetry?: () => void;
  homeHref?: string;
  retryLabel?: string;
  supportHint?: string;
}

export function ErrorActions({
  onRetry,
  homeHref = "/",
  retryLabel = "Try again",
  supportHint = "If this continues, contact HealthCore Digital support.",
}: ErrorActionsProps) {
  return (
    <>
      <div className="inline-actions">
        {onRetry ? (
          <button type="button" className="button" onClick={onRetry}>
            {retryLabel}
          </button>
        ) : null}
        <Link className="link-button secondary" href={homeHref}>
          Back to home
        </Link>
      </div>
      <p>{supportHint}</p>
    </>
  );
}
