export interface CandidateNote {
  id: string;
  recordId: string;
  content: string;
  createdAt: string;
  author?: string;
}

export interface CreateNoteInput {
  content: string;
}