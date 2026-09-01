import React, { useEffect, useRef, useState } from "react";
import "./ChatWidget.css";
import { createApiClient } from "../../api/client";
import { useAuth } from "../../auth/AuthContext";
import { usePatient } from "../../patient/PatientContext";

const ORCHESTRATOR_URL = "http://localhost:8094";
const MAX_IMAGE_SIZE_BYTES = 8 * 1024 * 1024;

// Maps a /chat response's tools_called entries to which ServicesPage data
// kind changed, so it knows what to silently refresh.
const TOOL_TO_KIND = {
  add_medicine: "medicines",
  add_doctor_note: "notes",
  add_lab_report: "labReports",
};

const ChatWidget = () => {
  const { isAuthenticated } = useAuth();
  const { activeInsuranceNumber, setActiveInsuranceNumber, notifyDataChanged } =
    usePatient();
  const api = createApiClient(ORCHESTRATOR_URL);

  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [file, setFile] = useState(null);
  const [lastRequest, setLastRequest] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, loading, isOpen]);

  if (!isAuthenticated) return null;

  const clearAttachment = () => {
    setFile(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const sendMessage = async ({ text, image }) => {
    if (!text.trim() && !image) return;

    setLoading(true);
    setError("");

    const formData = new FormData();
    formData.append("message", text);
    if (image) formData.append("attachment", image);
    if (activeInsuranceNumber) {
      formData.append("insurance_number", activeInsuranceNumber);
    }

    setLastRequest({ text, image });
    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        text,
        imageName: image?.name,
      },
    ]);
    setInput("");
    clearAttachment();

    try {
      const response = await api.post("/chat", formData);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: response.reply,
          image: response.xray_image_base64,
        },
      ]);
      setLastRequest(null);

      const changedKinds = (response.tools_called || [])
        .map((tool) => TOOL_TO_KIND[tool])
        .filter(Boolean);
      if (changedKinds.length > 0) notifyDataChanged(changedKinds);
    } catch (err) {
      setError(err.message || "Failed to get a response");
    } finally {
      setLoading(false);
    }
  };

  const handleSend = () => {
    sendMessage({ text: input, image: file });
  };

  const handleRetry = () => {
    if (!lastRequest || loading) return;
    sendMessage(lastRequest);
  };

  const handleNewPatient = async () => {
    setError("");
    try {
      await api.post("/new-patient");
      setMessages([]);
      setInput("");
      clearAttachment();
      setLastRequest(null);
      // A fresh consultation shouldn't keep targeting the previous patient -
      // the next write should ask again rather than silently reuse this one.
      setActiveInsuranceNumber(null);
    } catch (err) {
      setError(err.message || "Failed to start a new patient consultation");
    }
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;

    const isValidType = ["image/jpeg", "image/png", "application/pdf"].includes(
      selectedFile.type
    );
    if (!isValidType) {
      setError("Attach a JPG, PNG, or PDF file.");
      clearAttachment();
      return;
    }

    if (selectedFile.size > MAX_IMAGE_SIZE_BYTES) {
      setError("File must be smaller than 8 MB.");
      clearAttachment();
      return;
    }

    setError("");
    setFile(selectedFile);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-widget-root">
      {isOpen && (
        <div className="chat-widget-panel" role="dialog" aria-label="MediTrack chat assistant">
          <div className="chat-widget-header">
            <div className="chat-header-profile">
              <div className="chat-avatar" aria-hidden="true">
                M
              </div>
              <div>
                <h3>MediTrack Assistant</h3>
                <span className="chat-active-patient">
                  {activeInsuranceNumber
                    ? `Patient: ${activeInsuranceNumber}`
                    : "No patient selected"}
                </span>
              </div>
            </div>
            <div className="chat-widget-header-actions">
              <button
                className="chat-icon-btn chat-new-btn"
                onClick={handleNewPatient}
                title="Start new patient"
                aria-label="Start new patient"
              >
                New Patient
              </button>
              <button
                className="chat-icon-btn chat-widget-close"
                onClick={() => setIsOpen(false)}
                aria-label="Collapse chat"
                title="Collapse chat"
              >
                X
              </button>
            </div>
          </div>

          <div className="chat-messages">
            {messages.length === 0 && (
              <div className="chat-empty">
                <p>
                  Ask about symptoms, medications, or attach an X-ray image or
                  lab report. You can also add a medicine, note, or lab report
                  to the current patient's record.
                </p>
              </div>
            )}

            {messages.map((message, index) => (
              <div
                key={`${message.role}-${index}`}
                className={`chat-message chat-message-${message.role}`}
              >
                <div className={`chat-bubble chat-bubble-${message.role}`}>
                  {message.imageName && (
                    <div className="chat-bubble-attachment">
                      Attached file: {message.imageName}
                    </div>
                  )}
                  {message.text && (
                    <div className="chat-bubble-text">{message.text}</div>
                  )}
                  {message.image && (
                    <img
                      className="chat-bubble-image"
                      src={`data:image/jpeg;base64,${message.image}`}
                      alt="X-ray annotated result"
                    />
                  )}
                </div>
              </div>
            ))}

            {loading && (
              <div className="chat-message chat-message-assistant">
                <div className="chat-bubble chat-bubble-assistant chat-typing">
                  <span />
                  <span />
                  <span />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {error && (
            <div className="chat-error">
              <span>{error}</span>
              {lastRequest && (
                <button type="button" onClick={handleRetry}>
                  Retry
                </button>
              )}
            </div>
          )}

          {file && (
            <div className="chat-file-preview">
              <div>
                <strong>{file.name}</strong>
                <span>{Math.ceil(file.size / 1024)} KB</span>
              </div>
              <button type="button" onClick={clearAttachment}>
                Remove
              </button>
            </div>
          )}

          <div className="chat-input-row">
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png,application/pdf"
              onChange={handleFileChange}
              className="chat-file-input"
            />
            <button
              type="button"
              className="chat-attach-btn"
              onClick={() => fileInputRef.current?.click()}
              aria-label="Attach X-ray image or lab report"
              title="Attach X-ray image or lab report"
            >
              +
            </button>
            <textarea
              className="chat-text-input"
              placeholder="Message MediTrack..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={1}
            />
            <button
              className="chat-send-btn"
              onClick={handleSend}
              disabled={loading || (!input.trim() && !file)}
              aria-label="Send message"
              title="Send message"
            >
              Send
            </button>
          </div>
        </div>
      )}

      <button
        className="chat-widget-fab"
        onClick={() => setIsOpen((prev) => !prev)}
        aria-label={isOpen ? "Collapse chat" : "Open AI Assistant"}
      >
        {isOpen ? "X" : "Chat"}
      </button>
    </div>
  );
};

export default ChatWidget;
