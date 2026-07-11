import { fetchJson } from "@/lib/api-client";
import {
  CandidateFormValues,
  CandidateRecord,
  CandidateStage,
  CandidateStatus,
  CreateCandidateInput,
  PatchCandidateInput,
  UpdateCandidateInput,
  candidateStageOptions,
  candidateStatusOptions,
} from "@/types/candidate";
import { QueryParams } from "@/types/api";

type UnknownRecord = Record<string, unknown>;

export interface RecordsResult {
  records: CandidateRecord[];
  total: number;
  page: number;
  limit: number;
}

export async function getRecords(query: QueryParams = {}) {
  const payload = await fetchJson<unknown>("/records", {
    method: "GET",
    query: toApiQuery(query),
    cache: "no-store",
  });

  const { records, total, page, limit } = readCollectionPayload(payload);

  return {
    records: records.map(normalizeCandidateRecord),
    total,
    page,
    limit,
  } satisfies RecordsResult;
}

export async function getRecordById(id: string) {
  const payload = await fetchJson<unknown>(`/records/${id}`, {
    method: "GET",
    cache: "no-store",
  });

  return normalizeCandidateRecord(payload);
}

export async function createRecord(input: CreateCandidateInput) {
  const payload = await fetchJson<unknown>("/records", {
    method: "POST",
    body: toApiCandidatePayload(input),
  });

  return normalizeCandidateRecord(payload);
}

export async function updateRecord(id: string, input: UpdateCandidateInput) {
  const payload = await fetchJson<unknown>(`/records/${id}`, {
    method: "PUT",
    body: toApiCandidatePayload(input),
  });

  return normalizeCandidateRecord(payload);
}

export async function patchRecord(id: string, input: PatchCandidateInput) {
  const payload = await fetchJson<unknown>(`/records/${id}`, {
    method: "PATCH",
    body: input,
  });

  return normalizeCandidateRecord(payload);
}

export function filterCandidateRecords(
  records: CandidateRecord[],
  query: QueryParams,
) {
  const searchTerm = query.query?.trim().toLowerCase() ?? "";

  return records.filter((record) => {
    const matchesStatus = query.status ? record.status === query.status : true;
    const matchesStage = query.stage ? record.stage === query.stage : true;
    const matchesQuery = searchTerm
      ? record.fullName.toLowerCase().includes(searchTerm) ||
        record.email.toLowerCase().includes(searchTerm)
      : true;

    return matchesStatus && matchesStage && matchesQuery;
  });
}

export function getDefaultCandidateValues(): CandidateFormValues {
  return {
    fullName: "",
    email: "",
    phone: "",
    position: "",
    linkedinUrl: "",
    cvUrl: "",
    experience: "",
    status: "received",
    stage: "pending",
    applicationDate: new Date().toISOString().slice(0, 10),
  };
}

export function toCandidateFormValues(
  candidate: CandidateRecord,
): CandidateFormValues {
  return {
    fullName: candidate.fullName,
    email: candidate.email,
    phone: candidate.phone,
    position: candidate.position,
    linkedinUrl: candidate.linkedinUrl,
    cvUrl: candidate.cvUrl,
    experience: candidate.experience,
    status: candidate.status,
    stage: candidate.stage,
    applicationDate: candidate.applicationDate.slice(0, 10),
  };
}

function toApiCandidatePayload(input: CandidateFormValues) {
  return {
    fullName: input.fullName,
    email: input.email,
    phone: input.phone,
    position: input.position,
    linkedinUrl: input.linkedinUrl,
    cvUrl: input.cvUrl,
    experience: input.experience,
    status: input.status,
    stage: input.stage,
    applicationDate: input.applicationDate,
  };
}

function normalizeCandidateRecord(payload: unknown): CandidateRecord {
  if (!isRecord(payload)) {
    throw new Error("Candidate payload is not a valid object.");
  }

  return {
    id: readString(firstDefined(payload.id, payload.recordId, payload.record_id)),
    fullName: readString(
      firstDefined(payload.fullName, payload.full_name, payload.name),
    ),
    email: readString(payload.email),
    phone: readString(firstDefined(payload.phone, payload.phoneNumber, payload.phone_number)),
    position: readString(
      firstDefined(payload.position, payload.positionAppliedFor, payload.position_applied_for, payload.role),
    ),
    linkedinUrl: readString(
      firstDefined(payload.linkedinUrl, payload.linkedin_url, payload.linkedin),
    ),
    cvUrl: readString(firstDefined(payload.cvUrl, payload.cv_url, payload.cvLink, payload.cv_link)),
    experience: stringifyValue(
      firstDefined(
        payload.experience,
        payload.experienceYears,
        payload.experience_years,
        payload.yearsExperience,
        payload.years_experience,
      ),
    ),
    status: normalizeStatus(payload.status),
    stage: normalizeStage(payload.stage),
    applicationDate: normalizeDate(
      firstDefined(
        payload.applicationDate,
        payload.application_date,
        payload.appliedAt,
        payload.applied_at,
        payload.createdAt,
        payload.created_at,
      ),
    ),
  };
}

function normalizeStatus(value: unknown): CandidateStatus {
  const normalized = readString(value).toLowerCase().trim();

  return candidateStatusOptions.find((option) => option === normalized) ?? "received";
}

function normalizeStage(value: unknown): CandidateStage {
  const normalized = readString(value).toLowerCase().trim();

  return candidateStageOptions.find((option) => option === normalized) ?? "pending";
}

function readCollectionPayload(payload: unknown) {
  if (Array.isArray(payload)) {
    return {
      records: payload,
      total: payload.length,
      page: 1,
      limit: payload.length,
    };
  }

  if (isRecord(payload) && Array.isArray(payload.data)) {
    return {
      records: payload.data,
      total: readNumber(payload.total) ?? payload.data.length,
      page: readNumber(payload.page) ?? 1,
      limit: readNumber(payload.limit) ?? payload.data.length,
    };
  }

  throw new Error("Records payload is not a valid collection.");
}

function toApiQuery(query: QueryParams) {
  return {
    status: query.status,
    stage: query.stage,
    search: query.query,
    page: query.page,
    limit: query.limit,
  };
}

function normalizeDate(value: unknown) {
  const dateString = readString(value);

  if (!dateString) {
    return new Date().toISOString();
  }

  return dateString;
}

function firstDefined(...values: unknown[]) {
  return values.find((value) => value !== undefined && value !== null);
}

function isRecord(value: unknown): value is UnknownRecord {
  return typeof value === "object" && value !== null;
}

function readString(value: unknown) {
  return typeof value === "string" ? value : "";
}

function readNumber(value: unknown) {
  return typeof value === "number" ? value : null;
}

function stringifyValue(value: unknown) {
  if (typeof value === "string") {
    return value;
  }

  if (typeof value === "number") {
    return String(value);
  }

  return "";
}