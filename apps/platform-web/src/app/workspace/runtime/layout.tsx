import type { ReactNode } from "react";

import { RuntimeSectionsNav } from "@/components/platform/runtime-sections-nav";

export default function RuntimeLayout({ children }: { children: ReactNode }) {
  return (
    <section className="p-4 sm:p-6">
      <h2 className="text-xl font-semibold tracking-tight">Runtime</h2>
      <p className="text-muted-foreground mt-2 text-sm">
        Read-only view of LangGraph runtime capabilities, split by models and tools.
      </p>
      <RuntimeSectionsNav />
      <div className="mt-6">{children}</div>
    </section>
  );
}
