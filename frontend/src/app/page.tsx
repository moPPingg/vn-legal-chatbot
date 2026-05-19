"use client";

import { useState, useRef, useEffect } from "react";
import { ArrowUp, ChevronDown, Scale, FileText, Plus, MessageSquare, Trash2 } from "lucide-react";
import CitationCard from "@/components/DocumentViewer/CitationCard";
import dynamic from 'next/dynamic';

const PdfPanel = dynamic(() => import('@/components/DocumentViewer/PdfPanel'), {
  ssr: false,
});

interface Message {
  role: "user" | "bot";
  content?: string;
  data?: {
    answer: string;
    summary?: string;
    legal_basis?: string[];
    citations?: any[];
    confidence: string;
    note?: string;
    follow_up?: string;
  };
  sources?: string[];
  error?: string;
}

interface ChatSession {
  id: string;
  title: string;
  domain: string;
  messages: Message[];
}

const LAW_DOMAINS = [
  "Hình sự", "Dân sự", "Lao động", "Hành chính", 
  "Thương mại", "Đất đai", "Hôn nhân & Gia đình", 
  "Thuế", "Giao thông", "Y tế", "Giáo dục", "Khác"
];

export default function ChatApp() {
  const [sessions, setSessions] = useState<ChatSession[]>([
    { id: "1", title: "Cuộc trò chuyện mới", domain: "Dân sự", messages: [] }
  ]);
  const [activeSessionId, setActiveSessionId] = useState("1");
  const [input, setInput] = useState("");
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  
  // Document Viewer state
  const [isPdfPanelOpen, setIsPdfPanelOpen] = useState(false);
  const [pdfUrl, setPdfUrl] = useState("");
  const [pdfTitle, setPdfTitle] = useState("");
  const [pdfPage, setPdfPage] = useState(1);
  
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const activeSession = sessions.find(s => s.id === activeSessionId) || sessions[0];
  const messages = activeSession.messages;
  const lawDomain = activeSession.domain;

  const updateActiveSession = (updates: Partial<ChatSession>) => {
    setSessions(prev => prev.map(s => s.id === activeSessionId ? { ...s, ...updates } : s));
  };

  const createNewChat = () => {
    const newId = Date.now().toString();
    setSessions(prev => [
      { id: newId, title: "Cuộc trò chuyện mới", domain: "Dân sự", messages: [] },
      ...prev
    ]);
    setActiveSessionId(newId);
  };

  const deleteSession = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setSessions(prev => {
      const newSessions = prev.filter(s => s.id !== id);
      if (newSessions.length === 0) {
        const newId = Date.now().toString();
        setActiveSessionId(newId);
        return [{ id: newId, title: "Cuộc trò chuyện mới", domain: "Dân sự", messages: [] }];
      }
      if (id === activeSessionId) {
        setActiveSessionId(newSessions[0].id);
      }
      return newSessions;
    });
  };

  const handleDomainChange = (newDomain: string) => {
    if (messages.length > 0) {
      const newId = Date.now().toString();
      setSessions(prev => [
        { id: newId, title: "Cuộc trò chuyện mới", domain: newDomain, messages: [] },
        ...prev
      ]);
      setActiveSessionId(newId);
    } else {
      updateActiveSession({ domain: newDomain });
    }
  };

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
    
    let newTitle = activeSession.title;
    if (messages.length === 0) {
      newTitle = q.length > 30 ? q.substring(0, 30) + "..." : q;
    }

    updateActiveSession({ 
      title: newTitle,
      messages: [...messages, userMsg] 
    });

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: q,
          lawType: lawDomain
            .toLowerCase()
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .replace(/đ/g, "d")
            .replace(/&/g, " ")
            .replace(/[^\w\s]/g, " ")
            .replace(/\s+/g, "_")
            .replace(/^_+|_+$/g, ""),
        }),
      });
      const result = await res.json();
      
      setSessions(prev => prev.map(s => {
        if (s.id !== activeSessionId) return s;
        const newMessages = [...s.messages];
        if (result.success && result.data) {
          newMessages.push({ role: "bot", data: result.data, sources: result.sources });
        } else {
          newMessages.push({ role: "bot", error: result.error || "Lỗi hệ thống" });
        }
        return { ...s, messages: newMessages };
      }));
    } catch (err: any) {
      setSessions(prev => prev.map(s => {
        if (s.id !== activeSessionId) return s;
        return { ...s, messages: [...s.messages, { role: "bot", error: err.message || "Không thể kết nối máy chủ" }] };
      }));
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
    <div className="flex h-screen bg-white text-gray-900 font-sans overflow-hidden">
      
      {/* Sidebar */}
      <div className="w-64 bg-gray-50 border-r border-gray-200 flex flex-col h-full hidden md:flex shrink-0">
        <div className="p-4">
          <button 
            onClick={createNewChat}
            className="flex items-center gap-2 w-full px-4 py-2.5 bg-black text-white rounded-xl hover:bg-gray-800 transition-colors text-sm font-medium shadow-sm"
          >
            <Plus size={16} />
            Đoạn chat mới
          </button>
        </div>
        <div className="flex-1 overflow-y-auto px-3 pb-4">
          <div className="text-[11px] font-bold text-gray-400 mb-3 mt-2 px-2 uppercase tracking-wider">Lịch sử</div>
          {sessions.map(s => (
            <div
              key={s.id}
              onClick={() => setActiveSessionId(s.id)}
              className={`group w-full cursor-pointer text-left px-3 py-2.5 rounded-xl mb-1.5 flex items-center gap-2.5 transition-colors text-sm relative
                ${s.id === activeSessionId ? 'bg-gray-200 text-gray-900 font-medium' : 'text-gray-600 hover:bg-gray-100'}`}
            >
              <MessageSquare size={15} className={s.id === activeSessionId ? "text-gray-700" : "text-gray-400"} />
              <div className="truncate flex-1 pr-6">{s.title}</div>
              <button
                onClick={(e) => deleteSession(s.id, e)}
                className={`absolute right-2 p-1.5 rounded-md hover:bg-gray-300 transition-opacity opacity-0 group-hover:opacity-100 flex items-center justify-center
                  ${s.id === activeSessionId ? "text-gray-700 hover:text-red-600" : "text-gray-400 hover:text-red-600"}`}
                title="Xóa đoạn chat"
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex flex-col h-full flex-1 min-w-0 transition-all duration-300">
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
                      handleDomainChange(domain);
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
                            <div className="rounded-2xl border border-gray-100 bg-gray-50 px-4 py-3">
                              <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
                                Tom tat AI
                              </div>
                              <div className="whitespace-pre-wrap">{msg.data?.summary || msg.data?.answer}</div>
                            </div>

                            {msg.data?.note && (
                              <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
                                {msg.data.note}
                              </div>
                            )}
                            
                            {msg.data?.citations && msg.data.citations.length > 0 && (
                              <div className="mt-4 pt-4 border-t border-gray-100">
                                <p className="text-sm font-semibold text-gray-800 mb-2">Cơ sở pháp lý:</p>
                                <div className="space-y-2">
                                  {msg.data.citations.map((cit: any, i: number) => (
                                    <CitationCard 
                                      key={i} 
                                      citation={cit} 
                                      onClick={() => {
                                        if (!cit.pdf_url) {
                                          return;
                                        }
                                        setPdfUrl(`${cit.pdf_url}${cit.pdf_url.includes("?") ? "&" : "?"}v=${Date.now()}`);
                                        setPdfTitle(`${cit.so_hieu} - ${cit.dieu}`);
                                        setPdfPage(cit.trang ? parseInt(cit.trang) : 1);
                                        setIsPdfPanelOpen(true);
                                      }}
                                    />
                                  ))}
                                </div>
                              </div>
                            )}

                            {!msg.data?.citations && msg.data?.legal_basis && msg.data.legal_basis.length > 0 && (
                              <div className="mt-4 pt-4 border-t border-gray-100">
                                <p className="text-sm font-semibold text-gray-800 mb-2">Cơ sở pháp lý (cũ):</p>
                                <ul className="list-disc pl-5 space-y-1">
                                  {msg.data.legal_basis.map((basis: string, i: number) => (
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
                        handleDomainChange(domain);
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

      {/* Document Viewer Panel */}
      <div className={`h-full transition-all duration-300 ${isPdfPanelOpen ? 'w-[400px] lg:w-[500px] border-l border-gray-200' : 'w-0 overflow-hidden'}`}>
        <PdfPanel 
          isOpen={isPdfPanelOpen} 
          onClose={() => setIsPdfPanelOpen(false)} 
          pdfUrl={pdfUrl} 
          title={pdfTitle} 
          initialPage={pdfPage}
        />
      </div>

    </div>
  );
}
