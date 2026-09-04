"use client";

import React, { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { chat, ChatResponse, LoginResponse, SourceInfo } from "@/lib/api";

const ROLE_COLORS: Record<string, string> = {
  doctor: "bg-blue-100 text-blue-800",
  nurse: "bg-green-100 text-green-800",
  billing_executive: "bg-purple-100 text-purple-800",
  technician: "bg-orange-100 text-orange-800",
  admin: "bg-red-100 text-red-800",
};

const ROLE_ICONS: Record<string, string> = {
  doctor: "🩺",
  nurse: "💉",
  billing_executive: "💰",
  technician: "🔧",
  admin: "🛡️",
};

const COLLECTION_LABELS: Record<string, string> = {
  general: "📋 General",
  clinical: "🏥 Clinical",
  nursing: "💊 Nursing",
  billing: "💰 Billing",
  equipment: "🔧 Equipment",
};

const RETRIEVAL_BADGES: Record<string, { label: string; className: string }> = {
  hybrid_rag: {
    label: "Hybrid RAG",
    className: "bg-emerald-100 text-emerald-700",
  },
  sql_rag: {
    label: "SQL RAG",
    className: "bg-violet-100 text-violet-700",
  },
};

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: SourceInfo[];
  retrieval_type?: string;
  timestamp: Date;
}

interface ChatInterfaceProps {
  user: LoginResponse;
  onLogout: () => void;
}

