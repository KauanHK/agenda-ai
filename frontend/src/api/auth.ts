import { api, request, setAuth } from "./client";
import type { LoginRequest, TokenResponse, UserCreate, UserRead } from "./types";

export async function login(body: LoginRequest): Promise<TokenResponse> {
  const tokens = await request<TokenResponse>("/auth/login", {
    method: "POST",
    body: { username: body.username, password: body.password },
    auth: false,
  });
  setAuth(tokens);
  return tokens;
}

export function logout() {
  setAuth(null);
}

export function createUser(body: UserCreate) {
  return api.post<UserRead>("/auth/", body);
}
