const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "/api";

function toUrl(path: string): string {
  return `${API_BASE}${path.startsWith("/") ? path : `/${path}`}`;
}

async function readJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail = `Request failed: ${response.status}`;
    try {
      const data = await response.json();
      detail = data?.detail ?? data?.message ?? data?.error ?? detail;
    } catch {
      const text = await response.text();
      if (text) detail = text;
    }
    throw new Error(detail);
  }
  return (await response.json()) as T;
}

export type ChatRole = "system" | "user" | "assistant";
export type ChatMessageInput = { role: ChatRole; content: string; images?: string[] };
export type CodingTask =
  | "generate"
  | "fix"
  | "explain"
  | "refactor"
  | "tests"
  | "readme"
  | "api"
  | "project"
  | "review";

export type ResearchMode = "web" | "deep" | "academic" | "news" | "fact-check" | "report";

export function filterEmptyChatMessages(messages: ChatMessageInput[]): ChatMessageInput[] {
  return messages.filter((msg) => msg.content.trim().length > 0);
}

export async function getOllamaModels(): Promise<{ models: { name: string }[] }> {
  const response = await fetch(toUrl("/models"));
  return readJson<{ models: { name: string }[] }>(response);
}

export async function chatWithOllama(
  model: string,
  messages: ChatMessageInput[],
  signal?: AbortSignal,
): Promise<Response> {
  return fetch(toUrl("/chat"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model, messages, stream: true }),
    signal,
  });
}

export async function uploadDocument(file: File): Promise<{ documents: { id: string }[] }> {
  const formData = new FormData();
  formData.append("files", file);
  const response = await fetch(toUrl("/documents/upload"), {
    method: "POST",
    body: formData,
  });
  return readJson<{ documents: { id: string }[] }>(response);
}

