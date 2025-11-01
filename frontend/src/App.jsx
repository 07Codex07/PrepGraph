<<<<<<< HEAD
import React, { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export default function App() {
  const [userId, setUserId] = useState("vinayak");
  const [message, setMessage] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const chatContainerRef = useRef(null);

  const API_BASE = "http://127.0.0.1:8000";

  // Auto scroll to bottom when new messages come
  useEffect(() => {
    chatContainerRef.current?.scrollTo({
      top: chatContainerRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [chatHistory]);

  // ✅ Fetch previous chat history on load
  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await fetch(`${API_BASE}/history/${userId}`);
        if (!res.ok) throw new Error("Failed to fetch history");
        const data = await res.json();
        setChatHistory(data.history || []);
      } catch (err) {
        console.error("History fetch failed:", err);
      }
    };

    fetchHistory();
  }, [userId]);

  const sendMessage = async () => {
    const userMessage = message.trim();
    if (!userMessage) return;

    setMessage("");
    setError("");
    setChatHistory((prev) => [...prev, { role: "user", content: userMessage }]);
    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, message: userMessage }),
      });

      if (!response.ok) throw new Error(`Server error: ${response.status}`);
=======
import { useState, useEffect, useRef } from 'react';

function App() {
  const [userId, setUserId] = useState('vinayak');
  const [message, setMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatHistory]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const sendMessage = async () => {
    if (!message.trim() || !userId.trim() || isLoading) return;

    const userMessage = message.trim();
    setMessage('');
    setError('');

    setChatHistory((prev) => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);

    try {
      const response = await fetch('http://127.0.0.1:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          message: userMessage,
        }),
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

>>>>>>> 81b52b1b6a4f7744a4006e1777e5dc890a50d9cb
      const data = await response.json();

      setChatHistory((prev) => [
        ...prev,
<<<<<<< HEAD
        { role: "assistant", content: data.assistant },
      ]);
    } catch (err) {
      setError("Server error. Try again.");
      console.error("Error:", err);
=======
        { role: 'assistant', content: data.assistant },
      ]);
    } catch (err) {
      setError('⚠️ Server error, please try again');
      console.error('Error:', err);
>>>>>>> 81b52b1b6a4f7744a4006e1777e5dc890a50d9cb
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
<<<<<<< HEAD
    if (e.key === "Enter" && !e.shiftKey) {
=======
    if (e.key === 'Enter' && !e.shiftKey) {
>>>>>>> 81b52b1b6a4f7744a4006e1777e5dc890a50d9cb
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = async () => {
<<<<<<< HEAD
    try {
      await fetch(`${API_BASE}/memory/clear`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId }),
      });
      setChatHistory([]);
    } catch (err) {
      console.error("Error clearing chat:", err);
=======
    if (!userId.trim()) return;

    try {
      const response = await fetch('http://127.0.0.1:8000/memory/clear', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
        }),
      });

      if (response.ok) {
        setChatHistory([]);
        setError('');
      }
    } catch (err) {
      console.error('Error clearing chat:', err);
>>>>>>> 81b52b1b6a4f7744a4006e1777e5dc890a50d9cb
    }
  };

  return (
<<<<<<< HEAD
    <div className="flex flex-col h-screen bg-[#0d0d0d] text-gray-100">
      {/* Header */}
      <header className="flex justify-between items-center px-6 py-3 border-b border-gray-800 bg-[#0d0d0d]">
        <h1 className="text-2xl font-bold text-white">PrepGraph</h1>
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-300">User:</label>
          <input
            type="text"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            className="px-2 py-1 bg-gray-900 border border-gray-700 rounded text-white text-sm focus:outline-none focus:ring focus:ring-blue-600"
          />
          <button
            onClick={clearChat}
            className="px-3 py-1 bg-gray-800 hover:bg-gray-700 rounded text-white text-sm"
          >
            Clear
          </button>
        </div>
      </header>

      {/* Chat Area */}
      <main
        ref={chatContainerRef}
        className="flex-1 overflow-y-auto px-6 py-4 space-y-4"
        style={{ paddingBottom: "100px" }}
      >
        {chatHistory.map((msg, i) => (
          <div
            key={i}
            className={`flex ${
              msg.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            <div
              className={`max-w-[75%] px-5 py-3 rounded-2xl leading-relaxed ${
                msg.role === "user"
                  ? "bg-blue-600 text-white"
                  : "bg-[#1a1a1a] border border-gray-700 text-gray-100"
              }`}
            >
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  p: ({ node, ...props }) => <p className="mb-2" {...props} />,
                  strong: ({ node, ...props }) => (
                    <strong className="text-blue-400" {...props} />
                  ),
                  li: ({ node, ...props }) => (
                    <li className="ml-4 list-disc" {...props} />
                  ),
                }}
              >
                {msg.content}
              </ReactMarkdown>
            </div>
          </div>
        ))}
        {isLoading && <p className="text-gray-400 italic">Thinking...</p>}
        {error && <p className="text-red-500">{error}</p>}
      </main>

      {/* Floating Input Bar */}
      <div className="fixed bottom-0 left-0 right-0 bg-[#0d0d0d] border-t border-gray-800 shadow-lg z-50">
        <div className="max-w-5xl mx-auto flex items-center gap-3 px-4 py-3">
          <textarea
            className="flex-1 resize-none bg-gray-900 text-white placeholder-gray-500 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-600"
            rows="1"
            placeholder="Type your message..."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyPress}
          />
          <button
            onClick={sendMessage}
            disabled={isLoading}
            className="px-5 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg text-white font-medium transition"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
=======
    <div className="flex flex-col h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      <div className="flex-shrink-0 border-b border-gray-700 bg-gray-900/50 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-3 flex-1">
              <label className="text-gray-300 text-sm font-medium whitespace-nowrap">
                User ID:
              </label>
              <input
                type="text"
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
                className="flex-1 max-w-xs px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                placeholder="Enter user ID"
              />
            </div>
            <button
              onClick={clearChat}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded-lg transition-all duration-200 transform hover:scale-105 active:scale-95"
            >
              Clear Chat
            </button>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-4xl mx-auto space-y-4">
          {chatHistory.length === 0 && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center space-y-3 animate-fade-in">
                <div className="text-6xl">💬</div>
                <h2 className="text-2xl font-semibold text-gray-300">
                  Start a conversation
                </h2>
                <p className="text-gray-500">
                  Type a message below to begin chatting
                </p>
              </div>
            </div>
          )}

          {chatHistory.map((msg, index) => (
            <div
              key={index}
              className={`flex ${
                msg.role === 'user' ? 'justify-end' : 'justify-start'
              } animate-slide-in`}
            >
              <div
                className={`max-w-[80%] px-4 py-3 rounded-2xl shadow-lg transform transition-all duration-200 hover:scale-[1.02] ${
                  msg.role === 'user'
                    ? 'bg-gradient-to-br from-blue-600 to-blue-700 text-white rounded-br-sm'
                    : 'bg-gradient-to-br from-green-600 to-green-700 text-white rounded-bl-sm'
                }`}
              >
                <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">
                  {msg.content}
                </p>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start animate-fade-in">
              <div className="max-w-[80%] px-4 py-3 rounded-2xl rounded-bl-sm bg-gradient-to-br from-gray-700 to-gray-800 shadow-lg">
                <div className="flex items-center gap-2">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div
                      className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                      style={{ animationDelay: '0.1s' }}
                    ></div>
                    <div
                      className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                      style={{ animationDelay: '0.2s' }}
                    ></div>
                  </div>
                  <span className="text-gray-300 text-sm">Thinking...</span>
                </div>
              </div>
            </div>
          )}

          {error && (
            <div className="flex justify-center animate-fade-in">
              <div className="px-4 py-3 bg-red-600/20 border border-red-500/50 rounded-lg text-red-300 text-sm">
                {error}
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      <div className="flex-shrink-0 border-t border-gray-700 bg-gray-900/50 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex gap-3 items-end">
            <textarea
              ref={inputRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Type your message..."
              rows="1"
              className="flex-1 px-4 py-3 bg-gray-800 border border-gray-700 rounded-2xl text-white resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all placeholder-gray-500"
              style={{
                maxHeight: '120px',
                minHeight: '48px',
              }}
              onInput={(e) => {
                e.target.style.height = 'auto';
                e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
              }}
            />
            <button
              onClick={sendMessage}
              disabled={isLoading || !message.trim() || !userId.trim()}
              className="px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 disabled:from-gray-700 disabled:to-gray-800 disabled:cursor-not-allowed text-white font-medium rounded-2xl transition-all duration-200 transform hover:scale-105 active:scale-95 disabled:scale-100 shadow-lg"
            >
              Send
            </button>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes slide-in {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes fade-in {
          from {
            opacity: 0;
          }
          to {
            opacity: 1;
          }
        }

        .animate-slide-in {
          animation: slide-in 0.3s ease-out;
        }

        .animate-fade-in {
          animation: fade-in 0.3s ease-out;
        }
      `}</style>
    </div>
  );
}

export default App;
>>>>>>> 81b52b1b6a4f7744a4006e1777e5dc890a50d9cb
