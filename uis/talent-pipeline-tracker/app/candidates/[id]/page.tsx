import { Suspense } from "react";
import { CandidateDetailPage } from "@/components/candidates/CandidateDetailPage";

export default function CandidateDetailRoute() {
  return (
    <Suspense fallback={<main className="app-shell"><div className="page-frame"><div className="feedback info">Loading candidate detail...</div></div></main>}>
      <CandidateDetailPage />
    </Suspense>
  );
}