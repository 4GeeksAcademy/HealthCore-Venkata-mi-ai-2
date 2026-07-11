import { NextRequest, NextResponse } from "next/server";
import { getRecord, removeNote } from "@/lib/mock-store";

interface RouteContext {
  params: Promise<{ id: string; note_id: string }>;
}

export async function DELETE(_request: NextRequest, context: RouteContext) {
  const { id, note_id: noteId } = await context.params;

  if (!getRecord(id)) {
    return NextResponse.json({ message: "Candidate not found." }, { status: 404 });
  }

  const deleted = removeNote(id, noteId);

  if (!deleted) {
    return NextResponse.json({ message: "Note not found." }, { status: 404 });
  }

  return new NextResponse(null, { status: 204 });
}