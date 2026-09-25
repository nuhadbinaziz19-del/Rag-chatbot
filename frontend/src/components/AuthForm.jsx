import { useState } from "react";
import { api } from "../api";

export default function AuthForm({ onAuthed }) {
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const signup = mode === "register";

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      onAuthed(await (signup ? api.register : api.login)(email.trim(), password));
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  return (
    <main className="auth">
      <section className="auth-intro">
        <h1 className="wordmark">নথি</h1>
        <p>Upload Bangla and English PDFs, then ask questions. Every answer points to the page it came from.</p>
        <p lang="bn" className="bn-sample">আপনার নথি থেকে প্রশ্ন করুন, উত্তরের সাথে পৃষ্ঠার উৎস পান।</p>
      </section>
      <form className="auth-card" onSubmit={submit}>
        <h2>{signup ? "Create your account" : "Sign in"}</h2>
        <label>
          Email
          <input type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
        </label>
        <label>
          Password
          <input
            type="password"
            autoComplete={signup ? "new-password" : "current-password"}
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          {signup && <span className="hint">At least 8 characters.</span>}
        </label>
        {error && <p className="error" role="alert">{error}</p>}
        <button className="primary" disabled={busy}>{busy ? "Please wait" : signup ? "Create account" : "Sign in"}</button>
        <button type="button" className="link" onClick={() => { setMode(signup ? "login" : "register"); setError(""); }}>
          {signup ? "Already have an account? Sign in" : "New here? Create an account"}
        </button>
      </form>
    </main>
  );
}
