import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .config import settings
from .deps import chat_rate_limit, current_user_id
from .services import chat_store
from .services.llm import condense_question, stream_answer
from .services.prompt import NO_CONTEXT_REPLY, SYSTEM, build_messages, sources_payload
from .services.retrieve import retrieve

log = logging.getLogger(__name__)
router = APIRouter()


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    conversation_id: int | None = None
    document_ids: list[int] | None = None  # restrict to specific documents


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/chat")
def chat(req: ChatRequest, user_id: int = Depends(chat_rate_limit)):
    """Streams Server-Sent Events: meta -> sources -> token* -> done (or error)."""
    if not settings.anthropic_api_key:
        raise HTTPException(503, "ANTHROPIC_API_KEY is not configured.")
    if req.conversation_id and not chat_store.conversation_exists(req.conversation_id, user_id):
        raise HTTPException(404, "Conversation not found.")

    conv_id = req.conversation_id or chat_store.create_conversation(user_id, req.question)

    def events():
        try:
            history = chat_store.get_history(conv_id, settings.history_turns * 2)
            query = condense_question(req.question, history)
            chunks = retrieve(query, settings.context_chunks, user_id, req.document_ids)
            sources = sources_payload(chunks)

            yield _sse("meta", {"conversation_id": conv_id, "search_query": query})
            yield _sse("sources", {"sources": sources})

            if not chunks:
                yield _sse("token", {"text": NO_CONTEXT_REPLY})
                chat_store.add_exchange(conv_id, req.question, NO_CONTEXT_REPLY, [])
                yield _sse("done", {})
                return

            parts: list[str] = []
            for token in stream_answer(SYSTEM, build_messages(req.question, chunks, history)):
                parts.append(token)
                yield _sse("token", {"text": token})

            chat_store.add_exchange(conv_id, req.question, "".join(parts), sources)
            yield _sse("done", {})
        except Exception:
            log.exception("chat stream failed")
            yield _sse("error", {"message": "Something went wrong while generating the answer."})

    return StreamingResponse(events(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})


@router.get("/conversations")
def conversations(user_id: int = Depends(current_user_id)):
    return chat_store.list_conversations(user_id)


@router.get("/conversations/{conv_id}/messages")
def messages(conv_id: int, user_id: int = Depends(current_user_id)):
    if not chat_store.conversation_exists(conv_id, user_id):
        raise HTTPException(404, "Conversation not found.")
    return chat_store.get_messages(conv_id)


@router.delete("/conversations/{conv_id}", status_code=204)
def delete_conversation(conv_id: int, user_id: int = Depends(current_user_id)):
    if not chat_store.delete_conversation(conv_id, user_id):
        raise HTTPException(404, "Conversation not found.")
