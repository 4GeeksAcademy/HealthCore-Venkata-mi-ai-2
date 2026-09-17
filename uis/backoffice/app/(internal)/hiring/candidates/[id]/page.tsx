import { Suspense } from "react";
import { CandidateDetailPage } from "@/components/candidates/CandidateDetailPage";

export default function HiringCandidateDetailRoute() {
  return (
    <Suspense
      fallback={
        <main className="app-shell">
          <div className="page-frame">
            <div className="feedback info">Loading candidate profile...</div>
          </div>
        </main>
      }
    >
      <CandidateDetailPage />
    </Suspense>
  );
}
