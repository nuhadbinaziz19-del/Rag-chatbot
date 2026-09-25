import { useEffect, useRef, useState } from "react";
import { api, streamChat } from "../api";

const CITE = /(\[\d+\])/g;
const EXAMPLES = ["এই নথির মূল বিষয় কী?", "Summarize the key points", "What are the deadlines mentioned?"];

function Message({ m }) {
  const [openN, setOpenN] = useState(null);
  const sources = m.sources || [];

  if (m.role === "user") return <div className="msg user"><p>{m.content}</p></div>;
  if (!m.content && !m.pending) return null;

  return (
    <div className="msg assistant">
      <p className="answer">
        {m.content.split(CITE).map((part, i) => {
          const n = /^\[(\d+)\]$/.exec(part)?.[1];
          return n && sources.some((s) => s.n === +n) ? (
            <button key={i} className="cite" aria-label={`Show source ${n}`} onClick={() => setOpenN(openN === +n ? null : +n)}>{n}</button>
          ) : (
            part
          );
        })}
        {m.pending && <span className="caret" aria-label="Thinking" />}
      </p>
      {sources.length > 0 && !m.pending && (
        <ul className="sources">
          {sources.map((s) => (
            <li key={s.n} className={openN === s.n ? "open" : ""}>
              <button onClick={() => setOpenN(openN === s.n ? null : s.n)} aria-expanded={openN === s.n}>
                <span className="cite static">{s.n}</span>
                {s.filename}, page {s.page}
              </button>
              {openN === s.n && <blockquote>{s.snippet}{s.snippet.length >= 300 ? "…" : ""}</blockquote>}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function Chat({ convId, hasDocs, selected, onOpenMenu, onConversation, onDone }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const abortRef = useRef(null);
  const skipLoad = useRef(null);
  const endRef = useRef(null);

  // Load history when the user opens an existing conversation.
  useEffect(() => {
    if (convId == null) return;
    if (skipLoad.current === convId) { skipLoad.current = null; return; }
    let live = true;
    api.messages(convId)
      .then((rows) => live && setMessages(rows.map((r) => ({ role: r.role, content: r.content, sources: r.sources || [] }))))
      .catch((e) => live && setError(e.message));
    return () => { live = false; };
  }, [convId]);

  useEffect(() => () => abortRef.current?.abort(), []);
  useEffect(() => endRef.current?.scrollIntoView({ block: "end" }), [messages]);

  async function send(text) {
    const question = text.trim();
    if (!question || busy) return;
    setError("");
    setInput("");
    setBusy(true);
    const ctrl = new AbortController();
    abortRef.current = ctrl;
    setMessages((m) => [...m, { role: "user", content: question }, { role: "assistant", content: "", sources: [], pending: true }]);
    const patchLast = (fn) => setMessages((m) => { const c = m.slice(); c[c.length - 1] = fn(c[c.length - 1]); return c; });

    try {
      await streamChat(
        { question, conversation_id: convId, document_ids: selected.length ? selected : null },
        {
          signal: ctrl.signal,
          onEvent: ({ event, data }) => {
            if (event === "meta" && convId == null) { skipLoad.current = data.conversation_id; onConversation(data.conversation_id); }
            else if (event === "sources") patchLast((a) => ({ ...a, sources: data.sources }));
            else if (event === "token") patchLast((a) => ({ ...a, content: a.content + data.text, pending: false }));
            else if (event === "error") setError(data.message);
          },
        }
      );
    } catch (e) {
      if (e.name !== "AbortError") setError(e.message);
    } finally {
      patchLast((a) => ({ ...a, pending: false }));
      setBusy(false);
      onDone();
    }
  }

  const onKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(input); }
  };

  return (
    <main className="chat">
      <header className="chat-head">
        <button className="ghost menu" onClick={onOpenMenu}>Menu</button>
        <span className="scope">{selected.length ? `Searching ${selected.length} selected document${selected.length > 1 ? "s" : ""}` : "Searching all your documents"}</span>
      </header>

      <div className="thread" aria-live="polite">
        {messages.length === 0 ? (
          <div className="blank">
            <h1>{hasDocs ? "What do you want to know?" : "Start by adding a document"}</h1>
            <p>{hasDocs ? "Ask in Bangla or English. Answers cite the page they came from." : "Upload a PDF from the sidebar. Scanned Bangla pages are read with OCR."}</p>
            {hasDocs && (
              <div className="examples">
                {EXAMPLES.map((q) => <button key={q} onClick={() => setInput(q)}>{q}</button>)}
              </div>
            )}
          </div>
        ) : (
          messages.map((m, i) => <Message key={i} m={m} />)
        )}
        <div ref={endRef} />
      </div>

      {error && <p className="error banner" role="alert">{error}</p>}
      <div className="composer">
        <textarea
          rows={2}
          value={input}
          disabled={!hasDocs}
          placeholder={hasDocs ? "Ask a question about your documents" : "Upload a document first"}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKey}
          aria-label="Your question"
        />
        <button className="primary" disabled={busy || !input.trim() || !hasDocs} onClick={() => send(input)}>
          {busy ? "Answering" : "Ask"}
        </button>
      </div>
    </main>
  );
}
