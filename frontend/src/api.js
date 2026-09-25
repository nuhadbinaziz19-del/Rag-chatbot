const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

let token = localStorage.getItem("nothi_token");
let onUnauthorized = () => {};
export const getToken = () => token;
export const setToken = (t) => {
  token = t;
  t ? localStorage.setItem("nothi_token", t) : localStorage.removeItem("nothi_token");
};
export const setUnauthorizedHandler = (fn) => (onUnauthorized = fn);

async function fail(res) {
  let message = "Something went wrong. Please try again.";
  try {
    const { detail } = await res.json();
    if (typeof detail === "string") message = detail;
    else if (Array.isArray(detail)) message = detail.map((d) => d.msg).join(". ");
  } catch {}
  if (res.status === 401 && token) {
    setToken(null);
    onUnauthorized();
  }
  throw new ApiError(message, res.status);
}

const headers = (json) => ({
  ...(json ? { "Content-Type": "application/json" } : {}),
  ...(token ? { Authorization: `Bearer ${token}` } : {}),
});

async function request(path, { method = "GET", body, form } = {}) {
  const res = await fetch(BASE + path, {
    method,
    headers: headers(!!body),
    body: body ? JSON.stringify(body) : form,
  });
  if (!res.ok) await fail(res);
  return res.status === 204 ? null : res.json();
}

export const api = {
  register: (email, password) => request("/auth/register", { method: "POST", body: { email, password } }),
  login: (email, password) => request("/auth/login", { method: "POST", body: { email, password } }),
  me: () => request("/auth/me"),
  documents: () => request("/documents"),
  upload: (file) => {
    const form = new FormData();
    form.append("file", file);
    return request("/documents", { method: "POST", form });
  },
  deleteDocument: (id) => request(`/documents/${id}`, { method: "DELETE" }),
  conversations: () => request("/conversations"),
  messages: (id) => request(`/conversations/${id}/messages`),
  deleteConversation: (id) => request(`/conversations/${id}`, { method: "DELETE" }),
};

/** POST /chat and call onEvent({event, data}) for each server-sent event. */
export async function streamChat(payload, { onEvent, signal }) {
  const res = await fetch(BASE + "/chat", {
    method: "POST",
    headers: headers(true),
    body: JSON.stringify(payload),
    signal,
  });
  if (!res.ok) await fail(res);

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const frames = buffer.split("\n\n");
    buffer = frames.pop();
    for (const frame of frames) {
      const event = /^event: (.+)$/m.exec(frame)?.[1];
      const data = /^data: (.+)$/m.exec(frame)?.[1];
      if (event && data) onEvent({ event, data: JSON.parse(data) });
    }
  }
}
