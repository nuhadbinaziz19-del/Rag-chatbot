import { useRef, useState } from "react";
import { api } from "../api";

export default function Sidebar({
  user, docs, convs, selected, setSelected, convId, open, onClose, onPick, onNewChat, onChanged, onLogout,
}) {
  const fileRef = useRef(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  async function upload(e) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    setUploading(true);
    setError("");
    try {
      await api.upload(file);
      onChanged();
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  }

  async function remove(kind, id, label) {
    if (!window.confirm(`Delete "${label}"? This cannot be undone.`)) return;
    try {
      kind === "doc" ? await api.deleteDocument(id) : await api.deleteConversation(id);
      if (kind === "conv" && id === convId) onNewChat();
      onChanged();
    } catch (err) {
      setError(err.message);
    }
  }

  const toggle = (id) => setSelected((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]));

  return (
    <>
      {open && <div className="scrim" onClick={onClose} />}
      <aside className={`sidebar ${open ? "open" : ""}`} aria-label="Documents and conversations">
        <div className="side-head">
          <span className="wordmark small">নথি</span>
          <button className="ghost" onClick={onNewChat}>New chat</button>
        </div>

        <section>
          <h2>Documents</h2>
          <input ref={fileRef} type="file" accept="application/pdf" hidden onChange={upload} />
          <button className="upload" disabled={uploading} onClick={() => fileRef.current.click()}>
            {uploading ? "Reading pages. Scanned pages take longer." : "Upload a PDF"}
          </button>
          {error && <p className="error" role="alert">{error}</p>}
          {docs.length === 0 ? (
            <p className="empty">No documents yet. Upload a PDF to start asking questions.</p>
          ) : (
            <ul>
              {docs.map((d) => (
                <li key={d.id}>
                  <label className="doc">
                    <input type="checkbox" checked={selected.includes(d.id)} onChange={() => toggle(d.id)} />
                    <span className="doc-name" title={d.filename}>{d.filename}</span>
                    <span className="doc-meta">{d.n_pages} pages</span>
                  </label>
                  <button className="icon" aria-label={`Delete ${d.filename}`} onClick={() => remove("doc", d.id, d.filename)}>×</button>
                </li>
              ))}
            </ul>
          )}
          {docs.length > 0 && (
            <p className="hint">{selected.length ? `Searching ${selected.length} selected` : "Searching all documents. Tick boxes to narrow."}</p>
          )}
        </section>

        <section className="grow">
          <h2>Conversations</h2>
          {convs.length === 0 ? (
            <p className="empty">Your past questions will appear here.</p>
          ) : (
            <ul>
              {convs.map((c) => (
                <li key={c.id} className={c.id === convId ? "active" : ""}>
                  <button className="conv" onClick={() => onPick(c.id)}>{c.title}</button>
                  <button className="icon" aria-label={`Delete conversation ${c.title}`} onClick={() => remove("conv", c.id, c.title)}>×</button>
                </li>
              ))}
            </ul>
          )}
        </section>

        <div className="side-foot">
          <span title={user.email}>{user.email}</span>
          <button className="ghost" onClick={onLogout}>Sign out</button>
        </div>
      </aside>
    </>
  );
}
