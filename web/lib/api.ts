// Chunk 3 scope: register/login/refresh against the auth blueprint,
// plus simple session storage. Gets a real HTTP wrapper (interceptors,
// auto-refresh-on-401, etc.) as more endpoints land in later chunks —
// this stays deliberately small for now.

const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

export type Role = "patient" | "doctor" | "admin";

export interface AuthUser {
  id: number;
  email: string;
  role: Role;
}

export interface AuthResponse {
  user: AuthUser;
  access_token: string;
  refresh_token: string;
  role: Role;
}

interface ApiErrorBody {
  error?: {
    code?: string;
    message?: string;
    details?: { field?: string; message: string }[];
  };
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_URL}/api/v1${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });

  const data = (await res.json().catch(() => ({}))) as T & ApiErrorBody;

  if (!res.ok) {
    const message = data?.error?.message || "Something went wrong. Please try again.";
    throw new Error(message);
  }

  return data as T;
}

export function register(input: {
  email: string;
  password: string;
  role: Role;
  full_name: string;
}): Promise<AuthResponse> {
  return request<AuthResponse>("/auth/register", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function login(input: { email: string; password: string }): Promise<AuthResponse> {
  return request<AuthResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

const ACCESS_TOKEN_KEY = "healthcare_appt.access_token";
const REFRESH_TOKEN_KEY = "healthcare_appt.refresh_token";
const ROLE_KEY = "healthcare_appt.role";

export function storeSession(auth: AuthResponse) {
  localStorage.setItem(ACCESS_TOKEN_KEY, auth.access_token);
  localStorage.setItem(REFRESH_TOKEN_KEY, auth.refresh_token);
  localStorage.setItem(ROLE_KEY, auth.role);
}

export function clearSession() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(ROLE_KEY);
}

export function getStoredRole(): Role | null {
  if (typeof window === "undefined") return null;
  const role = localStorage.getItem(ROLE_KEY);
  return role === "patient" || role === "doctor" || role === "admin" ? role : null;
}

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function roleHomePath(role: Role): string {
  return `/${role}`;
}
