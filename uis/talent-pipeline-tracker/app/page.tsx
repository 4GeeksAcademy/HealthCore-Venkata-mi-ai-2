import { Suspense } from "react";
import { CandidateListPage } from "@/components/candidates/CandidateListPage";

export default function Home() {
  return (
    <Suspense fallback={<main className="app-shell"><div className="page-frame"><div className="feedback info">Loading candidate workspace...</div></div></main>}>
      <CandidateListPage />
    </Suspense>
  );
}
