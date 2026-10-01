const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "/api";
import { apiFetch, apiJson } from "./api-client";

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

export type CodingWorkspace = { id: string; name: string };
export type CodingProject = { id: string; workspace_id: string; name: string; description?: string };
export type CodingProjectFile = { path: string; size_bytes: number; mime_type: string };
export type CodingProposal = {
  mode: "patch";
  path: string;
  summary: string;
  diff: string;
  proposed_content: string;
  original_sha256: string;
};
export type ProjectGitStatus = {
  is_git_repository: boolean;
  state: "not_connected" | "clean" | "dirty";
  branch: string | null;
  repository_url: string | null;
  provider: string | null;
  default_branch: string | null;
  modified_files: string[];
  untracked_files: string[];
  staged_files: string[];
  deleted_files: string[];
};
export type TerminalCapabilities = { available: boolean; reason: string | null; allowed_commands: string[]; test_runner: string | null };
export type TerminalRunResult = { command: string; stdout: string; stderr: string; exit_code: number; duration_ms: number; timed_out: boolean; test_runner?: string };

export async function getCodingWorkspaces(): Promise<{ items: CodingWorkspace[] }> {
  return apiJson("/v1/coding/workspaces");
}

export async function getCodingProjects(workspaceId: string): Promise<{ items: CodingProject[] }> {
  return apiJson(`/v1/workspaces/${encodeURIComponent(workspaceId)}/projects`);
}

export async function getCodingProjectFiles(projectId: string, query = ""): Promise<{ items: CodingProjectFile[] }> {
  return apiJson(`/v1/coding/projects/${encodeURIComponent(projectId)}/files?q=${encodeURIComponent(query)}`);
}

export async function searchCodingProjectContent(projectId: string, query: string): Promise<{ items: { path: string; line: number; snippet: string }[] }> {
  return apiJson(`/v1/coding/projects/${encodeURIComponent(projectId)}/search?q=${encodeURIComponent(query)}`);
}

export async function readCodingProjectFile(projectId: string, path: string): Promise<{ path: string; content: string; sha256: string; size_bytes: number }> {
  return apiJson(`/v1/coding/projects/${encodeURIComponent(projectId)}/file?path=${encodeURIComponent(path)}`);
}

export async function uploadCodingProjectFile(projectId: string, file: File, path: string): Promise<void> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("path", path);
  const response = await apiFetch(`/v1/coding/projects/${encodeURIComponent(projectId)}/files`, { method: "POST", body: formData });
  if (!response.ok) throw new Error((await response.json().catch(() => ({}))).detail || `Upload failed (${response.status})`);
}

export async function runProjectCodingAction(payload: {
  project_id: string;
  mode: "explain" | "suggest" | "patch";
  prompt: string;
  path?: string;
  selected_code?: string;
  history?: { role: string; content: string }[];
  model?: string;
}): Promise<{ mode: "explain" | "suggest"; answer: string } | CodingProposal> {
  return apiJson(`/v1/coding/projects/${encodeURIComponent(payload.project_id)}/assist`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload),
  });
}

export async function applyProjectCodingPatch(projectId: string, proposal: CodingProposal): Promise<void> {
  await apiJson(`/v1/coding/projects/${encodeURIComponent(projectId)}/apply`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path: proposal.path, content: proposal.proposed_content, original_sha256: proposal.original_sha256 }),
  });
}

export async function connectProjectGit(projectId: string, repositoryUrl: string, defaultBranch: string): Promise<ProjectGitStatus> {
  return apiJson(`/v1/coding/projects/${encodeURIComponent(projectId)}/git/connect`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repository_url: repositoryUrl, default_branch: defaultBranch }),
  });
}

export async function getProjectGitStatus(projectId: string): Promise<ProjectGitStatus> {
  return apiJson(`/v1/coding/projects/${encodeURIComponent(projectId)}/git/status`);
}

export async function getProjectGitDiff(projectId: string): Promise<{ is_git_repository: boolean; diff: string; truncated: boolean }> {
  return apiJson(`/v1/coding/projects/${encodeURIComponent(projectId)}/git/diff`);
}

export async function suggestProjectCommitMessage(projectId: string, model: string): Promise<{ message: string }> {
  return apiJson(`/v1/coding/projects/${encodeURIComponent(projectId)}/git/commit-message`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ model }),
  });
}

export async function createProjectGitCommit(projectId: string, message: string, confirmed: boolean): Promise<{ commit: string; message: string }> {
  return apiJson(`/v1/coding/projects/${encodeURIComponent(projectId)}/git/commit`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ message, confirmed }),
  });
}

export async function getProjectTerminalCapabilities(projectId: string): Promise<TerminalCapabilities> {
  return apiJson(`/v1/coding/projects/${encodeURIComponent(projectId)}/terminal/capabilities`);
}

export async function runProjectTerminalCommand(projectId: string, argv: string[], signal?: AbortSignal): Promise<TerminalRunResult> {
  return apiJson(`/v1/coding/projects/${encodeURIComponent(projectId)}/terminal/run`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ argv }), signal,
  });
}

export async function runProjectTests(projectId: string, signal?: AbortSignal): Promise<TerminalRunResult> {
  return apiJson(`/v1/coding/projects/${encodeURIComponent(projectId)}/terminal/tests`, {
    method: "POST", headers: { "Content-Type": "application/json" }, signal,
  });
}

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
