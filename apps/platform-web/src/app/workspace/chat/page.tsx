"use client";

import { ArtifactProvider } from "@/components/thread/artifact";
import { Thread } from "@/components/thread";
import { Toaster } from "@/components/ui/sonner";
import { StreamProvider } from "@/providers/Stream";
import { ThreadProvider } from "@/providers/Thread";
import React from "react";

export default function WorkspaceChatPage(): React.ReactNode {
  return (
    <React.Suspense fallback={<div>Loading chat...</div>}>
      <Toaster />
      <ThreadProvider>
        <StreamProvider>
          <ArtifactProvider>
            <Thread />
          </ArtifactProvider>
        </StreamProvider>
      </ThreadProvider>
    </React.Suspense>
  );
}
