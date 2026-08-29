import { NextRequest, NextResponse } from "next/server";

export async function readJsonBody<T>(
  request: NextRequest,
): Promise<{ ok: true; data: T } | { ok: false; response: NextResponse }> {
  try {
    const data = (await request.json()) as T;
    return { ok: true, data };
  } catch {
    return {
      ok: false,
      response: NextResponse.json(
        { message: "Request body must be valid JSON." },
        { status: 400 },
      ),
    };
  }
}
