"use client";

import { useState, useRef, useEffect } from "react";
import MessageBubble from "./MessageBubble";

interface Message {
  role: "user" | "bot";
  content?: string;
  data?: { answer: string; legal_basis: string[]; confidence: string; note?: string; follow_up?: string };
  sources?: string[];
  error?: string;
  lawLabel?: string;
  time: string;
}

export default function ChatBox({ lawType, lawLabel }: { lawType: string; lawLabel: string }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    setTimeout(() => scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" }), 50);
  };

  useEffect(scrollToBottom, [messages]);

  const now = () => new Date().toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" });

  const handleSend = async () => {
    const q = input.trim();
    if (!q || loading) return;
    setInput("");
    setLoading(true);

    const userMsg: Message = { role: "user", content: q, lawLabel, time: now() };
    setMessages((prev) => [...prev, userMsg]);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q, lawType }),
      });
      const result = await res.json();
      if (result.success && result.data) {
        setMessages((prev) => [...prev, { role: "bot", data: result.data, sources: result.sources, time: now() }]);
      } else {
        setMessages((prev) => [...prev, { role: "bot", error: result.error || "Lỗi hệ thống", time: now() }]);
      }
    } catch (err: any) {
      setMessages((prev) => [...prev, { role: "bot", error: err.message || "Không thể kết nối máy chủ", time: now() }]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  return (
    <div className="flex-1 flex flex-col bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-6 flex flex-col gap-6 min-h-[400px] max-h-[70vh]">
        {messages.length === 0 && (
          <div className="flex-1 flex flex-col items-center justify-center text-center py-12">
            <p className="text-gray-500 text-sm">Chưa có dữ liệu hội thoại.</p>
          </div>
        )}

        {messages.map((msg, i) => <MessageBubble key={i} msg={msg} />)}

        {loading && (
          <div className="flex">
            <div className="bg-gray-100 rounded-xl px-4 py-3 text-sm text-gray-500">
              Đang xử lý...
            </div>
          </div>
        )}
      </div>

      <div className="p-4 border-t border-gray-200 bg-white">
        <div className="relative flex items-end">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={1}
            placeholder="Nhập câu hỏi pháp luật..."
            className="w-full border border-gray-300 rounded-lg px-4 py-3 pr-12 text-gray-900 resize-none focus:outline-none focus:border-gray-500 focus:ring-0 transition-colors text-sm"
            style={{ height: "auto", minHeight: "46px" }}
            onInput={(e) => {
              const t = e.currentTarget;
              t.style.height = "auto";
              t.style.height = Math.min(t.scrollHeight, 120) + "px";
            }}
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="absolute right-2 bottom-2 text-gray-500 hover:text-gray-900 disabled:opacity-40 disabled:cursor-not-allowed p-2 cursor-pointer"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="19" x2="12" y2="5"></line><polyline points="5 12 12 5 19 12"></polyline></svg>
          </button>
        </div>
      </div>
    </div>
  );
}
