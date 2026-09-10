/** Base URL for API calls. Empty = same origin (dev proxy / prod /ui hosting). */
export const API_BASE: string =
  (import.meta.env.VITE_API_BASE as string | undefined) ?? "";

export function apiUrl(path: string): string {
  if (!path.startsWith("/")) return `${API_BASE}/${path}`;
  return `${API_BASE}${path}`;
}

export function wsUrl(path: string): string {
  const base = API_BASE.replace(/^http/, "ws");
  const hostPath = base
    ? `${base}${path}`
    : `${window.location.protocol === "https:" ? "wss" : "ws"}://${
        window.location.host
      }${path}`;
  return hostPath;
}
