from pathlib import Path

import httpx

from app.core.config import Settings


class TranscriptionProvider:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def transcribe(self, path: Path, content_type: str) -> list[dict]:
        if not self.settings.deepgram_api_key:
            return [
                {
                    "text": "Deepgram API key is not configured. This is a development transcript.",
                    "start": 0.0,
                    "end": 5.0,
                }
            ]

        params = {"model": "nova-2", "smart_format": "true", "utterances": "true"}
        headers = {
            "Authorization": f"Token {self.settings.deepgram_api_key}",
            "Content-Type": content_type,
        }
        async with httpx.AsyncClient(timeout=180) as client:
            response = await client.post(
                "https://api.deepgram.com/v1/listen",
                params=params,
                headers=headers,
                content=path.read_bytes(),
            )
            response.raise_for_status()
        payload = response.json()
        utterances = payload.get("results", {}).get("utterances") or []
        if utterances:
            return [
                {"text": item["transcript"], "start": item["start"], "end": item["end"]}
                for item in utterances
            ]

        transcript = (
            payload.get("results", {})
            .get("channels", [{}])[0]
            .get("alternatives", [{}])[0]
            .get("transcript", "")
        )
        return [{"text": transcript, "start": 0.0, "end": 0.0}] if transcript else []

