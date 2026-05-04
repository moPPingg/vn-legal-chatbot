"use client";

interface Message {
  role: "user" | "bot";
  content?: string;
  data?: {
    answer: string;
    legal_basis: string[];
    confidence: string;
    note?: string;
    follow_up?: string;
  };
  sources?: string[];
  error?: string;
  lawLabel?: string;
  time: string;
}

export default function MessageBubble({ msg }: { msg: Message }) {
  if (msg.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[80%] bg-gray-900 text-white rounded-xl px-4 py-2 text-sm">
          {msg.content}
        </div>
      </div>
    );
  }

  if (msg.error) {
    return (
      <div className="flex">
        <div className="max-w-[80%] bg-white text-red-600 rounded-xl px-4 py-3 text-sm border border-red-200">
          Lỗi: {msg.error}
        </div>
      </div>
    );
  }

  const d = msg.data!;

  return (
    <div className="flex">
      <div className="max-w-[85%] bg-gray-100 text-gray-800 rounded-xl px-4 py-3 text-sm">
        <div className="whitespace-pre-wrap leading-relaxed">{d.answer}</div>
        
        {d.legal_basis && d.legal_basis.length > 0 && (
          <div className="mt-3 pt-3 border-t border-gray-200">
            <p className="text-xs font-medium text-gray-500 mb-1">Cơ sở pháp lý:</p>
            <div className="flex flex-col gap-1">
              {d.legal_basis.map((b, i) => (
                <span key={i} className="text-xs text-gray-500">{b}</span>
              ))}
            </div>
          </div>
        )}

        {msg.sources && msg.sources.length > 0 && (
          <details className="mt-3">
            <summary className="text-xs text-gray-500 font-medium cursor-pointer hover:text-gray-900 transition-colors">
              Nguồn tham khảo
            </summary>
            <ul className="mt-2 space-y-1">
              {msg.sources.map((s, i) => (
                <li key={i} className="text-xs text-gray-500 break-words">
                  • {s}
                </li>
              ))}
            </ul>
          </details>
        )}
      </div>
    </div>
  );
}
