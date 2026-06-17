"""OpenAI-compatible request/response schemas.

These mirror the public shapes used by the OpenAI Python/Node SDKs so existing
clients work without modification. We deliberately keep them permissive
(``extra="allow"`` on the request) so unknown sampling parameters are forwarded
verbatim to llama.cpp rather than rejected.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# --------------------------------------------------------------------------- #
# Models endpoint
# --------------------------------------------------------------------------- #


class ModelCard(BaseModel):
    """A single entry in the GET /v1/models response."""

    id: str
    object: Literal["model"] = "model"
    created: int = 0
    owned_by: str = "airllm"


class ModelList(BaseModel):
    """Response body for GET /v1/models."""

    object: Literal["list"] = "list"
    data: list[ModelCard] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Chat completions — request
# --------------------------------------------------------------------------- #


class ChatMessage(BaseModel):
    """A single chat message.

    ``content`` may be a plain string or the OpenAI "content parts" array
    (used for multimodal input); we accept both and forward as-is.
    """

    model_config = ConfigDict(extra="allow")

    role: str
    content: str | list[dict[str, Any]] | None = None
    name: str | None = None


class ChatCompletionRequest(BaseModel):
    """Request body for POST /v1/chat/completions.

    Extra fields are allowed and forwarded to the upstream llama.cpp server so
    that sampling knobs (top_p, repeat_penalty, etc.) keep working.
    """

    model_config = ConfigDict(extra="allow")

    model: str
    messages: list[ChatMessage]
    stream: bool = False
    temperature: float | None = None
    top_p: float | None = None
    max_tokens: int | None = None
    stop: str | list[str] | None = None

    def upstream_payload(self) -> dict[str, Any]:
        """Serialise the request for forwarding to llama.cpp.

        Drops ``None`` values so we don't override upstream defaults, and keeps
        any extra fields the client supplied.
        """
        return self.model_dump(exclude_none=True)


# --------------------------------------------------------------------------- #
# Chat completions — response (non-streaming)
# --------------------------------------------------------------------------- #


class Usage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatCompletionChoice(BaseModel):
    index: int = 0
    message: ChatMessage
    finish_reason: str | None = None


class ChatCompletionResponse(BaseModel):
    """Non-streaming completion response. Mirrors OpenAI's shape."""

    model_config = ConfigDict(extra="allow")

    id: str
    object: Literal["chat.completion"] = "chat.completion"
    created: int
    model: str
    choices: list[ChatCompletionChoice]
    usage: Usage | None = None
