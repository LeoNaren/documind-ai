import type { FileRecord } from "./api";

export function formatTime(value: number) {
  const minutes = Math.floor(value / 60);
  const seconds = Math.floor(value % 60)
    .toString()
    .padStart(2, "0");
  return `${minutes}:${seconds}`;
}

export function isMedia(file: FileRecord) {
  return file.content_type.startsWith("audio/") || file.content_type.startsWith("video/");
}

