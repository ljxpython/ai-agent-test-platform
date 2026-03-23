import { getValidAccessToken } from "@/lib/oidc-storage";

type RequestOptions = RequestInit & {
  projectId?: string;
};

function trimTrailingSlash(value: string): string {
  return value.replace(/\/+$/, "");
}

export function getManagementBaseUrl(): string {
  return `${trimTrailingSlash(process.env.NEXT_PUBLIC_API_URL || "http://localhost:2024")}/_management`;
}

export async function requestManagementJson<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const token = getValidAccessToken();
  const headers = new Headers(options.headers ?? {});

  if (!headers.has("Content-Type") && options.body) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  if (options.projectId) {
    headers.set("x-project-id", options.projectId);
  }

  const response = await fetch(`${getManagementBaseUrl()}${path}`, {
    ...options,
    headers,
    cache: "no-store",
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const payload = (await response.json()) as { detail?: string };
      detail = payload.detail || detail;
    } catch {
      // Keep fallback status text.
    }
    throw new Error(detail || `request_failed_${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
