import { Suspense, type ReactNode } from "react";

import { WorkspaceAuthGuard } from "@/components/platform/workspace-auth-guard";
import { LogBootstrap } from "@/components/platform/log-bootstrap";
import { WorkspaceShell } from "@/components/platform/workspace-shell";
import { WorkspaceProvider } from "@/providers/WorkspaceContext";

export default function WorkspaceLayout({ children }: { children: ReactNode }) {
  return (
    <Suspense fallback={<div className="p-6">Loading workspace...</div>}>
      <WorkspaceAuthGuard>
        <WorkspaceProvider>
          <LogBootstrap />
          <WorkspaceShell>{children}</WorkspaceShell>
        </WorkspaceProvider>
      </WorkspaceAuthGuard>
    </Suspense>
  );
}
