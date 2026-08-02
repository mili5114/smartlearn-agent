import { useState } from "react";
import PdfUploader from "./PdfUploader.jsx";
import ChatPanel from "./ChatPanel.jsx";

function App() {
  const [upload, setUpload] = useState(null);
  const [answer, setAnswer] = useState(null);

  return (
    <main>
      <h1>SmartLearn Lite</h1>

      <PdfUploader onUploaded={(result) => setUpload(result)} />

      {upload && (
        <p className="upload-info">
          Uploaded: {upload.filename} ({upload.pages} pages, {upload.characters}{" "}
          characters)
        </p>
      )}

      <ChatPanel
        onAnswer={(result) => setAnswer(result)}
        hasUpload={!!upload}
      />

      {answer && (
        <section className="answer-card">
          <h2>Answer</h2>
          <p>{answer.answer}</p>
          <div className="page-chips">
            {answer.citations.map((page) => (
              <span key={page} className="page-chip">
                Page {page}
              </span>
            ))}
          </div>
        </section>
      )}
    </main>
  );
}

export default App;
