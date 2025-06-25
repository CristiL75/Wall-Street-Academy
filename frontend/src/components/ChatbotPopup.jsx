import React, { useState, useEffect, useRef } from "react";
import "./ChatbotPopup.css";
import axios from "axios";
import chatIcon from "../assets/chat-icon.png";
import { getTokenPayload } from "../utils/auth"; // Adaugă acest import

export default function ChatbotPopup() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const [userId, setUserId] = useState(null);
  
  // Obține ID-ul utilizatorului la prima încărcare
  useEffect(() => {
    // Folosește metoda corectă pentru a obține ID-ul utilizatorului din token JWT
    const payload = getTokenPayload();
    
    if (payload && payload.sub) {
      console.log("User ID from token:", payload.sub);
      setUserId(payload.sub);
    } else {
      // Fallback la metodele anterioare
      const storedUserId = localStorage.getItem("userId") || localStorage.getItem("user_id") || localStorage.getItem("_id");
      console.log("User ID from localStorage:", storedUserId);
      
      if (storedUserId) {
        setUserId(storedUserId);
      } else {
        setUserId("guest");
      }
    }
    
    // Afișează mesaj de bun venit la prima deschidere
    if (open && messages.length === 0) {
      setMessages([{ 
        role: "assistant", 
        content: "Hello! How can I help you with questions about stocks or finance?"
      }]);
    }
  }, [open, messages.length]);

  // Auto-scroll la mesaje noi
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim()) return;
    
    // Actualizează starea local pentru UI responsiv
    const userMessage = { role: "user", content: input };
    const currentInput = input; // Salvează inputul înainte de a-l reseta
    setMessages(prevMessages => [...prevMessages, userMessage]);
    setLoading(true);
    setInput("");
    
    try {
      console.log("Sending to API with user ID:", userId);
      
      // Trimite cerere către backend
      const res = await axios.post("http://localhost:8000/api/chatbot/chat", {
        message: currentInput,
        user_id: userId || "guest"
      });
      
      // Adaugă răspunsul backend-ului
      const botResponse = { role: "assistant", content: res.data.response };
      setMessages(prevMessages => [...prevMessages, botResponse]);
    } catch (e) {
      console.error("Chatbot error:", e);
      console.error("Error details:", e.response?.data || "No response data");
      
      // Mesaj de eroare mai descriptiv
      let errorMessage = { 
        role: "assistant", 
        content: "I'm sorry, I couldn't process your request right now. Please try again later."
      };
      
      if (e.response?.data?.detail) {
        errorMessage.content = `Error: ${e.response.data.detail}`;
      }
      
      setMessages(prevMessages => [...prevMessages, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <button className="chatbot-popup-btn" onClick={() => setOpen(!open)}>
        <img 
          src={chatIcon} 
          alt="Chat with us" 
          className="chatbot-icon"
        />
      </button>
      {open && (
        <div className="chatbot-popup-box">
          <div className="chatbot-popup-header">
            <span>Wall Street Academy Chatbot</span>
            <button onClick={() => setOpen(false)}>✖</button>
          </div>
          <div className="chatbot-popup-messages">
            {messages.length === 0 ? (
              <div className="welcome-message">
                How can I help you with stocks or finance today?
              </div>
            ) : (
              messages.map((msg, idx) => (
                <div key={idx} className={msg.role}>
                  {msg.content}
                </div>
              ))
            )}
            {loading && (
              <div className="assistant loading">
                <div className="typing-dots">
                  <span className="dot"></span>
                  <span className="dot"></span>
                  <span className="dot"></span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
          <div className="chatbot-popup-input">
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && !e.shiftKey && sendMessage()}
              disabled={loading}
              placeholder="Type your question..."
            />
            <button onClick={sendMessage} disabled={loading || !input.trim()}>
              Send
            </button>
          </div>
        </div>
      )}
    </>
  );
}