import { NextRequest, NextResponse } from "next/server";
import { createRecord, listRecords } from "@/lib/mock-store";
import { readJsonBody } from "@/lib/read-json-body";
import {
  candidateStageOptions,
  candidateStatusOptions,
  CreateCandidateInput,
} from "@/types/candidate";

export async function GET(request: NextRequest) {
  const status = request.nextUrl.searchParams.get("status") ?? undefined;
  const stage = request.nextUrl.searchParams.get("stage") ?? undefined;
  const query = request.nextUrl.searchParams.get("query")?.trim().toLowerCase();

  const records = listRecords().filter((record) => {
    const matchesStatus = status ? record.status === status : true;
    const matchesStage = stage ? record.stage === stage : true;
    const matchesQuery = query
      ? record.fullName.toLowerCase().includes(query) ||
        record.email.toLowerCase().includes(query)
      : true;

    return matchesStatus && matchesStage && matchesQuery;
  });

  return NextResponse.json(records);
}

export async function POST(request: NextRequest) {
  const parsed = await readJsonBody<Partial<CreateCandidateInput>>(request);
  if (!parsed.ok) {
    return parsed.response;
  }
  const payload = parsed.data;
  const validationMessage = validateCandidatePayload(payload);

  if (validationMessage) {
    return NextResponse.json({ message: validationMessage }, { status: 400 });
  }

  const record = createRecord({
    fullName: payload.fullName!,
    email: payload.email!,
    phone: payload.phone ?? "",
    position: payload.position!,
    linkedinUrl: payload.linkedinUrl ?? "",
    cvUrl: payload.cvUrl ?? "",
    experience: payload.experience ?? "",
    status: payload.status!,
    stage: payload.stage!,
    applicationDate: payload.applicationDate!,
  });

  return NextResponse.json(record, { status: 201 });
}

function validateCandidatePayload(payload: Partial<CreateCandidateInput>) {
  if (!payload.fullName?.trim()) {
    return "Full name is required.";
  }

  if (!payload.email?.trim()) {
    return "Email is required.";
  }

  if (!payload.position?.trim()) {
    return "Position is required.";
  }

  if (!payload.applicationDate?.trim()) {
    return "Application date is required.";
  }

  if (!payload.status || !candidateStatusOptions.includes(payload.status)) {
    return "A valid status is required.";
  }

  if (!payload.stage || !candidateStageOptions.includes(payload.stage)) {
    return "A valid stage is required.";
  }

  return null;
}