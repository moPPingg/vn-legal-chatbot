import { NextRequest, NextResponse } from "next/server";

const PYTHON_API = process.env.PYTHON_API_URL || "http://127.0.0.1:8000";

const DOMAIN_ALIASES: Record<string, string> = {
  hon_nhan_gia_dinh: "hon_nhan",
};

function normalizeLawType(lawType: string): string {
  const normalized = lawType
    .trim()
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/đ/g, "d")
    .replace(/&/g, " ")
    .replace(/[^\w\s]/g, " ")
    .replace(/\s+/g, "_")
    .replace(/^_+|_+$/g, "");

  return DOMAIN_ALIASES[normalized] || normalized;
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { question, lawType } = body;

    if (!question || !lawType) {
      return NextResponse.json(
        { success: false, error: "question and lawType are required" },
        { status: 400 },
      );
    }

    const res = await fetch(`${PYTHON_API}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, lawType: normalizeLawType(lawType) }),
    });

    const data = await res.json();
    return NextResponse.json(data);
  } catch (error: any) {
    console.error("API route error:", error);
    return NextResponse.json(
      {
        success: false,
        error: `Khong the ket noi toi AI server: ${error.message}`,
      },
      { status: 502 },
    );
  }
}
