import {
  CandidateRecord,
  CandidateStage,
  CandidateStatus,
} from "@/types/candidate";
import { CandidateNote } from "@/types/note";

type CandidateRecordInput = Omit<CandidateRecord, "id">;
type CandidateNoteInput = Omit<CandidateNote, "id" | "createdAt">;

interface MockStore {
  records: CandidateRecord[];
  notesByRecordId: Record<string, CandidateNote[]>;
}

const initialRecords: CandidateRecord[] = [
  {
    id: "cand-001",
    fullName: "Avery Chen",
    email: "avery.chen@example.com",
    phone: "+1 555 0101",
    position: "Clinical Operations Analyst",
    linkedinUrl: "https://linkedin.com/in/avery-chen",
    cvUrl: "https://example.com/cv/avery-chen.pdf",
    experience: "6 years in healthcare operations and talent coordination.",
    status: "in_progress",
    stage: "review",
    applicationDate: "2026-07-01",
  },
  {
    id: "cand-002",
    fullName: "Mateo Rivera",
    email: "mateo.rivera@example.com",
    phone: "+34 600 100 200",
    position: "People Systems Specialist",
    linkedinUrl: "https://linkedin.com/in/mateo-rivera",
    cvUrl: "https://example.com/cv/mateo-rivera.pdf",
    experience: "4 years managing ATS workflows and recruiting operations.",
    status: "in_progress",
    stage: "review",
    applicationDate: "2026-06-26",
  },
  {
    id: "cand-003",
    fullName: "Priya Nair",
    email: "priya.nair@example.com",
    phone: "+44 20 7946 0958",
    position: "Talent Partner",
    linkedinUrl: "https://linkedin.com/in/priya-nair",
    cvUrl: "https://example.com/cv/priya-nair.pdf",
    experience: "8 years leading technical and operations hiring across distributed teams.",
    status: "selected",
    stage: "review",
    applicationDate: "2026-06-20",
  },
];

const initialNotesByRecordId: Record<string, CandidateNote[]> = {
  "cand-001": [
    {
      id: "note-001",
      recordId: "cand-001",
      content: "Strong process mapping background. Good fit for coordination-heavy work.",
      createdAt: "2026-07-02T10:00:00.000Z",
      author: "Hiring Team",
    },
  ],
  "cand-002": [
    {
      id: "note-002",
      recordId: "cand-002",
      content: "Interview panel requested a follow-up on reporting automation experience.",
      createdAt: "2026-06-29T15:30:00.000Z",
      author: "Recruiter",
    },
  ],
  "cand-003": [],
};

const globalStore = globalThis as typeof globalThis & {
  __talentPipelineStore__?: MockStore;
};

function createStore(): MockStore {
  return {
    records: structuredClone(initialRecords),
    notesByRecordId: structuredClone(initialNotesByRecordId),
  };
}

function getStore() {
  if (!globalStore.__talentPipelineStore__) {
    globalStore.__talentPipelineStore__ = createStore();
  }

  return globalStore.__talentPipelineStore__;
}

export function listRecords() {
  return [...getStore().records];
}

export function createRecord(input: CandidateRecordInput) {
  const store = getStore();
  const record: CandidateRecord = {
    ...input,
    id: crypto.randomUUID(),
  };

  store.records.unshift(record);
  store.notesByRecordId[record.id] = [];

  return record;
}

export function getRecord(id: string) {
  return getStore().records.find((record) => record.id === id) ?? null;
}

export function replaceRecord(id: string, input: CandidateRecordInput) {
  const store = getStore();
  const index = store.records.findIndex((record) => record.id === id);

  if (index === -1) {
    return null;
  }

  const nextRecord: CandidateRecord = {
    ...input,
    id,
  };

  store.records[index] = nextRecord;

  return nextRecord;
}

export function patchRecord(
  id: string,
  input: { status?: CandidateStatus; stage?: CandidateStage },
) {
  const store = getStore();
  const record = store.records.find((candidate) => candidate.id === id);

  if (!record) {
    return null;
  }

  if (input.status) {
    record.status = input.status;
  }

  if (input.stage) {
    record.stage = input.stage;
  }

  return record;
}

export function listNotes(recordId: string) {
  const notes = getStore().notesByRecordId[recordId] ?? [];

  return [...notes].sort((left, right) =>
    right.createdAt.localeCompare(left.createdAt),
  );
}

export function addNote(recordId: string, input: CandidateNoteInput) {
  const store = getStore();
  const note: CandidateNote = {
    ...input,
    id: crypto.randomUUID(),
    createdAt: new Date().toISOString(),
  };

  store.notesByRecordId[recordId] = [note, ...(store.notesByRecordId[recordId] ?? [])];

  return note;
}

export function removeNote(recordId: string, noteId: string) {
  const store = getStore();
  const currentNotes = store.notesByRecordId[recordId] ?? [];
  const nextNotes = currentNotes.filter((note) => note.id !== noteId);

  if (nextNotes.length === currentNotes.length) {
    return false;
  }

  store.notesByRecordId[recordId] = nextNotes;

  return true;
}