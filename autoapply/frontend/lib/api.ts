/**
 * All API calls go through this module.
 * Components never call fetch directly.
 */

import { Application, HuntProfile, Job, Resume } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function apiFetch<T>(
  path: string,
  token: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${API_BASE}/api/v1${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...options.headers,
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ error: res.statusText, code: "UNKNOWN" }));
    throw new Error(body.error ?? res.statusText);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// ─── Resumes ─────────────────────────────────────────────────────────────────

export async function uploadResume(token: string, file: File): Promise<Resume> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/api/v1/resumes/upload`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: form,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(body.error ?? res.statusText);
  }
  return res.json();
}

export async function listResumes(token: string): Promise<Resume[]> {
  return apiFetch<Resume[]>("/resumes/", token);
}

export async function getResume(token: string, id: string): Promise<Resume> {
  return apiFetch<Resume>(`/resumes/${id}`, token);
}

export async function deleteResume(token: string, id: string): Promise<void> {
  return apiFetch<void>(`/resumes/${id}`, token, { method: "DELETE" });
}

// ─── Hunt Profiles ───────────────────────────────────────────────────────────

export async function listHuntProfiles(token: string): Promise<HuntProfile[]> {
  return apiFetch<HuntProfile[]>("/hunt-profiles/", token);
}

export async function createHuntProfile(
  token: string,
  data: Partial<HuntProfile>
): Promise<HuntProfile> {
  return apiFetch<HuntProfile>("/hunt-profiles/", token, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateHuntProfile(
  token: string,
  id: string,
  data: Partial<HuntProfile>
): Promise<HuntProfile> {
  return apiFetch<HuntProfile>(`/hunt-profiles/${id}`, token, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

// ─── Jobs ────────────────────────────────────────────────────────────────────

export async function listJobs(
  token: string,
  params?: { min_score?: number; status_filter?: string; limit?: number; offset?: number }
): Promise<Job[]> {
  const qs = new URLSearchParams();
  if (params?.min_score != null) qs.set("min_score", String(params.min_score));
  if (params?.status_filter) qs.set("status_filter", params.status_filter);
  if (params?.limit != null) qs.set("limit", String(params.limit));
  if (params?.offset != null) qs.set("offset", String(params.offset));
  const query = qs.toString() ? `?${qs}` : "";
  return apiFetch<Job[]>(`/jobs/${query}`, token);
}

export async function ignoreJob(token: string, id: string): Promise<void> {
  return apiFetch<void>(`/jobs/${id}/ignore`, token, { method: "POST" });
}

// ─── Applications ────────────────────────────────────────────────────────────

export async function listApplications(token: string): Promise<Application[]> {
  return apiFetch<Application[]>("/applications/", token);
}

export async function tailorApplication(
  token: string,
  job_id: string,
  resume_id: string
): Promise<Application> {
  return apiFetch<Application>("/applications/tailor", token, {
    method: "POST",
    body: JSON.stringify({ job_id, resume_id }),
  });
}

export async function updateApplicationStatus(
  token: string,
  id: string,
  status: string,
  notes?: string
): Promise<Application> {
  return apiFetch<Application>(`/applications/${id}/status`, token, {
    method: "PATCH",
    body: JSON.stringify({ status, notes }),
  });
}
