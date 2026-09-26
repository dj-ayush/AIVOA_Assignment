import { useEffect, useRef, useState } from "react";

function FlaskIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M9 2v6L3.5 18a2 2 0 001.8 3h13.4a2 2 0 001.8-3L14 8V2" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M8 2h8" strokeLinecap="round" />
      <path d="M6.5 15h11" strokeLinecap="round" />
    </svg>
  );
}

function BoltIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
      <path d="M13 2L4 14h6l-1 8 9-12h-6l1-8z" />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
      <path d="M5 13l4 4L19 7" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function PaperclipIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path
        d="M21 11.5l-9.19 9.19a5 5 0 01-7.07-7.07l8.49-8.49a3.5 3.5 0 014.95 4.95l-8.49 8.49a2 2 0 01-2.83-2.83l7.78-7.78"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function SendIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
      <path d="M22 2L11 13" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M22 2l-7 20-4-9-9-4 20-7z" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function PdfChip({ name }) {
  return (
    <div className="pdf-chip">
      <span className="pdf-chip-icon">PDF</span>
      <div>
        <div className="pdf-chip-title">Document queued</div>
        <div className="pdf-chip-name">{name}</div>
      </div>
    </div>
  );
}

function Message({ message }) {
  const isUser = message.role === "user";
  return (
    <div className={`msg-row ${isUser ? "msg-row-user" : ""}`}>
      {!isUser && <div className="msg-avatar msg-avatar-assistant">{message.icon || <BoltIcon />}</div>}
      <div className={`msg-bubble ${isUser ? "msg-bubble-user" : "msg-bubble-assistant"}`}>
        {message.attachment && <PdfChip name={message.attachment.name} />}
        {message.content && <p>{message.content}</p>}
      </div>
      {isUser && <div className="msg-avatar msg-avatar-user">QA</div>}
    </div>
  );
}

export default function CopilotChat({ messages, onSendMessage, onUploadFile, loading }) {
  const [draft, setDraft] = useState("");
  const scrollRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, loading]);

  function handleSubmit(e) {
    e.preventDefault();
    const text = draft.trim();
    if (!text || loading) return;
    onSendMessage(text);
    setDraft("");
  }

  function handleFileChange(e) {
    const file = e.target.files?.[0];
    if (file) onUploadFile(file);
    e.target.value = "";
  }

  return (
    <div className="chat-panel">
      <div className="chat-header">
        <div className="chat-header-icon">
          <FlaskIcon />
        </div>
        <div>
          <h2>Deviation Copilot</h2>
          <p>Drop deviation files or paste text below.</p>
        </div>
        <span className="chat-status-dot" />
      </div>

      <div className="chat-messages" ref={scrollRef}>
        {messages.map((m) => (
          <Message key={m.id} message={m} />
        ))}
        {loading && (
          <div className="msg-row">
            <div className="msg-avatar msg-avatar-assistant">
              <BoltIcon />
            </div>
            <div className="msg-bubble msg-bubble-assistant msg-bubble-loading" aria-label="DeviationIQ is processing">
              <span className="typing-dot" />
              <span className="typing-dot" />
              <span className="typing-dot" />
            </div>
          </div>
        )}
      </div>

      <form className="chat-input-row" onSubmit={handleSubmit}>
        <button
          type="button"
          className="icon-btn"
          onClick={() => fileInputRef.current?.click()}
          title="Attach a PDF, text file, or email"
          disabled={loading}
        >
          <PaperclipIcon />
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.txt,.eml"
          hidden
          onChange={handleFileChange}
        />
        <input
          className="chat-text-input"
          type="text"
          placeholder={loading ? "DeviationIQ is processing..." : "Type a correction or paste a deviation..."}
          value={draft}
          disabled={loading}
          onChange={(e) => setDraft(e.target.value)}
        />
        <button type="submit" className="send-btn" disabled={!draft.trim() || loading} title="Send">
          <SendIcon />
        </button>
      </form>
      <div className="chat-footer">DEVIATIONIQ | POWERED BY LANGGRAPH + GROQ</div>
    </div>
  );
}

export { CheckIcon };
