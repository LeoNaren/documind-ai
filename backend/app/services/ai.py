import hashlib
import logging
import math
import re

from google import genai

from app.core.config import Settings

logger = logging.getLogger(__name__)


class AIProvider:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._client = genai.Client(api_key=settings.gemini_api_key) if settings.gemini_api_key else None

    async def embed(self, text: str) -> list[float]:
        if self._client:
            try:
                result = await self._client.aio.models.embed_content(
                    model=self.settings.gemini_embedding_model,
                    contents=text,
                )
                values = result.embeddings[0].values
                return _fit_dimensions(values, 768)
            except Exception:
                logger.exception("Gemini embedding failed; falling back to deterministic embedding")
        return deterministic_embedding(text)
    
    async def embed_many(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if self._client:
            try:
                result = await self._client.aio.models.embed_content(
                    model=self.settings.gemini_embedding_model,
                    contents=texts,
                )
                return [_fit_dimensions(e.values, 768) for e in result.embeddings]
            except Exception:
                logger.exception("Gemini batch embedding failed; falling back to deterministic embedding")
        
        return [deterministic_embedding(t) for t in texts]

    async def summarize(self, text: str) -> str:
        prompt = (
            "Summarize this uploaded content for a study/work Q&A app. "
            "Use 5 concise bullets and mention important topics.\n\n"
            f"{text[:18000]}"
        )
        return await self.generate(prompt)

    async def answer(self, question: str, contexts: list[str]) -> str:
        joined = "\n\n".join(f"Source {idx + 1}: {text}" for idx, text in enumerate(contexts))
        prompt = (
            "Answer the user using only the provided sources. "
            "If the sources are insufficient, say what is missing. Keep the answer concise.\n\n"
            f"{joined}\n\nQuestion: {question}"
        )
        return await self.generate(prompt)

    async def generate(self, prompt: str) -> str:
        if self._client:
            try:
                response = await self._client.aio.models.generate_content(
                    model=self.settings.gemini_chat_model,
                    contents=prompt,
                )
                return response.text or "I could not generate a response."
            except Exception:
                logger.exception("Gemini generation failed; falling back to development response")
        return mock_generate(prompt)


def deterministic_embedding(text: str, dimensions: int = 768) -> list[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    values = []
    for index in range(dimensions):
        byte = digest[index % len(digest)]
        values.append((byte / 127.5) - 1.0)
    magnitude = math.sqrt(sum(value * value for value in values)) or 1.0
    return [value / magnitude for value in values]


def _fit_dimensions(values: list[float], dimensions: int) -> list[float]:
    if len(values) == dimensions:
        return values
    if len(values) > dimensions:
        return values[:dimensions]
    return values + [0.0] * (dimensions - len(values))


def mock_generate(prompt: str) -> str:
    if "Summarize" in prompt:
        return extractive_summary(prompt)
    return extractive_answer(prompt)


def extractive_summary(prompt: str) -> str:
    content = prompt.split("\n\n", 1)[-1]
    sentences = split_sentences(content)
    if not sentences:
        return "I found the file, but there was not enough readable text to summarize yet."

    bullets = sentences[:5]
    return "\n".join(f"- {sentence}" for sentence in bullets)


def extractive_answer(prompt: str) -> str:
    question_match = re.search(r"Question:\s*(.+)$", prompt, flags=re.DOTALL)
    question = question_match.group(1).strip() if question_match else "your question"
    source_text = prompt.split("Question:", 1)[0]
    sentences = split_sentences(source_text)

    if not sentences:
        return (
            "I found the upload, but I do not have enough extracted source text to answer that yet."
        )

    keywords = {
        word.lower()
        for word in re.findall(r"[A-Za-z][A-Za-z0-9+-]{2,}", question)
        if word.lower() not in {"what", "where", "when", "which", "about", "does", "this", "that"}
    }
    ranked = sorted(
        sentences,
        key=lambda sentence: sum(1 for word in keywords if word in sentence.lower()),
        reverse=True,
    )
    chosen = [sentence for sentence in ranked[:3] if sentence]

    return (
        "Gemini quota is unavailable right now, so I am answering from the retrieved text directly. "
        + " ".join(chosen)
    )


def split_sentences(text: str) -> list[str]:
    clean = re.sub(r"\s+", " ", text).strip()
    clean = re.sub(r"Source \d+:\s*", "", clean)
    if not clean:
        return []
    parts = re.split(r"(?<=[.!?])\s+", clean)
    sentences = [part.strip(" -•") for part in parts if len(part.strip()) > 20]
    return [sentence[:300] for sentence in sentences]
