import type { FileRecord } from "../lib/api";

interface SummaryPanelProps {
  selectedFile?: FileRecord;
  mediaUrl: string | null;
  onMediaElement: (element: HTMLVideoElement | HTMLAudioElement | null) => void;
}

export function SummaryPanel({ selectedFile, mediaUrl, onMediaElement }: SummaryPanelProps) {
  return (
    <section className="summary-panel">
      <h2>Summary</h2>
      <p>{selectedFile?.summary ?? "Summaries appear here after processing completes."}</p>
      {selectedFile?.content_type.startsWith("video/") && mediaUrl && (
        <video ref={onMediaElement} controls src={mediaUrl} />
      )}
      {selectedFile?.content_type.startsWith("audio/") && mediaUrl && (
        <audio ref={onMediaElement} controls src={mediaUrl} />
      )}
    </section>
  );
}

