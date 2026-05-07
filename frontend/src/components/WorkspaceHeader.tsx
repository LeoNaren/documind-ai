import { Search } from "lucide-react";
import type { FileRecord } from "../lib/api";

interface WorkspaceHeaderProps {
  selectedFile?: FileRecord;
}

export function WorkspaceHeader({ selectedFile }: WorkspaceHeaderProps) {
  return (
    <header className="topbar">
      <div>
        <span className="eyebrow">Active file</span>
        <h1>{selectedFile?.filename ?? "Upload a source to begin"}</h1>
      </div>
      <div className="status-pill">
        <Search aria-hidden />
        {selectedFile?.status ?? "waiting"}
      </div>
    </header>
  );
}

