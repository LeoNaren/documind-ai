import { onAuthStateChanged, type User } from "firebase/auth";
import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { ChatPanel } from "./components/ChatPanel";
import { Sidebar } from "./components/Sidebar";
import { SummaryPanel } from "./components/SummaryPanel";
import { WorkspaceHeader } from "./components/WorkspaceHeader";
import { askQuestion, listFiles, uploadFile, type FileRecord } from "./lib/api";
import { auth, firebaseEnabled } from "./lib/firebase";
import { isMedia } from "./lib/media";
import type { ChatTurn } from "./lib/types";

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [files, setFiles] = useState<FileRecord[]>([]);
  const [selectedFileId, setSelectedFileId] = useState<number | null>(null);
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [question, setQuestion] = useState("");
  const [mediaUrl, setMediaUrl] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const mediaRef = useRef<HTMLMediaElement | null>(null);

  const selectedFile = useMemo(
    () => files.find((file) => file.id === selectedFileId) ?? files[0],
    [files, selectedFileId]
  );

  useEffect(() => {
    if (!auth) return;
    return onAuthStateChanged(auth, setUser);
  }, []);

  useEffect(() => {
    void refreshFiles();
  }, [user]);

  useEffect(() => {
    let cancelled = false;

    async function buildMediaUrl() {
      if (!selectedFile || !isMedia(selectedFile)) {
        setMediaUrl(null);
        return;
      }
      const token = firebaseEnabled && user ? await user.getIdToken() : "dev-token";
      if (!cancelled) {
        setMediaUrl(
          `${import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api"}/files/${selectedFile.id}/content?token=${encodeURIComponent(token)}`
        );
      }
    }

    void buildMediaUrl();
    return () => {
      cancelled = true;
    };
  }, [selectedFile, user]);

  async function refreshFiles() {
    try {
      setFiles(await listFiles(user));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load files");
    }
  }

  async function handleUpload(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      const created = await uploadFile(file, user);
      setFiles((current) => [created, ...current]);
      setSelectedFileId(created.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setBusy(false);
      event.target.value = "";
    }
  }

  async function handleAsk(event: FormEvent) {
    event.preventDefault();
    const trimmed = question.trim();
    if (!trimmed) return;
    setQuestion("");
    setTurns((current) => [...current, { role: "user", text: trimmed }]);
    setBusy(true);
    setError(null);
    try {
      const response = await askQuestion(trimmed, selectedFileId, user);
      setTurns((current) => [
        ...current,
        { role: "assistant", text: response.answer, sources: response.sources }
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Chat failed");
    } finally {
      setBusy(false);
    }
  }

  function playFrom(seconds: number) {
    if (!mediaRef.current) return;
    mediaRef.current.currentTime = seconds;
    void mediaRef.current.play();
  }

  function setMediaElement(element: HTMLVideoElement | HTMLAudioElement | null) {
    mediaRef.current = element;
  }

  return (
    <main className="app-shell">
      <Sidebar
        user={user}
        files={files}
        selectedFile={selectedFile}
        busy={busy}
        onUpload={handleUpload}
        onSelectFile={setSelectedFileId}
      />

      <section className="workspace">
        <WorkspaceHeader selectedFile={selectedFile} />
        {error && <p className="error">{error}</p>}

        <div className="content-grid">
          <SummaryPanel
            selectedFile={selectedFile}
            mediaUrl={mediaUrl}
            onMediaElement={setMediaElement}
          />
          <ChatPanel
            turns={turns}
            question={question}
            busy={busy}
            files={files}
            onQuestionChange={setQuestion}
            onAsk={handleAsk}
            onPlayFrom={playFrom}
          />
        </div>
      </section>
    </main>
  );
}