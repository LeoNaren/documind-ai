import type { User } from "firebase/auth";
import { firebaseEnabled } from "./firebase";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";

export interface FileRecord {
  id: number;
  filename: string;
  content_type: string;
  status: string;
  summary?: string | null;
}

export interface Source {
  file_id: number;
  filename: string;
  text: string;
  page_number?: number | null;
  start_seconds?: number | null;
  end_seconds?: number | null;
}

export interface ChatResponse {
  answer: string;
  sources: Source[];
}

async function authHeaders(user: User | null): Promise<HeadersInit> {
  if (firebaseEnabled && user) {
    return { Authorization: `Bearer ${await user.getIdToken()}` };
  }
  return { Authorization: "Bearer dev-token" };
}

export async function uploadFile(file: File, user: User | null): Promise<FileRecord> {
  const form = new FormData();
  form.append("upload", file);
  const response = await fetch(`${API_BASE}/files`, {
    method: "POST",
    headers: await authHeaders(user),
    body: form
  });
  return parseResponse(response);
}

export async function listFiles(user: User | null): Promise<FileRecord[]> {
  const response = await fetch(`${API_BASE}/files`, { headers: await authHeaders(user) });
  return parseResponse(response);
}

export async function askQuestion(
  question: string,
  fileId: number | null,
  user: User | null
): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: {
      ...(await authHeaders(user)),
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ question, file_id: fileId })
  });
  return parseResponse(response);
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail ?? `Request failed with ${response.status}`);
  }
  return response.json();
}

