import { Bot, MessageSquare, Play, Send } from "lucide-react";
import type { FormEvent } from "react";
import type { ChatTurn } from "../lib/types";
import type { FileRecord } from "../lib/api";
import { formatTime } from "../lib/media";

interface ChatPanelProps {
  turns: ChatTurn[];
  question: string;
  busy: boolean;
  files: FileRecord[];
  onQuestionChange: (question: string) => void;
  onAsk: (event: FormEvent) => void;
  onPlayFrom: (seconds: number) => void;
}

export function ChatPanel({
  turns,
  question,
  busy,
  files,
  onQuestionChange,
  onAsk,
  onPlayFrom
}: ChatPanelProps) {
  return (
    <section className="chat-panel">
      <div className="chat-title">
        <MessageSquare aria-hidden />
        <h2>Ask DocuMind</h2>
      </div>
      <div className="messages">
        {turns.length === 0 && (
          <div className="empty-state">
            <Bot aria-hidden />
            <p>Ask about decisions, topics, definitions, or where something appears.</p>
          </div>
        )}
        {turns.map((turn, index) => (
          <article className={`message ${turn.role}`} key={`${turn.role}-${index}`}>
            <p>{turn.text}</p>
            {turn.sources?.map((source, sourceIndex) => (
              <div className="source" key={`${source.file_id}-${sourceIndex}`}>
                <strong>{source.filename}</strong>
                <span>
                  {source.page_number ? `Page ${source.page_number}` : null}
                  {source.start_seconds != null ? ` ${formatTime(source.start_seconds)}` : null}
                </span>
                <p>{source.text}</p>
                {source.start_seconds != null && (
                  <button onClick={() => onPlayFrom(source.start_seconds ?? 0)}>
                    <Play aria-hidden />
                    Play
                  </button>
                )}
              </div>
            ))}
          </article>
        ))}
      </div>
      <form className="composer" onSubmit={onAsk}>
        <input
          value={question}
          onChange={(event) => onQuestionChange(event.target.value)}
          placeholder="Ask a question about uploaded content"
          disabled={busy || files.length === 0}
        />
        <button disabled={busy || !question.trim()}>
          <Send aria-hidden />
        </button>
      </form>
    </section>
  );
}

