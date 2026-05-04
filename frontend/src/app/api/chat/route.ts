import { NextRequest, NextResponse } from "next/server";

const PYTHON_API = process.env.PYTHON_API_URL || "http://localhost:8000";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { question, lawType } = body;

    if (!question || !lawType) {
      return NextResponse.json(
        { success: false, error: "question and lawType are required" },
        { status: 400 }
      );
    }

    // Forward to Python FastAPI
    const res = await fetch(`${PYTHON_API}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, lawType }),
    });

    const data = await res.json();
    return NextResponse.json(data);
  } catch (error: any) {
    console.error("API route error:", error);
    return NextResponse.json(
      {
        success: false,
        error: `Không thể kết nối tới AI server: ${error.message}`,
      },
      { status: 502 }
    );
  }
}
