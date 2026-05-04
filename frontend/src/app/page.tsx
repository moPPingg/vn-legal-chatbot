"use client";

import { useState, useRef, useEffect } from "react";
import { ArrowUp, ChevronDown, Scale } from "lucide-react";

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
}

const LAW_DOMAINS = [
  "Hình sự", "Dân sự", "Lao động", "Hành chính", 
  "Thương mại", "Đất đai", "Hôn nhân & Gia đình", 
  "Thuế", "Giao thông", "Y tế", "Giáo dục", "Khác"
];

export default function ChatApp() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [lawDomain, setLawDomain] = useState("Dân sự");
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSend = async () => {
    const q = input.trim();
    if (!q || loading) return;
    
    setInput("");
    setLoading(true);
    setIsDropdownOpen(false);

    const userMsg: Message = { role: "user", content: q };
    setMessages((prev) => [...prev, userMsg]);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q, lawType: lawDomain.toLowerCase() }),
      });
      const result = await res.json();
      if (result.success && result.data) {
        setMessages((prev) => [...prev, { role: "bot", data: result.data, sources: result.sources }]);
      } else {
        setMessages((prev) => [...prev, { role: "bot", error: result.error || "Lỗi hệ thống" }]);
      }
    } catch (err: any) {
      setMessages((prev) => [...prev, { role: "bot", error: err.message || "Không thể kết nối máy chủ" }]);
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 10);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const isInitialState = messages.length === 0;

  return (
    <div className="flex flex-col h-screen bg-white text-gray-900 font-sans">
      
      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto w-full flex justify-center" ref={scrollRef}>
        <div className="w-full max-w-3xl px-4 py-8 md:py-12 flex flex-col min-h-full">
          
          {/* State 1: Initial View */}
          {isInitialState ? (
            <div className="flex flex-col items-center justify-center flex-1 w-full transition-opacity duration-500">
              <h1 className="text-2xl md:text-3xl font-medium text-gray-800 mb-8 text-center leading-relaxed">
                Xin chào, tôi có thể giúp gì cho<br />vấn đề pháp lý của bạn hôm nay?
              </h1>
              
              <div className="flex flex-wrap justify-center gap-2.5 w-full max-w-2xl">
                {LAW_DOMAINS.map((domain) => (
                  <button
                    key={domain}
                    onClick={() => {
                      setLawDomain(domain);
                      inputRef.current?.focus();
                    }}
                    className={`px-4 py-2 rounded-full border transition-all text-sm font-medium
                      ${lawDomain === domain 
                        ? "bg-gray-100 text-gray-900 border-gray-200" 
                        : "bg-white border-gray-200 text-gray-600 hover:bg-gray-50"
                      }`}
                  >
                    {domain}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            /* State 2: Chat View */
            <div className="flex flex-col gap-8 w-full pb-32">
              {messages.map((msg, idx) => (
                <div key={idx} className={`flex w-full ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                  
                  {msg.role === "user" ? (
                    <div className="max-w-[85%] bg-gray-100 rounded-3xl px-5 py-3 text-gray-800 text-[15px] leading-relaxed break-words">
                      {msg.content}
                    </div>
                  ) : (
                    <div className="flex gap-4 w-full max-w-[95%]">
                      <div className="w-8 h-8 rounded-full flex-shrink-0 border border-gray-200 flex items-center justify-center text-gray-700 mt-1 bg-white shadow-sm">
                        <Scale size={14} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="font-semibold text-gray-800 mb-1 text-sm">LegalAI</div>
                        
                        {msg.error ? (
                          <div className="text-red-600 text-[15px] leading-relaxed">{msg.error}</div>
                        ) : (
                          <div className="text-gray-800 text-[15px] leading-relaxed space-y-4">
                            <div className="whitespace-pre-wrap">{msg.data?.answer}</div>
                            
                            {msg.data?.legal_basis && msg.data.legal_basis.length > 0 && (
                              <div className="mt-4 pt-4 border-t border-gray-100">
                                <p className="text-sm font-semibold text-gray-800 mb-2">Cơ sở pháp lý:</p>
                                <ul className="list-disc pl-5 space-y-1">
                                  {msg.data.legal_basis.map((basis, i) => (
                                    <li key={i} className="text-sm text-gray-600">{basis}</li>
                                  ))}
                                </ul>
                              </div>
                            )}

                            {msg.sources && msg.sources.length > 0 && (
                              <details className="mt-3 group">
                                <summary className="text-sm text-gray-500 font-medium cursor-pointer hover:text-gray-900 transition-colors list-none flex items-center gap-1.5">
                                  <ChevronDown size={14} className="group-open:rotate-180 transition-transform" />
                                  Nguồn tham khảo
                                </summary>
                                <ul className="mt-3 pl-6 space-y-2 border-l-2 border-gray-100">
                                  {msg.sources.map((s, i) => (
                                    <li key={i} className="text-[13px] text-gray-500 break-words">{s}</li>
                                  ))}
                                </ul>
                              </details>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                </div>
              ))}
              
              {loading && (
                <div className="flex gap-4 w-full max-w-[95%] animate-pulse">
                   <div className="w-8 h-8 rounded-full border border-gray-200 bg-gray-50 flex-shrink-0" />
                   <div className="h-4 bg-gray-100 rounded w-24 mt-2" />
                </div>
              )}
            </div>
          )}

        </div>
      </div>

      {/* Input Area (Sticky Bottom) */}
      <div className="w-full flex justify-center bg-gradient-to-t from-white via-white to-transparent pb-6 pt-8 px-4">
        <div className="w-full max-w-3xl relative flex flex-col items-center">
          
          {/* Domain Switcher */}
          <div className="relative mb-3 z-10 w-full flex justify-center" ref={dropdownRef}>
            <button
              onClick={() => setIsDropdownOpen(!isDropdownOpen)}
              className="flex items-center gap-2 px-4 py-1.5 rounded-full bg-white border border-gray-200 text-gray-700 text-sm font-medium hover:bg-gray-50 transition-colors shadow-sm"
            >
              <Scale size={14} className="text-gray-500" />
              Lĩnh vực: {lawDomain}
              <ChevronDown size={14} className={`text-gray-400 transition-transform ${isDropdownOpen ? "rotate-180" : ""}`} />
            </button>

            {isDropdownOpen && (
              <div className="absolute bottom-full mb-2 w-56 bg-white border border-gray-100 rounded-2xl shadow-xl overflow-hidden p-1 z-50">
                <div className="max-h-60 overflow-y-auto">
                  {LAW_DOMAINS.map((domain) => (
                    <button
                      key={domain}
                      onClick={() => {
                        setLawDomain(domain);
                        setIsDropdownOpen(false);
                        inputRef.current?.focus();
                      }}
                      className={`w-full text-left px-4 py-2.5 text-sm rounded-xl transition-colors
                        ${lawDomain === domain ? "bg-gray-50 font-medium text-gray-900" : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"}
                      `}
                    >
                      {domain}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Input Box */}
          <div className="w-full relative flex items-end bg-gray-50 rounded-[32px] border border-gray-200 p-2 overflow-hidden focus-within:ring-1 focus-within:ring-gray-300 focus-within:bg-white transition-colors">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Nhập câu hỏi pháp luật..."
              rows={1}
              className="w-full max-h-[200px] bg-transparent border-none outline-none focus:ring-0 resize-none px-4 py-3 text-[15px] leading-relaxed text-gray-900 placeholder-gray-500"
              style={{ height: "auto", minHeight: "48px" }}
              onInput={(e) => {
                const target = e.target as HTMLTextAreaElement;
                target.style.height = "auto";
                target.style.height = `${Math.min(target.scrollHeight, 200)}px`;
              }}
            />
            
            <div className="absolute right-3 bottom-3 flex items-center justify-center">
              <button
                onClick={handleSend}
                disabled={loading || !input.trim()}
                className={`w-9 h-9 flex items-center justify-center rounded-full transition-all flex-shrink-0
                  ${input.trim() && !loading 
                    ? "bg-black text-white hover:bg-gray-800" 
                    : "bg-gray-200 text-gray-400 cursor-not-allowed"}`}
              >
                <ArrowUp size={18} strokeWidth={2.5} />
              </button>
            </div>
          </div>
          <p className="text-xs text-gray-400 mt-3 text-center">
            LegalAI có thể mắc lỗi. Hãy kiểm tra các thông tin pháp lý quan trọng.
          </p>
        </div>
      </div>

    </div>
  );
}
