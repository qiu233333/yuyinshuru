from __future__ import annotations

from openai import OpenAI


DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_DEEPSEEK_TIMEOUT_SECONDS = 5.0


class TextPolisherError(RuntimeError):
    """Raised when DeepSeek text polishing fails."""


class TextPolisher:
    def __init__(
        self,
        api_key: str | None,
        model: str,
        timeout_seconds: float = DEFAULT_DEEPSEEK_TIMEOUT_SECONDS,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self._client = (
            OpenAI(
                api_key=api_key,
                base_url=DEEPSEEK_BASE_URL,
                max_retries=0,
                timeout=timeout_seconds,
            )
            if api_key
            else None
        )

    def polish(self, text: str) -> str:
        clean_text = text.strip()
        if not clean_text:
            return ""
        if self._client is None:
            raise TextPolisherError("DEEPSEEK_API_KEY is missing.")

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "你只负责整理中文语音识别文本。只修正中文标点、断句和明显错别字。"
                            "不要扩写，不要改变原意，不要解释，不要添加前后缀。"
                        ),
                    },
                    {"role": "user", "content": clean_text},
                ],
                temperature=0,
                timeout=self.timeout_seconds,
            )
            polished_text = response.choices[0].message.content
        except Exception as exc:
            raise TextPolisherError(str(exc)) from exc

        if polished_text is None:
            raise TextPolisherError("DeepSeek returned empty content.")

        return polished_text.strip()
