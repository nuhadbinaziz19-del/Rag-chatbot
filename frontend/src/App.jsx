import { useCallback, useEffect, useState } from "react";
import { api, getToken, setToken, setUnauthorizedHandler } from "./api";
import AuthForm from "./components/AuthForm.jsx";
import Sidebar from "./components/Sidebar.jsx";
import Chat from "./components/Chat.jsx";

export default function App() {
  const [user, setUser] = useState(null);
  const [booting, setBooting] = useState(!!getToken());
  const [docs, setDocs] = useState([]);
  const [convs, setConvs] = useState([]);
  const [selected, setSelected] = useState([]); // document ids to search; empty = all
  const [convId, setConvId] = useState(null);
  const [menuOpen, setMenuOpen] = useState(false);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    setDocs([]);
    setConvs([]);
    setSelected([]);
    setConvId(null);
  }, []);

  useEffect(() => setUnauthorizedHandler(logout), [logout]);

  useEffect(() => {
    if (!getToken()) return;
    api.me().then(setUser).catch(() => {}).finally(() => setBooting(false));
  }, []);

  const refresh = useCallback(async () => {
    const [d, c] = await Promise.all([api.documents(), api.conversations()]);
    setDocs(d);
    setConvs(c);
    setSelected((s) => s.filter((id) => d.some((x) => x.id === id)));
  }, []);

  useEffect(() => {
    if (user) refresh().catch(() => {});
  }, [user, refresh]);

  if (booting) return <div className="boot" aria-busy="true" />;
  if (!user) return <AuthForm onAuthed={(session) => { setToken(session.access_token); setUser(session.user); }} />;

  return (
    <div className="app">
      <Sidebar
        user={user}
        docs={docs}
        convs={convs}
        selected={selected}
        setSelected={setSelected}
        convId={convId}
        open={menuOpen}
        onClose={() => setMenuOpen(false)}
        onPick={(id) => { setConvId(id); setMenuOpen(false); }}
        onNewChat={() => { setConvId(null); setMenuOpen(false); }}
        onChanged={() => refresh().catch(() => {})}
        onLogout={logout}
      />
      <Chat
        key={convId === null ? "new" : "existing"}
        convId={convId}
        hasDocs={docs.length > 0}
        selected={selected}
        onOpenMenu={() => setMenuOpen(true)}
        onConversation={setConvId}
        onDone={() => refresh().catch(() => {})}
      />
    </div>
  );
}