export default function ChatInterface({ user, onLogout }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content: `Hello, **${user.full_name}**! I'm MediBot, your AI assistant at MediAssist Health Network.\n\nYou're logged in as **${user.role.replace("_", " ")}** with access to: ${user.collections.map((c) => `**${c}**`).join(", ")} collections.\n\nHow can I help you today?`,
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    const question = input.trim();
    if (!question || loading) return;

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content: question,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const response: ChatResponse = await chat(question, user.access_token);
      const assistantMsg: Message = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: response.answer,
        sources: response.sources,
        retrieval_type: response.retrieval_type,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: unknown) {
      const errorMsg: Message = {
        id: `error-${Date.now()}`,
        role: "assistant",
        content: `⚠️ ${err instanceof Error ? err.message : "Something went wrong. Please try again."}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="h-screen flex bg-slate-50">
      {/* Sidebar */}
      <aside className="w-72 bg-slate-900 text-white flex flex-col shrink-0">
        {/* Logo */}
        <div className="p-5 border-b border-slate-700">
          <div className="flex items-center gap-3">
            <span className="text-3xl">🏥</span>
            <div>
              <h1 className="text-lg font-bold">MediBot</h1>
              <p className="text-slate-400 text-xs">MediAssist Health Network</p>
            </div>
          </div>
        </div>

        {/* User Info */}
        <div className="p-5 border-b border-slate-700">
          <div className="flex items-center gap-3 mb-3">
            <span className="text-2xl">{ROLE_ICONS[user.role] || "👤"}</span>
            <div>
              <div className="font-medium text-sm">{user.full_name}</div>
              <div className="text-slate-400 text-xs">@{user.username}</div>
            </div>
          </div>
          <span
            className={`inline-block px-2.5 py-1 rounded-full text-xs font-medium ${ROLE_COLORS[user.role]}`}
          >
            {user.role.replace("_", " ")}
          </span>
        </div>

        {/* Accessible Collections */}
        <div className="p-5 flex-1">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
            Your Collections
          </h3>
          <div className="space-y-1.5">
            {user.collections.map((col) => (
              <div
                key={col}
                className="flex items-center gap-2 px-3 py-2 bg-slate-800 rounded-lg text-sm"
              >
                <span>{COLLECTION_LABELS[col]?.split(" ")[0] || "📁"}</span>
                <span className="capitalize">{col}</span>
              </div>
            ))}
          </div>

          {user.role === "billing_executive" || user.role === "admin" ? (
            <div className="mt-4 px-3 py-2 bg-violet-900/40 border border-violet-700/50 rounded-lg">
              <div className="text-xs font-medium text-violet-300">
                🗄️ SQL RAG Enabled
              </div>
              <div className="text-xs text-violet-400 mt-0.5">
                Ask analytical questions about claims & maintenance data
              </div>
            </div>
          ) : null}
        </div>

        {/* Logout */}
        <div className="p-5 border-t border-slate-700">
          <button
            onClick={onLogout}
            className="w-full px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm transition"
          >
            Sign Out
          </button>
        </div>
      </aside>

      {/* Chat Area */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          <div className="max-w-3xl mx-auto space-y-4">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[85%] ${
                    msg.role === "user"
                      ? "bg-blue-600 text-white rounded-2xl rounded-br-md px-4 py-3"
                      : "bg-white shadow-sm border border-slate-200 rounded-2xl rounded-bl-md px-5 py-4"
                  }`}
                >
                  {/* Retrieval type badge */}
                  {msg.retrieval_type && (
                    <div className="mb-2">
                      <span
                        className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${
                          RETRIEVAL_BADGES[msg.retrieval_type]?.className ||
                          "bg-gray-100 text-gray-600"
                        }`}
                      >
                        {RETRIEVAL_BADGES[msg.retrieval_type]?.label || msg.retrieval_type}
                      </span>
                    </div>
                  )}

                  {/* Message content */}
                  <div
                    className={`${msg.role === "assistant" ? "markdown-content text-slate-700" : ""} text-sm leading-relaxed`}
                  >
                    {msg.role === "assistant" ? (
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                    ) : (
                      msg.content
                    )}
                  </div>

                  {/* Source citations */}
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-slate-100">
                      <div className="text-xs font-semibold text-slate-500 mb-1.5">
                        📚 Sources
                      </div>
                      <div className="space-y-1">
                        {msg.sources.map((source, idx) => (
                          <div
                            key={idx}
                            className="flex items-start gap-2 text-xs text-slate-500 bg-slate-50 px-2.5 py-1.5 rounded-md"
                          >
                            <span className="text-slate-400 mt-0.5">•</span>
                            <div>
                              <span className="font-medium text-slate-600">
                                {source.source_document}
                              </span>
                              {source.section_title && (
                                <span className="text-slate-400">
                                  {" — "}
                                  {source.section_title}
                                </span>
                              )}
                              <span
                                className={`ml-1.5 inline-block px-1.5 py-0 rounded text-[10px] font-medium ${
                                  ROLE_COLORS[source.collection] ||
                                  "bg-slate-100 text-slate-500"
                                }`}
                              >
                                {source.collection}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Timestamp */}
                  <div
                    className={`text-[10px] mt-2 ${
                      msg.role === "user" ? "text-blue-200" : "text-slate-400"
                    }`}
                  >
                    {msg.timestamp.toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </div>
                </div>
              </div>
            ))}

            {/* Loading indicator */}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-white shadow-sm border border-slate-200 rounded-2xl rounded-bl-md px-5 py-4">
                  <div className="flex items-center gap-2 text-slate-400 text-sm">
                    <div className="flex gap-1">
                      <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce [animation-delay:0ms]"></span>
                      <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce [animation-delay:150ms]"></span>
                      <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce [animation-delay:300ms]"></span>
                    </div>
                    <span>MediBot is thinking...</span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Area */}
        <div className="border-t border-slate-200 bg-white px-6 py-4">
          <div className="max-w-3xl mx-auto">
            <div className="flex gap-3 items-end">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask MediBot a question..."
                rows={1}
                className="flex-1 resize-none border border-slate-300 rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition max-h-32 overflow-y-auto"
                style={{
                  height: "auto",
                  minHeight: "44px",
                }}
                onInput={(e) => {
                  const target = e.target as HTMLTextAreaElement;
                  target.style.height = "auto";
                  target.style.height = `${Math.min(target.scrollHeight, 128)}px`;
                }}
              />
              <button
                onClick={handleSend}
                disabled={!input.trim() || loading}
                className="px-5 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-medium text-sm transition disabled:opacity-40 disabled:cursor-not-allowed shrink-0"
              >
                {loading ? "..." : "Send"}
              </button>
            </div>
            <div className="text-xs text-slate-400 mt-2 text-center">
              Press Enter to send • Shift+Enter for new line
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
