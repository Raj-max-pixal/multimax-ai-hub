/** Consume the body once, including when a proxy returns text instead of JSON. */
export async function readJsonResponse<T>(response: Response): Promise<T> {
  const text = await response.text();
  let data: unknown = null;
  let validJson = false;
  try {
    data = JSON.parse(text);
    validJson = true;
  } catch {
    // Plain-text/HTML gateway errors are not API JSON responses.
  }

  if (!response.ok) {
    if (data && typeof data === "object") {
      const error = data as Record<string, unknown>;
      const detail = error.detail ?? error.message ?? error.error;
      if (detail) throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
    if (/^\s*</.test(text) || (response.status === 404 && /\bNOT_FOUND\b/.test(text))) {
      throw new Error(`The API service is unavailable (HTTP ${response.status}). Please try again after the server connection is restored.`);
    }
    throw new Error(text.trim() || `Request failed with status ${response.status}`);
  }
  if (!text.trim() && response.status === 204) return null as T;
  if (!validJson) throw new Error("The server returned an invalid response. Please try again.");
  return data as T;
}
