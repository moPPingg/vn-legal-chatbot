import React from "react";
import { ChevronRight, FileText } from "lucide-react";

interface CitationProps {
  citation: {
    so_hieu: string;
    ten_van_ban: string;
    dieu: string;
    trang: string;
    pdf_url: string | null;
    snippet: string;
    still_valid: boolean;
  };
  onClick: () => void;
}

export default function CitationCard({ citation, onClick }: CitationProps) {
  const canOpenPdf = Boolean(citation.pdf_url);

  return (
    <div
      onClick={canOpenPdf ? onClick : undefined}
      className={`mt-2 mb-4 rounded-lg border border-gray-200 p-3 transition-colors duration-200 ${
        canOpenPdf ? "cursor-pointer hover:bg-gray-50" : "cursor-not-allowed bg-gray-50 opacity-75"
      }`}
    >
      <div className="mb-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-blue-600" />
          <span className="text-sm font-medium text-gray-800">{citation.so_hieu}</span>
        </div>
        <div className="flex items-center gap-2">
          {citation.still_valid ? (
            <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs text-green-700">
              Con hieu luc
            </span>
          ) : (
            <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs text-red-700">
              Het hieu luc
            </span>
          )}
          {!canOpenPdf && (
            <span className="rounded-full bg-gray-200 px-2 py-0.5 text-xs text-gray-600">
              Chua co PDF
            </span>
          )}
          <ChevronRight className="h-4 w-4 text-gray-400" />
        </div>
      </div>

      <div className="mb-1 text-sm font-semibold text-gray-700">{citation.dieu}</div>

      <p className="line-clamp-2 text-xs text-gray-500">{citation.snippet}</p>
    </div>
  );
}
