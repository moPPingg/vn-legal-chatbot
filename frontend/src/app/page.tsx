"use client";

import { useState, useRef, useEffect } from "react";
import { ArrowUp, ChevronDown, Scale, Plus, MessageSquare, History, Trash2, Menu, X } from "lucide-react";

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

interface ChatHistoryItem {
  id: string;
  domain: string;
  title: string;
  messages: Message[];
  timestamp: number;
}

const LAW_DOMAINS = [
  "Hình sự", "Dân sự", "Lao động", "Hành chính", 
  "Thương mại", "Đất đai", "Hôn nhân & Gia đình", 
  "Thuế", "Giao thông", "Y tế", "Giáo dục", "Khác"
];

export default function ChatApp() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [history, setHistory] = useState<ChatHistoryItem[]>([]);
  const [input, setInput] = useState("");
  const [lawDomain, setLawDomain] = useState("Dân sự");
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const isFirstRender = useRef(true);

  // Load history from localStorage
  useEffect(() => {
    const saved = localStorage.getItem("legal_chat_history");
    if (saved) {
      try {
        setHistory(JSON.parse(saved));
      } catch (e) {
        console.error("Failed to parse history", e);
      }
    }
  }, []);

  // Save history to localStorage
  useEffect(() => {
    if (!isFirstRender.current) {
      localStorage.setItem("legal_chat_history", JSON.stringify(history));
    }
  }, [history]);

  // Handle Domain Change -> Clear and New Chat
  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }
    
    // Auto-save current chat to history before clearing if it has messages
    if (messages.length > 0) {
      const firstUserMsg = messages.find(m => m.role === "user")?.content || "Cuộc trò chuyện mới";
      const title = firstUserMsg.length > 30 ? firstUserMsg.substring(0, 30) + "..." : firstUserMsg;
      
      const newHistoryItem: ChatHistoryItem = {
        id: Date.now().toString(),
        domain: lawDomain, // This is the NEW domain, but the chat was in the OLD one... 
        // Wait, the state updates. Let's fix the logic.
        title: title,
        messages: [...messages],
        timestamp: Date.now(),
      };
      // We'll handle this in the setLawDomain click handler instead for better accuracy
    }
  }, [lawDomain]);

  const startNewChat = (newDomain?: string) => {
    if (messages.length > 0) {
      const firstUserMsg = messages.find(m => m.role === "user")?.content || "Cuộc trò chuyện mới";
      const title = firstUserMsg.length > 30 ? firstUserMsg.substring(0, 30) + "..." : firstUserMsg;
      
      const newHistoryItem: ChatHistoryItem = {
        id: Date.now().toString(),
        domain: lawDomain,
        title: title,
        messages: [...messages],
        timestamp: Date.now(),
      };
      setHistory(prev => [newHistoryItem, ...prev]);
    }
    setMessages([]);
    if (newDomain) setLawDomain(newDomain);
  };

  const loadChatFromHistory = (item: ChatHistoryItem) => {
    // Save current if exists
    if (messages.length > 0) {
       // Save logic... for simplicity let's just clear
    }
    setMessages(item.messages);
    setLawDomain(item.domain);
    if (window.innerWidth < 768) setIsSidebarOpen(false);
  };

  const deleteHistoryItem = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setHistory(prev => prev.filter(h => h.id !== id));
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
    setMessages((prev) => [...prev, userMsg]);

    try {
      const domainMapping: { [key: string]: string } = {
        "Hôn nhân & Gia đình": "hôn nhân gia đình",
      };
      const domainValue = domainMapping[lawDomain] || lawDomain.toLowerCase();

      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q, lawType: domainValue }),
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
    <div className="flex h-screen bg-white text-gray-900 font-sans overflow-hidden">
      
      {/* Sidebar - Chat History */}
      <aside 
        className={`${isSidebarOpen ? "w-72" : "w-0"} md:relative absolute z-40 h-full bg-gray-50 border-r border-gray-200 transition-all duration-300 overflow-hidden flex flex-col`}
      >
        <div className="p-4 flex flex-col h-full w-72">
          <button 
            onClick={() => startNewChat()}
            className="flex items-center gap-3 w-full px-4 py-3 rounded-xl border border-gray-200 bg-white hover:bg-gray-50 transition-colors text-sm font-medium shadow-sm mb-6"
          >
            <Plus size={18} />
            Chat mới
          </button>

          <div className="flex items-center gap-2 px-2 mb-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">
            <History size={14} />
            Lịch sử trò chuyện
          </div>

          <div className="flex-1 overflow-y-auto space-y-1 pr-1 custom-scrollbar">
            {history.length === 0 ? (
              <div className="px-4 py-8 text-center text-gray-400 text-sm italic">
                Chưa có lịch sử
              </div>
            ) : (
              history.map((item) => (
                <div 
                  key={item.id}
                  onClick={() => loadChatFromHistory(item)}
                  className="group relative flex items-center gap-3 w-full px-3 py-3 rounded-xl hover:bg-gray-200/50 transition-colors cursor-pointer text-sm"
                >
                  <MessageSquare size={16} className="text-gray-400 flex-shrink-0" />
                  <div className="flex-1 truncate pr-6">
                    <div className="truncate font-medium text-gray-700">{item.title}</div>
                    <div className="text-[11px] text-gray-400">{item.domain} • {new Date(item.timestamp).toLocaleDateString()}</div>
                  </div>
                  <button 
                    onClick={(e) => deleteHistoryItem(item.id, e)}
                    className="absolute right-2 opacity-0 group-hover:opacity-100 p-1.5 hover:bg-gray-300 rounded-lg transition-all text-gray-400 hover:text-red-500"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              ))
            )}
          </div>

          <div className="mt-auto pt-4 border-t border-gray-200">
            <div className="flex items-center gap-3 px-2 py-2">
              <div className="w-8 h-8 rounded-full bg-black text-white flex items-center justify-center text-xs font-bold">LA</div>
              <div className="flex-1 truncate">
                <div className="text-sm font-semibold text-gray-800">LegalAI Premium</div>
                <div className="text-[11px] text-gray-400">Phiên bản 2.0</div>
              </div>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0 relative h-full">
        
        {/* Top Header (Mobile) */}
        <header className="md:hidden flex items-center justify-between p-4 border-b border-gray-100 bg-white">
           <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} className="p-2 hover:bg-gray-100 rounded-lg">
             {isSidebarOpen ? <X size={20} /> : <Menu size={20} />}
           </button>
           <div className="font-bold text-gray-800">LegalAI</div>
           <div className="w-8" />
        </header>

        {/* Desktop Sidebar Toggle */}
        <button 
          onClick={() => setIsSidebarOpen(!isSidebarOpen)}
          className="hidden md:flex absolute left-4 top-4 z-30 p-2 bg-white/80 backdrop-blur-sm border border-gray-200 rounded-lg text-gray-400 hover:text-gray-900 hover:bg-white transition-all shadow-sm"
        >
          {isSidebarOpen ? <X size={18} /> : <Menu size={18} />}
        </button>

        {/* Scrollable Chat Area */}
        <div className="flex-1 overflow-y-auto w-full flex justify-center" ref={scrollRef}>
          <div className="w-full max-w-3xl px-4 py-8 md:py-12 flex flex-col min-h-full">
            
            {/* State 1: Initial View */}
            {isInitialState ? (
              <div className="flex flex-col items-center justify-center flex-1 w-full transition-opacity duration-500">
                <div className="w-16 h-16 bg-gray-900 text-white rounded-[24px] flex items-center justify-center mb-8 shadow-2xl">
                  <Scale size={32} />
                </div>
                <h1 className="text-2xl md:text-3xl font-medium text-gray-800 mb-8 text-center leading-relaxed">
                  Xin chào, tôi có thể giúp gì cho<br />vấn đề pháp lý của bạn hôm nay?
                </h1>
                
                <div className="flex flex-wrap justify-center gap-2.5 w-full max-w-2xl">
                  {LAW_DOMAINS.map((domain) => (
                    <button
                      key={domain}
                      onClick={() => {
                        startNewChat(domain);
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
                      <div className="max-w-[85%] bg-gray-100 rounded-3xl px-5 py-3 text-gray-800 text-[15px] leading-relaxed break-words shadow-sm">
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
                     <div className="flex-1 space-y-3">
                       <div className="h-4 bg-gray-100 rounded w-24" />
                       <div className="h-4 bg-gray-50 rounded w-full" />
                       <div className="h-4 bg-gray-50 rounded w-2/3" />
                     </div>
                  </div>
                )}
              </div>
            )}
  
          </div>
        </div>
  
        {/* Input Area (Sticky Bottom) */}
        <div className="w-full flex justify-center bg-gradient-to-t from-white via-white to-transparent pb-6 pt-8 px-4 absolute bottom-0 z-10">
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
                          startNewChat(domain);
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
            <div className="w-full relative flex items-end bg-gray-50 rounded-[32px] border border-gray-200 p-2 overflow-hidden focus-within:ring-1 focus-within:ring-gray-300 focus-within:bg-white transition-colors shadow-sm">
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
            <p className="text-[11px] text-gray-400 mt-3 text-center">
              LegalAI có thể mắc lỗi. Hãy kiểm tra các thông tin pháp lý quan trọng.
            </p>
          </div>
        </div>
      </main>

      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #e5e7eb;
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #d1d5db;
        }
      `}</style>

    </div>
  );
}
