import { apiJson, clearTokens, setTokens } from "./api-client";

export interface UserProfile {
  id: string;
  email: string;
  username: string;
  display_name: string;
  role: string;
  is_active: boolean;
  is_verified: boolean;
  avatar_url: string;
}

type ApiUserResponse = {
  success: boolean;
  user: UserProfile;
};

type ApiAuthResponse = {
  success: boolean;
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: UserProfile;
};

export async function registerUser(
  email: string,
  username: string,
  password: string,
  display_name?: string,
): Promise<UserProfile> {
  const response = await apiJson<ApiUserResponse>("/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, username, password, display_name }),
  });
  return response.user;
}

export async function loginUser(username: string, password: string): Promise<ApiAuthResponse> {
  const response = await apiJson<ApiAuthResponse>("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  setTokens(response.access_token, response.refresh_token);
  return response;
}

export async function logoutUser(): Promise<void> {
  const refreshToken = localStorage.getItem("multimax_refresh_token");
  if (refreshToken) {
    await apiJson<{ success: boolean }>("/auth/logout", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
  }
  clearTokens();
}

export async function getCurrentUser(): Promise<UserProfile> {
  const response = await apiJson<ApiUserResponse>("/auth/me", { method: "GET" });
  return response.user;
}

export async function updateCurrentUser(payload: {
  display_name?: string;
  avatar_url?: string;
}): Promise<UserProfile> {
  const response = await apiJson<ApiUserResponse>("/auth/me", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return response.user;
}

export async function resetPassword(email: string): Promise<void> {
  await apiJson<{ success: boolean }>("/auth/reset-password", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
}

export async function updatePassword(token: string, password: string): Promise<void> {
  await apiJson<{ success: boolean }>("/auth/reset-password/confirm", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token, password }),
  });
}
