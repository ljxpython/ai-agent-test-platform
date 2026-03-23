const API_KEY_STORAGE_KEY = "lg:chat:apiKey";

export function getApiKey(): string | null {
  if (typeof window === "undefined") {
    return null;
  }

  const value = window.localStorage.getItem(API_KEY_STORAGE_KEY)?.trim();
  return value ? value : null;
}
