import { fetchJson } from "@/lib/api-client";
import { CandidateNote, CreateNoteInput } from "@/types/note";

type UnknownRecord = Record<string, unknown>;

export async function getNotes(recordId: string) {
  const payload = await fetchJson<unknown>(`/records/${recordId}/notes`, {
    method: "GET",
    cache: "no-store",
  });

  const notes = readCollectionPayload(payload);

  return notes.map((note) => normalizeCandidateNote(note, recordId));
}

export async function createNote(recordId: string, input: CreateNoteInput) {
  const payload = await fetchJson<unknown>(`/records/${recordId}/notes`, {
    method: "POST",
    body: input,
  });

  return normalizeCandidateNote(payload, recordId);
}

export async function deleteNote(recordId: string, noteId: string) {
  await fetchJson(`/records/${recordId}/notes/${noteId}`, {
    method: "DELETE",
  });
}

function normalizeCandidateNote(payload: unknown, recordId: string): CandidateNote {
  if (!isRecord(payload)) {
    throw new Error("Note payload is not a valid object.");
  }

  return {
    id: readString(firstDefined(payload.id, payload.noteId, payload.note_id)),
    recordId,
    content: readString(firstDefined(payload.content, payload.body, payload.note)),
    createdAt: normalizeDate(
      firstDefined(payload.createdAt, payload.created_at, payload.timestamp),
    ),
    author: readString(firstDefined(payload.author, payload.createdBy, payload.created_by)),
  };
}

function firstDefined(...values: unknown[]) {
  return values.find((value) => value !== undefined && value !== null);
}

function isRecord(value: unknown): value is UnknownRecord {
  return typeof value === "object" && value !== null;
}

function readCollectionPayload(payload: unknown) {
  if (Array.isArray(payload)) {
    return payload;
  }

  if (isRecord(payload) && Array.isArray(payload.data)) {
    return payload.data;
  }

  throw new Error("Notes payload is not a valid collection.");
}

function normalizeDate(value: unknown) {
  return typeof value === "string" && value ? value : new Date().toISOString();
}

function readString(value: unknown) {
  return typeof value === "string" ? value : "";
}