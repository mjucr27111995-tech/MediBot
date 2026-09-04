/** API client for MediBot backend */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface LoginResponse {
  access_token: string;
  token_type: string;
  role: string;
  full_name: string;
  username: string;
  collections: string[];
}

export interface SourceInfo {
  source_document: string;
  section_title: string;
  collection: string;
}

export interface ChatResponse {
  answer: string;
  sources: SourceInfo[];
  retrieval_type: "hybrid_rag" | "sql_rag";
  role: string;
}

export interface CollectionsResponse {
  role: string;
  collections: string[];
}

export interface HealthResponse {
  status: string;
  qdrant_connected: boolean;
  database_accessible: boolean;
}

export async function login(
  username: string,
  password: string
): Promise<LoginResponse> {
  const res = await fetch(`${API_BASE}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Login failed" }));
    throw new Error(error.detail || "Login failed");
  }
  return res.json();
}

export async function chat(
  question: string,
  token: string
): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ question }),
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Chat request failed" }));
    throw new Error(error.detail || "Chat request failed");
  }
  return res.json();
}

export async function getCollections(
  role: string
): Promise<CollectionsResponse> {
  const res = await fetch(`${API_BASE}/collections/${role}`);
  if (!res.ok) {
    throw new Error("Failed to fetch collections");
  }
  return res.json();
}

export async function getHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) {
    throw new Error("Health check failed");
  }
  return res.json();
}
