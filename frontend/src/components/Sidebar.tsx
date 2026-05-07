import type { User } from "firebase/auth";
import { BrainCircuit, FileAudio, FileText, UploadCloud } from "lucide-react";
import type { ChangeEvent } from "react";
import type { FileRecord } from "../lib/api";
import { isMedia } from "../lib/media";
import { AuthPanel } from "./AuthPanel";

interface SidebarProps {
  user: User | null;
  files: FileRecord[];
  selectedFile?: FileRecord;
  busy: boolean;
  onUpload: (event: ChangeEvent<HTMLInputElement>) => void;
  onSelectFile: (fileId: number) => void;
}

export function Sidebar({
  user,
  files,
  selectedFile,
  busy,
  onUpload,
  onSelectFile
}: SidebarProps) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <BrainCircuit aria-hidden />
        <div>
          <strong>DocuMind AI</strong>
          <span>Multimedia RAG workspace</span>
        </div>
      </div>

      <AuthPanel user={user} />

      <label className="upload-zone">
        <UploadCloud aria-hidden />
        <span>{busy ? "Processing..." : "Upload PDF, audio, or video"}</span>
        <input
          type="file"
          accept="application/pdf,audio/*,video/*"
          onChange={onUpload}
          disabled={busy}
        />
      </label>

      <section className="file-list" aria-label="Uploaded files">
        {files.map((file) => (
          <button
            className={file.id === selectedFile?.id ? "file-row active" : "file-row"}
            key={file.id}
            onClick={() => onSelectFile(file.id)}
          >
            {isMedia(file) ? <FileAudio aria-hidden /> : <FileText aria-hidden />}
            <span>{file.filename}</span>
            <small>{file.status}</small>
          </button>
        ))}
      </section>
    </aside>
  );
}

