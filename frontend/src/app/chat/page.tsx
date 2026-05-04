"use client";

import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import ChatBox from "@/components/ChatBox";

const LAW_LABELS: Record<string, string> = {
  "hình sự": "Hình sự",
  "dân sự": "Dân sự",
  "lao động": "Lao động",
  "hành chính": "Hành chính",
  "thương mại": "Thương mại",
  "đất đai": "Đất đai",
  "hôn nhân gia đình": "Hôn nhân & Gia đình",
  "thuế": "Thuế",
  "giao thông": "Giao thông",
  "y tế": "Y tế",
  "giáo dục": "Giáo dục",
  "khác": "Khác",
};

function ChatContent() {
  const params = useSearchParams();
  const lawType = params.get("law") || "khác";
  const lawLabel = LAW_LABELS[lawType] || lawType;

  return (
    <div className="flex-1 flex flex-col py-12 max-w-3xl mx-auto w-full px-4 min-h-[calc(100vh-64px)]">
      {/* Top bar */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-sm font-medium text-gray-500">
          Lĩnh vực: {lawLabel}
        </h2>
        <a href="/" className="text-sm text-gray-500 hover:text-gray-900 transition-colors">
          Đổi lĩnh vực
        </a>
      </div>
      <ChatBox lawType={lawType} lawLabel={lawLabel} />
    </div>
  );
}

export default function ChatPage() {
  return (
    <Suspense fallback={<div className="flex-1 flex items-center justify-center text-gray-400 min-h-[calc(100vh-64px)]">Đang tải...</div>}>
      <ChatContent />
    </Suspense>
  );
}