export async function runCodingAssist(payload: {
  task: CodingTask;
  prompt: string;
  code?: string;
  language?: string;
  model?: string;
}): Promise<{ answer: string }> {
  const response = await fetch(toUrl("/coding/assist"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return readJson<{ answer: string }>(response);
}

export async function runResearchSearch(payload: {
  query: string;
  mode: ResearchMode;
  model?: string;
  max_sources?: number;
}): Promise<{ summary: string; sources: { title: string; url: string; snippet: string }[] }> {
  const response = await fetch(toUrl("/research/search"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return readJson<{ summary: string; sources: { title: string; url: string; snippet: string }[] }>(
    response,
  );
}

export async function runAgent(payload: {
  goal: string;
  agent_type: string;
  model?: string;
  max_steps?: number;
}): Promise<{ steps: string }> {
  const response = await fetch(toUrl("/agents/run"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return readJson<{ steps: string }>(response);
}

export async function getAgentRuns(): Promise<{ runs: { id: string; goal: string; steps: string; agent_type: string; status: string }[] }> {
  const response = await fetch(toUrl("/agents/runs"));
  return readJson<{ runs: { id: string; goal: string; steps: string; agent_type: string; status: string }[] }>(response);
}

export async function createMemory(payload: {
  content: string;
  category: string;
  tags: string[];
}): Promise<{ id: string }> {
  const response = await fetch(toUrl("/memory"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return readJson<{ id: string }>(response);
}

export async function getMemories(
  query?: string,
  category?: string,
): Promise<{ memories: { id: string; content: string; category: string; tags: string[] }[] }> {
  const params = new URLSearchParams();
  if (query) params.set("q", query);
  if (category) params.set("category", category);
  const suffix = params.size ? `?${params.toString()}` : "";
  const response = await fetch(toUrl(`/memory${suffix}`));
  return readJson<{ memories: { id: string; content: string; category: string; tags: string[] }[] }>(
    response,
  );
}

export async function deleteMemory(memoryId: string): Promise<{ message: string }> {
  const response = await fetch(toUrl(`/memory/${memoryId}`), { method: "DELETE" });
  return readJson<{ message: string }>(response);
}

export async function createWorkflow(payload: {
  name: string;
  trigger: string;
  actions: string[];
  enabled: boolean;
}): Promise<{ id: string }> {
  const response = await fetch(toUrl("/automation/workflows"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return readJson<{ id: string }>(response);
}

export async function getWorkflows(): Promise<{ workflows: { id: string; name: string; trigger: string; actions: string[] }[] }> {
  const response = await fetch(toUrl("/automation/workflows"));
  return readJson<{ workflows: { id: string; name: string; trigger: string; actions: string[] }[] }>(response);
}

export async function generateWorkflow(payload: {
  query: string;
  mode: ResearchMode;
  model?: string;
  max_sources?: number;
}): Promise<{ summary: string }> {
  const response = await fetch(toUrl("/automation/generate"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return readJson<{ summary: string }>(response);
}

export async function transcribeAudio(audioBlob: Blob): Promise<{ transcript: string }> {
  const formData = new FormData();
  formData.append("file", audioBlob, "recording.webm");
  const response = await fetch(toUrl("/transcribe"), {
    method: "POST",
    body: formData,
  });
  return readJson<{ transcript: string }>(response);
}

export async function voiceChat(payload: { transcript: string; model?: string }): Promise<{ answer: string }> {
  const response = await fetch(toUrl("/voice/chat"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return readJson<{ answer: string }>(response);
}

export async function generateImage(payload: {
  prompt: string;
  style: string;
  size: string;
}): Promise<{ prompt: string; style: string; size: string; image_url: string; note: string }> {
  const response = await fetch(toUrl("/images/generate"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return readJson<{ prompt: string; style: string; size: string; image_url: string; note: string }>(
    response,
  );
}

export async function generateVideo(payload: {
  prompt: string;
  style: string;
  duration_seconds: number;
  model?: string;
}): Promise<{ plan: string; frames: string[] }> {
  const response = await fetch(toUrl("/video/generate"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return readJson<{ plan: string; frames: string[] }>(response);
}

export async function getPluginCatalog(): Promise<{
  catalog: { name: string; category: string; description: string }[];
  installed: { id: string; name: string; category: string; description: string; enabled: boolean }[];
}> {
  const response = await fetch(toUrl("/plugins/catalog"));
  return readJson<{
    catalog: { name: string; category: string; description: string }[];
    installed: { id: string; name: string; category: string; description: string; enabled: boolean }[];
  }>(response);
}

export async function installPlugin(payload: {
  name: string;
  category: string;
  description?: string;
  enabled?: boolean;
}): Promise<{ id: string }> {
  const response = await fetch(toUrl("/plugins/install"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return readJson<{ id: string }>(response);
}

export async function getTeamWorkspaces(): Promise<{ workspaces: { id: string; name: string; members: string[]; permissions: string[] }[] }> {
  const response = await fetch(toUrl("/team/workspaces"));
  return readJson<{ workspaces: { id: string; name: string; members: string[]; permissions: string[] }[] }>(response);
}

export async function createTeamWorkspace(payload: {
  name: string;
  members: string[];
  permissions: string[];
}): Promise<{ id: string }> {
  const response = await fetch(toUrl("/team/workspaces"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return readJson<{ id: string }>(response);
}

export async function getMarketplaceItems(): Promise<{ items: { id: string; title: string; item_type: string; description: string }[] }> {
  const response = await fetch(toUrl("/marketplace/items"));
  return readJson<{ items: { id: string; title: string; item_type: string; description: string }[] }>(response);
}

export async function publishMarketplaceItem(payload: {
  title: string;
  item_type: string;
  description?: string;
  content?: string;
}): Promise<{ id: string }> {
  const response = await fetch(toUrl("/marketplace/items"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return readJson<{ id: string }>(response);
}

export async function getMobileBuilds(): Promise<{ builds: { id: string; app_name: string; platform: string; features: string[]; outputs: string[]; status: string }[] }> {
  const response = await fetch(toUrl("/mobile/builds"));
  return readJson<{ builds: { id: string; app_name: string; platform: string; features: string[]; outputs: string[]; status: string }[] }>(response);
}

export async function createMobileBuild(payload: {
  platform: string;
  app_name: string;
  features: string[];
}): Promise<{ id: string }> {
  const response = await fetch(toUrl("/mobile/builds"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return readJson<{ id: string }>(response);
}

export async function getEnterpriseConfig(): Promise<{ configs: { id: string; feature: string; enabled: boolean; notes: string }[] }> {
  const response = await fetch(toUrl("/enterprise/config"));
  return readJson<{ configs: { id: string; feature: string; enabled: boolean; notes: string }[] }>(response);
}

export async function saveEnterpriseConfig(payload: {
  feature: string;
  enabled: boolean;
  notes?: string;
}): Promise<{ id: string }> {
  const response = await fetch(toUrl("/enterprise/config"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return readJson<{ id: string }>(response);
}
