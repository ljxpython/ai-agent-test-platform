import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  timeout: 30_000,
  retries: 0,
  use: {
    baseURL: "http://127.0.0.1:3010",
    trace: "on-first-retry",
  },
  webServer: {
    command: "PORT=3010 pnpm dev",
    port: 3010,
    timeout: 120_000,
    reuseExistingServer: true,
    env: {
      NEXT_PUBLIC_AUTO_KEYCLOAK_TOKEN: "false",
      NEXT_PUBLIC_API_URL: "http://127.0.0.1:3010",
    },
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
