import { useCallback, useRef, useState } from "react";
import DeviationForm from "./components/DeviationForm";
import CopilotChat from "./components/CopilotChat";
import { EMPTY_FORM, EMPTY_RISK } from "./constants";
import { sendChatMessage, uploadDocument, saveDeviation } from "./api";
import "./app-layout.css";

const INITIAL_MESSAGE = {
  id: "welcome",
  role: "assistant",
  content:
    "Ready to log a deviation. Paste the raw report or upload a PDF, and I will extract the details, assess impact/severity, and recommend the next action.",
};

let idCounter = 1;
function nextId() {
  idCounter += 1;
  return `m-${idCounter}`;
}

export default function App() {
  const [form, setForm] = useState(EMPTY_FORM);
  const [risk, setRisk] = useState(EMPTY_RISK);
  const [status, setStatus] = useState("pending_triage");
  const [messages, setMessages] = useState([INITIAL_MESSAGE]);
  const [changedFields, setChangedFields] = useState([]);
  const [loading, setLoading] = useState(false);
  const [committing, setCommitting] = useState(false);
  const [lastSavedRecord, setLastSavedRecord] = useState(null);
  const highlightTimer = useRef(null);

  const applyResult = useCallback((result) => {
    setForm(result.form);
    setRisk(result.risk_assessment);
    setStatus(result.status);
    setChangedFields(result.changed_fields || []);
    setLastSavedRecord(null);

    if (highlightTimer.current) clearTimeout(highlightTimer.current);
    highlightTimer.current = setTimeout(() => setChangedFields([]), 5000);

    setMessages((prev) => [...prev, { id: nextId(), role: "assistant", content: result.reply }]);
  }, []);

  const pushErrorMessage = useCallback((err) => {
    setMessages((prev) => [
      ...prev,
      {
        id: nextId(),
        role: "assistant",
        content: `Something went wrong talking to the backend: ${err.message}. Make sure the FastAPI server is running and GROQ_API_KEY is set.`,
      },
    ]);
  }, []);

  const handleSendMessage = useCallback(
    async (text) => {
      setMessages((prev) => [...prev, { id: nextId(), role: "user", content: text }]);
      setLoading(true);
      try {
        const history = messages.slice(-8).map((m) => ({ role: m.role, content: m.content || "" }));
        const result = await sendChatMessage(text, form, risk, history);
        applyResult(result);
      } catch (err) {
        pushErrorMessage(err);
      } finally {
        setLoading(false);
      }
    },
    [form, risk, messages, applyResult, pushErrorMessage]
  );

  const handleUploadFile = useCallback(
    async (file) => {
      setMessages((prev) => [
        ...prev,
        { id: nextId(), role: "user", content: "", attachment: { name: file.name } },
      ]);
      setLoading(true);
      try {
        const result = await uploadDocument(file, form, risk);
        applyResult(result);
      } catch (err) {
        pushErrorMessage(err);
      } finally {
        setLoading(false);
      }
    },
    [form, risk, applyResult, pushErrorMessage]
  );

  const handleCommit = useCallback(async () => {
    setCommitting(true);
    try {
      const res = await saveDeviation(form, risk);
      setMessages((prev) => [
        ...prev,
        {
          id: nextId(),
          role: "assistant",
          content: `Saved to the deviation ledger as ${res.record_id}. Ready for the next deviation whenever you are.`,
        },
      ]);
      setLastSavedRecord(res.record_id);
      setForm(EMPTY_FORM);
      setRisk(EMPTY_RISK);
      setStatus("pending_triage");
      setChangedFields([]);
    } catch (err) {
      pushErrorMessage(err);
    } finally {
      setCommitting(false);
    }
  }, [form, risk, pushErrorMessage]);

  const handleReset = useCallback(() => {
    setForm(EMPTY_FORM);
    setRisk(EMPTY_RISK);
    setStatus("pending_triage");
    setChangedFields([]);
    setLastSavedRecord(null);
    setMessages((prev) => [
      ...prev,
      {
        id: nextId(),
        role: "assistant",
        content: "Deviation reset. Send the next report when you are ready.",
      },
    ]);
  }, []);

  return (
    <div className="app-shell">
      <DeviationForm
        form={form}
        risk={risk}
        status={status}
        changedFields={changedFields}
        onCommit={handleCommit}
        onReset={handleReset}
        committing={committing}
        lastSavedRecord={lastSavedRecord}
      />
      <CopilotChat
        messages={messages}
        onSendMessage={handleSendMessage}
        onUploadFile={handleUploadFile}
        loading={loading}
      />
    </div>
  );
}
