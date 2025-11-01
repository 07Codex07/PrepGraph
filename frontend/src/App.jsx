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
      const data = await response.json();

      setChatHistory((prev) => [
        ...prev,
        { role: "assistant", content: data.assistant },
      ]);
    } catch (err) {
      setError("Server error. Try again.");
      console.error("Error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = async () => {
    try {
      await fetch(`${API_BASE}/memory/clear`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId }),
      });
      setChatHistory([]);
    } catch (err) {
      console.error("Error clearing chat:", err);
    }
  };

  return (
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
