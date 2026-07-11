export const candidateStatusOptions = [
  "received",
  "in_progress",
  "selected",
  "rejected",
  "discarded",
] as const;

export const candidateStageOptions = [
  "pending",
  "review",
] as const;

export type CandidateStatus = (typeof candidateStatusOptions)[number];
export type CandidateStage = (typeof candidateStageOptions)[number];

export interface CandidateRecord {
  id: string;
  fullName: string;
  email: string;
  phone: string;
  position: string;
  linkedinUrl: string;
  cvUrl: string;
  experience: string;
  status: CandidateStatus;
  stage: CandidateStage;
  applicationDate: string;
}

export interface CandidateFormValues {
  fullName: string;
  email: string;
  phone: string;
  position: string;
  linkedinUrl: string;
  cvUrl: string;
  experience: string;
  status: CandidateStatus;
  stage: CandidateStage;
  applicationDate: string;
}

export type CreateCandidateInput = CandidateFormValues;
export type UpdateCandidateInput = CandidateFormValues;

export interface PatchCandidateInput {
  status?: CandidateStatus;
  stage?: CandidateStage;
}