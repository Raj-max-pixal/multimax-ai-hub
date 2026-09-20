const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "/api";
const ACCESS_TOKEN_KEY = "multimax_access_token";
const REFRESH_TOKEN_KEY = "multimax_refresh_token";

let onRefreshFailed: (() => void) | null = null;

type RequestInitWithAuth = RequestInit & {
  skipAuthRefresh?: boolean;
};

export function setOnRefreshFailed(handler: () => void): void {
  onRefreshFailed = handler;
}

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setTokens(accessToken: string, refreshToken: string): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

function buildUrl(path: string): string {
  if (path.startsWith("http://") || path.startsWith("https://")) {
    return path;
  }
  return `${API_BASE}${path.startsWith("/") ? path : `/${path}`}`;
}

async function parseError(response: Response): Promise<Error> {
  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    const data = await response.json();
    const detail = data?.detail ?? data?.message ?? data?.error;
    return new Error(detail || `Request failed with status ${response.status}`);
  }
  const text = await response.text();
  return new Error(text || `Request failed with status ${response.status}`);
}

async function refreshAccessToken(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    return false;
  }

  const response = await fetch(buildUrl("/auth/refresh"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  if (!response.ok) {
    return false;
  }

  const data = await response.json();
  if (!data.access_token || !data.refresh_token) {
    return false;
  }

  setTokens(data.access_token, data.refresh_token);
  return true;
}

export async function apiFetch(path: string, init: RequestInitWithAuth = {}): Promise<Response> {
  const headers = new Headers(init.headers ?? {});
  const token = getAccessToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(buildUrl(path), {
    ...init,
    headers,
  });

  if (response.status !== 401 || init.skipAuthRefresh) {
    return response;
  }

  const refreshed = await refreshAccessToken();
  if (!refreshed) {
    clearTokens();
    if (onRefreshFailed) {
      onRefreshFailed();
    }
    return response;
  }

  const retryHeaders = new Headers(init.headers ?? {});
  const newToken = getAccessToken();
  if (newToken) {
    retryHeaders.set("Authorization", `Bearer ${newToken}`);
  }

  return fetch(buildUrl(path), {
    ...init,
    headers: retryHeaders,
    skipAuthRefresh: true,
  } as RequestInitWithAuth);
}

export async function apiJson<T>(path: string, init: RequestInitWithAuth = {}): Promise<T> {
  const response = await apiFetch(path, init);
  if (!response.ok) {
    throw await parseError(response);
  }
  return (await response.json()) as T;
}
