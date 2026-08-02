import { useState } from "react";
import { askQuestion } from "./api.js";

export default function ChatPanel({ onAnswer, hasUpload }) {
  const [message, setMessage] = useState("");
  const [localStatus, setLocalStatus] = useState("idle");
  const [localError, setLocalError] = useState("");

  const isBusy = localStatus !== "idle";

  async function handleSubmit(event) {
    event.preventDefault();
    const trimmed = message.trim();
    if (!trimmed) return;
    setLocalError("");
    setLocalStatus("asking");
    try {
      const result = await askQuestion(trimmed);
      onAnswer(result);
    } catch (e) {
      setLocalError(e.message);
    } finally {
      setLocalStatus("idle");
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <h2>Ask a Question</h2>
      <label htmlFor="message">Message:</label>
      <textarea
        id="message"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        rows={3}
      />
      <button type="submit" disabled={!hasUpload || !message.trim() || isBusy}>
        Ask
      </button>
      {localStatus === "asking" && <p className="loading-text">Asking…</p>}
      {localError && (
        <p role="alert" className="error">
          {localError}
        </p>
      )}
    </form>
  );
}
