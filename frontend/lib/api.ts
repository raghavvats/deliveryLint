/** API helpers for calling the FastAPI backend directly. */

const configuredApiBase = process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "");
export const API_BASE_URL = configuredApiBase || "http://127.0.0.1:8000";

export function apiUrl(path: string): string {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE_URL}${normalized}`;
}

export async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) {
    const text = await res.text();
    let detail = text;
    try {
      const json = JSON.parse(text) as { detail?: unknown };
      if (typeof json.detail === "string") {
        detail = json.detail;
      } else if (Array.isArray(json.detail)) {
        detail = json.detail
          .map((item) =>
            typeof item === "object" && item && "msg" in item
              ? String((item as { msg: string }).msg)
              : String(item),
          )
          .join("; ");
      }
    } catch {
      // keep raw response text
    }
    throw new Error(detail || `API error ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export function isRecentRun(createdAt: string, withinMs = 5 * 60 * 1000): boolean {
  return Date.now() - new Date(createdAt).getTime() <= withinMs;
}
