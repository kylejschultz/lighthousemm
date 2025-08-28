export const API_BASE =
  import.meta.env.VITE_API_BASE ||
  (location.hostname.startsWith("lhmm.")
    ? location.origin.replace("//lhmm.", "//api.lhmm.")
    : "http://localhost:8080");

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${API_BASE}/api/v1/${path}`, {
    headers: { "content-type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!r.ok) {
    const text = await r.text();
    throw new Error(`HTTP ${r.status}: ${text}`);
  }
  return r.json();
}

export const api = {
  health: () => req<string>("healthz"),
  config: () => req<any>("system/config"),
  system: {
    updateConfig: (payload: any) => req<any>("system/config", { method: "PUT", body: JSON.stringify(payload) }),
  },
  disks: { list: () => req<any>("disks") },
  libraries: {
    list: () => req<any>("libraries"),
    get: (id: number) => req<any>(`libraries/${id}`),
    create: (payload: any) => req<any>("libraries", { method: "POST", body: JSON.stringify(payload) }),
    update: (id: number, payload: any) => req<any>(`libraries/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  },
  tmdb: {
    search: (q: string, media_type: "multi"|"movie"|"tv" = "multi") =>
      req<any>(`tmdb/search?q=${encodeURIComponent(q)}&media_type=${media_type}`),
  },
};
