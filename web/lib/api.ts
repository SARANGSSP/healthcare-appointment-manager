// Chunk 3 & Chunk 5: API client for Auth and Doctor CRUD management.

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

export interface Doctor {
  id: number;
  user_id: number;
  email: string | null;
  full_name: string;
  specialisation: string;
  working_hours: Record<string, string[]>;
  slot_duration_minutes: number;
}

export interface CreateDoctorInput {
  email: string;
  password: string;
  full_name: string;
  specialisation: string;
  working_hours?: Record<string, string[]>;
  slot_duration_minutes?: number;
}

export interface UpdateDoctorInput {
  email?: string;
  full_name?: string;
  specialisation?: string;
  working_hours?: Record<string, string[]>;
  slot_duration_minutes?: number;
}

export interface DoctorLeave {
  id: number;
  doctor_id: number;
  leave_date: string;
  reason: string | null;
}

export interface MarkLeaveInput {
  leave_date: string;
  reason?: string;
}


interface ApiErrorBody {
  error?: {
    code?: string;
    message?: string;
    details?: { field?: string; message: string }[];
  };
}

const ACCESS_TOKEN_KEY = "healthcare_appt.access_token";
const REFRESH_TOKEN_KEY = "healthcare_appt.refresh_token";
const ROLE_KEY = "healthcare_appt.role";

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getStoredRole(): Role | null {
  if (typeof window === "undefined") return null;
  const role = localStorage.getItem(ROLE_KEY);
  return role === "patient" || role === "doctor" || role === "admin" ? role : null;
}

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

export function roleHomePath(role: Role): string {
  return `/${role}`;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getAccessToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> || {}),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_URL}/api/v1${path}`, {
    ...options,
    headers,
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

export function fetchDoctors(specialisation?: string): Promise<Doctor[]> {
  const query = specialisation ? `?specialisation=${encodeURIComponent(specialisation)}` : "";
  return request<Doctor[]>(`/doctors${query}`);
}

export function fetchDoctor(id: number): Promise<Doctor> {
  return request<Doctor>(`/doctors/${id}`);
}

export function createDoctor(input: CreateDoctorInput): Promise<Doctor> {
  return request<Doctor>("/doctors", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function updateDoctor(id: number, input: UpdateDoctorInput): Promise<Doctor> {
  return request<Doctor>(`/doctors/${id}`, {
    method: "PUT",
    body: JSON.stringify(input),
  });
}

export function deleteDoctor(id: number): Promise<{ message: string }> {
  return request<{ message: string }>(`/doctors/${id}`, {
    method: "DELETE",
  });
}

export function fetchDoctorMe(): Promise<{ role: Role; message: string; doctor: Doctor | null }> {
  return request<{ role: Role; message: string; doctor: Doctor | null }>("/doctors/me");
}

export function fetchDoctorLeave(doctorId: number): Promise<DoctorLeave[]> {
  return request<DoctorLeave[]>(`/doctors/${doctorId}/leave`);
}

export function markDoctorLeave(doctorId: number, input: MarkLeaveInput): Promise<DoctorLeave> {
  return request<DoctorLeave>(`/doctors/${doctorId}/leave`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function deleteDoctorLeave(doctorId: number, leaveId: number): Promise<{ message: string }> {
  return request<{ message: string }>(`/doctors/${doctorId}/leave/${leaveId}`, {
    method: "DELETE",
  });
}

