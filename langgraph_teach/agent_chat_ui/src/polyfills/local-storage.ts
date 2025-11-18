/**
 * Next.js dev server (Node.js 22+) registers a partial localStorage shim that
 * throws when its methods are called. Some client-only libraries (e.g. nuqs)
 * touch localStorage during module evaluation, even while running on the server.
 * We provide a minimal in-memory polyfill so those calls become harmless.
 */
const globalWithStorage = globalThis as typeof globalThis & {
  localStorage?: Storage;
};

const shouldPolyfill =
  typeof window === "undefined" &&
  (!globalWithStorage.localStorage ||
    typeof globalWithStorage.localStorage.getItem !== "function" ||
    typeof globalWithStorage.localStorage.setItem !== "function" ||
    typeof globalWithStorage.localStorage.removeItem !== "function");

if (shouldPolyfill) {
  const store = new Map<string, string>();

  const memoryStorage: Storage = {
    getItem(key: string): string | null {
      return store.has(key) ? store.get(key)! : null;
    },
    setItem(key: string, value: string): void {
      store.set(key, String(value));
    },
    removeItem(key: string): void {
      store.delete(key);
    },
    clear(): void {
      store.clear();
    },
    key(index: number): string | null {
      return Array.from(store.keys())[index] ?? null;
    },
    get length(): number {
      return store.size;
    },
  };

  globalWithStorage.localStorage = memoryStorage;
}
