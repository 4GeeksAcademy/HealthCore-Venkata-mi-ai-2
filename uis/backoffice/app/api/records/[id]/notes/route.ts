import { NextRequest, NextResponse } from "next/server";
import { addNote, getRecord, listNotes } from "@/lib/mock-store";
import { readJsonBody } from "@/lib/read-json-body";

interface RouteContext {
  params: Promise<{ id: string }>;
}

export async function GET(_request: NextRequest, context: RouteContext) {
  const { id } = await context.params;

  if (!getRecord(id)) {
    return NextResponse.json({ message: "Candidate not found." }, { status: 404 });
  }

  return NextResponse.json(listNotes(id));
}

export async function POST(request: NextRequest, context: RouteContext) {
  const { id } = await context.params;

  if (!getRecord(id)) {
    return NextResponse.json({ message: "Candidate not found." }, { status: 404 });
  }

  const parsed = await readJsonBody<{ content?: string; author?: string }>(request);
  if (!parsed.ok) {
    return parsed.response;
  }
  const payload = parsed.data;

  if (!payload.content?.trim()) {
    return NextResponse.json({ message: "Note content is required." }, { status: 400 });
  }

  const note = addNote(id, {
    recordId: id,
    content: payload.content.trim(),
    author: payload.author?.trim() || "Hiring Team",
  });

  return NextResponse.json(note, { status: 201 });
}