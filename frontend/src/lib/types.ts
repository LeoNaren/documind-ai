import type { ChatResponse } from "./api";

export interface ChatTurn {
  role: "user" | "assistant";
  text: string;
  sources?: ChatResponse["sources"];
}

