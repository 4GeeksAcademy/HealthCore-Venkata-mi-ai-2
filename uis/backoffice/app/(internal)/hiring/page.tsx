import { Suspense } from "react";
import { CandidateListPage } from "@/components/candidates/CandidateListPage";

export default function HiringPage() {
  return (
    <Suspense
      fallback={
        <main className="app-shell">
          <div className="page-frame">
            <div className="feedback info">Loading hiring workspace...</div>
          </div>
        </main>
      }
    >
      <CandidateListPage />
    </Suspense>
  );
}
