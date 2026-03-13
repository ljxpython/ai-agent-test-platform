"use client";

import { BaseChatTemplate } from "@/components/chat-template/base-chat-template";

export default function WorkspaceChatPage() {
  return (
    <BaseChatTemplate
      target={{ targetType: "assistant" }}
      display={{
        title: "Agent Chat",
        description:
          "Welcome to Agent Chat! Before you get started, you need to enter the URL of the deployment and the assistant / graph ID.",
      }}
      features={{
        allowAssistantSwitch: true,
        allowApiUrlEdit: true,
        allowRunOptions: true,
        showHistory: true,
        showArtifacts: true,
        showContextBar: true,
      }}
    />
  );
}
