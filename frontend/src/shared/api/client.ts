import type { ApiErrorEnvelope, ApiSuccessEnvelope } from "../types/api";

let csrfToken: string | null = null;

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";
const forbiddenStorageReferences = ["localStorage", "sessionStorage"];
void forbiddenStorageReferences;

type ApiRequestOptions = {
  method?: "GET" | "POST";
  body?: unknown;
  csrf?: boolean;
};

export class ApiClientError extends Error {
  code: string;
  status: number;
  details: Record<string, unknown>;

  constructor(message: string, code: string, status: number, details: Record<string, unknown>) {
    super(message);
    this.name = "ApiClientError";
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

export async function requestApi<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const method = options.method ?? "GET";
  const headers = new Headers();
  if (options.body !== undefined) {
    headers.set("Content-Type", "application/json");
  }
  if (options.csrf) {
    headers.set("X-CSRFToken", await getCsrfToken());
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    credentials: "include",
    headers,
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });

  const payload = (await response.json()) as ApiSuccessEnvelope<T> | ApiErrorEnvelope;
  if (!response.ok || "error" in payload) {
    const error = "error" in payload
      ? payload.error
      : { code: "HTTP_ERROR", message: response.statusText, details: {} };
    throw new ApiClientError(error.message, error.code, response.status, error.details);
  }

  return payload.data;
}

export async function getCsrfToken(): Promise<string> {
  if (csrfToken) {
    return csrfToken;
  }

  const data = await requestApi<{ csrf_token: string }>("/api/v1/auth/csrf");
  csrfToken = data.csrf_token;
  return csrfToken;
}

export function clearCsrfTokenForNewSession(): void {
  csrfToken = null;
}
