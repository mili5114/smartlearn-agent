import { useState } from "react";
import { uploadPDF } from "./api.js";

export default function PdfUploader({ onUploaded }) {
  const [file, setFile] = useState(null);
  const [localStatus, setLocalStatus] = useState("idle");
  const [localError, setLocalError] = useState("");

  const isBusy = localStatus !== "idle";

  async function handleSubmit(event) {
    event.preventDefault();
    if (!file) return;
    setLocalError("");
    setLocalStatus("uploading");
    try {
      const result = await uploadPDF(file);
      onUploaded(result);
    } catch (e) {
      setLocalError(e.message);
    } finally {
      setLocalStatus("idle");
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <h2>Upload PDF</h2>
      <label htmlFor="pdf-file">Choose a PDF file:</label>
      <input
        id="pdf-file"
        type="file"
        accept=".pdf"
        onChange={(e) => setFile(e.target.files[0])}
      />
      <button type="submit" disabled={!file || isBusy}>
        Upload
      </button>
      {localStatus === "uploading" && <p className="loading-text">Uploading…</p>}
      {localError && (
        <p role="alert" className="error">
          {localError}
        </p>
      )}
    </form>
  );
}
