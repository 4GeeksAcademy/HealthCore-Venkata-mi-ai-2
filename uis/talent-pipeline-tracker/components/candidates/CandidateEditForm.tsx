"use client";

import { CandidateForm } from "@/components/candidates/CandidateForm";
import { toCandidateFormValues, updateRecord } from "@/lib/records-service";
import { CandidateRecord } from "@/types/candidate";

interface CandidateEditFormProps {
  candidate: CandidateRecord;
  onUpdated: (candidate: CandidateRecord) => void;
}

export function CandidateEditForm({
  candidate,
  onUpdated,
}: CandidateEditFormProps) {
  const formValues = toCandidateFormValues(candidate);

  return (
    <CandidateForm
      key={JSON.stringify(formValues)}
      heading="Edit candidate"
      description="Update the complete candidate profile through the PUT record endpoint."
      submitLabel="Save candidate"
      initialValues={formValues}
      onSubmit={async (values) => {
        const updatedCandidate = await updateRecord(candidate.id, values);
        onUpdated(updatedCandidate);
      }}
    />
  );
}