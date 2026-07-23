import { NextRequest, NextResponse } from "next/server";
import { getRecord, patchRecord, replaceRecord } from "@/lib/mock-store";
import {
  candidateStageOptions,
  candidateStatusOptions,
  PatchCandidateInput,
  UpdateCandidateInput,
} from "@/types/candidate";

interface RouteContext {
  params: Promise<{ id: string }>;
}

export async function GET(_request: NextRequest, context: RouteContext) {
  const { id } = await context.params;
  const record = getRecord(id);

  if (!record) {
    return NextResponse.json({ message: "Candidate not found." }, { status: 404 });
  }

  return NextResponse.json(record);
}

export async function PUT(request: NextRequest, context: RouteContext) {
  const { id } = await context.params;
  const existingRecord = getRecord(id);

  if (!existingRecord) {
    return NextResponse.json({ message: "Candidate not found." }, { status: 404 });
  }

  const payload = (await request.json()) as Partial<UpdateCandidateInput>;
  const validationMessage = validateFullPayload(payload);

  if (validationMessage) {
    return NextResponse.json({ message: validationMessage }, { status: 400 });
  }

  const updatedRecord = replaceRecord(id, {
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

  return NextResponse.json(updatedRecord);
}

export async function PATCH(request: NextRequest, context: RouteContext) {
  const { id } = await context.params;
  const payload = (await request.json()) as PatchCandidateInput;

  if (
    payload.status !== undefined &&
    !candidateStatusOptions.includes(payload.status)
  ) {
    return NextResponse.json({ message: "A valid status is required." }, { status: 400 });
  }

  if (payload.stage !== undefined && !candidateStageOptions.includes(payload.stage)) {
    return NextResponse.json({ message: "A valid stage is required." }, { status: 400 });
  }

  const updatedRecord = patchRecord(id, payload);

  if (!updatedRecord) {
    return NextResponse.json({ message: "Candidate not found." }, { status: 404 });
  }

  return NextResponse.json(updatedRecord);
}

function validateFullPayload(payload: Partial<UpdateCandidateInput>) {
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