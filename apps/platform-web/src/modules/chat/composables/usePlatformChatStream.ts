import { useStream } from '@langchain/vue'
import type { Message } from '@langchain/langgraph-sdk'
import { computed, ref, watch } from 'vue'
import {
  createLanggraphAuthorizedFetch,
  getLanggraphApiUrl
} from '@/services/langgraph/client'
import {
  getRuntimeRunStatus,
  normalizeRuntimeGatewayError
} from '@/services/runtime-gateway/workspace.service'
import { summarizeMessageContent, type ChatAttachmentBlock } from '@/utils/chat-content'
import {
  buildChatMessageMetadata,
  getChatBranchContext,
  normalizeHistoryStates
} from '../branching'
import { createPlatformChatStreamActions } from './platform-chat-stream/actions'
import {
  extractInterruptPayload,
  extractThreadFailureMessage,
  toLegacyMessage
} from './platform-chat-stream/helpers'
import type { ChatState, UsePlatformChatStreamOptions } from './platform-chat-stream/types'
import { streamMessagesToUi } from '../stream-messages-to-ui'
import type { AgentDisplayMessage } from '../agent-types'

export function usePlatformChatStream(options: UsePlatformChatStreamOptions) {
  const commandPending = ref(false)
  const cancelling = ref(false)
  const detailError = ref('')
  const detailInfo = ref('')
  const lastRunId = ref('')
  const lastEventAt = ref('')
  const reconciledTerminal = ref(false)
  const reconciledInterrupted = ref(false)
  const preferPersistedProjection = ref(false)

  const reconcileMissedTerminal = async (runId: string) => {
    const threadId = options.activeThreadId.value.trim()
    const projectId = options.projectId.value.trim();
    if (!projectId || !threadId || !runId) return

    for (let attempt = 0; attempt < 20 && stream.isLoading.value; attempt += 1) {
      await new Promise((resolve) => window.setTimeout(resolve, 250))
      const status = await getRuntimeRunStatus(projectId, threadId, runId).catch(() => '')
      if (
        ![
          'success',
          'succeeded',
          'completed',
          'error',
          'failed',
          'cancelled',
          'canceled',
          'interrupted'
        ].includes(status)
      ) {
        continue
      }
      if (options.activeThreadId.value.trim() !== threadId) {
        return
      }
      reconciledInterrupted.value = status === 'interrupted'
      reconciledTerminal.value = !reconciledInterrupted.value
      await stream.stop({ cancel: false })
      await options.onRefreshThread(threadId)
      return
    }
  }

  const authorizedFetch = createLanggraphAuthorizedFetch()
  const creationProjectId = options.projectId.value.trim()
  const scopedFetch: typeof fetch = (input, init) => {
    const headers = new Headers(init?.headers)
    if (creationProjectId) {
      headers.set('x-project-id', creationProjectId)
    } else {
      headers.delete('x-project-id')
    }
    return authorizedFetch(input, { ...init, headers })
  }

  const stream = useStream<ChatState>({
    apiUrl: getLanggraphApiUrl(),
    callerOptions: { fetch: scopedFetch },
    fetch: scopedFetch,
    assistantId: options.target.value?.resolvedTargetId || '',
    threadId: () => options.activeThreadId.value || null,
    messagesKey: 'messages',
    initialValues: {
      messages: []
    },
    onThreadId: (threadId) => {
      options.activeThreadId.value = threadId
      lastRunId.value = ''
      preferPersistedProjection.value = false
      detailInfo.value = ''
    },
    onCreated: ({ runId }) => {
      commandPending.value = false
      lastRunId.value = runId.trim()
      preferPersistedProjection.value = false
      void reconcileMissedTerminal(lastRunId.value)
    },
    onCompleted: async ({ reason }) => {
      const completedThreadId = stream.threadId.value?.trim() || options.activeThreadId.value.trim()
      if (!completedThreadId || completedThreadId !== options.activeThreadId.value.trim()) {
        reconciledTerminal.value = false
        return
      }

      const completedError =
        reason === 'error' && stream.error.value !== undefined && stream.error.value !== null
          ? normalizeRuntimeGatewayError(stream.error.value, '对话运行失败').message
          : ''
      commandPending.value = false
      cancelling.value = false
      lastEventAt.value = new Date().toISOString()

      if (reason === 'stopped' && reconciledTerminal.value) {
        detailInfo.value = '本轮运行已完成，页面已同步服务端结果。'
      }
      if (reason === 'stopped' && reconciledInterrupted.value) {
        detailInfo.value = '本轮运行等待人工确认，请处理下方确认事项后继续。'
      }

      reconciledTerminal.value = false
      reconciledInterrupted.value = false

      await options.onRefreshThread(options.activeThreadId.value, {
        preserveInfo: reason === 'stopped'
      })

      preferPersistedProjection.value = true

      if (completedError) {
        detailError.value = completedError
      }
    }
  })

  const historyStates = computed(() => normalizeHistoryStates(options.historyItems.value))
  const streamMatchesActiveThread = computed(() => {
    const activeThreadId = options.activeThreadId.value.trim()
    return Boolean(activeThreadId) && stream.threadId.value === activeThreadId
  })
  const branchContext = computed(() =>
    getChatBranchContext(options.selectedBranch.value, historyStates.value)
  )
  const selectedBranchValues = computed<Record<string, unknown> | null>(() => {
    if (!options.selectedBranch.value.trim()) {
      return null
    }

    const values = branchContext.value.threadHead?.values
    return values && typeof values === 'object' ? (values as Record<string, unknown>) : null
  })
  const persistedHeadState = computed<Record<string, unknown> | null>(() => {
    const head = branchContext.value.threadHead
    const values = head?.values
    if (!values || typeof values !== 'object') {
      return null
    }
    const persistedHead = head as unknown as Record<string, unknown>

    return {
      ...(values as Record<string, unknown>),
      interrupts: persistedHead.interrupts,
      tasks: persistedHead.tasks
    }
  })
  const displayState = computed<Record<string, unknown> | null>(() => {
    const liveValues = streamMatchesActiveThread.value ? stream.values.value : null
    const values =
      selectedBranchValues.value ||
      (stream.isLoading.value ? liveValues : persistedHeadState.value) ||
      liveValues
    return values && typeof values === 'object' ? (values as Record<string, unknown>) : null
  })
  const messages = computed<Message[]>(() => {
    const branchMessages = selectedBranchValues.value?.messages
    if (Array.isArray(branchMessages)) {
      return branchMessages as Message[]
    }

    const liveMessages = streamMatchesActiveThread.value
      ? stream.messages.value.map((message) => toLegacyMessage(message))
      : []
    const persistedMessages = Array.isArray(persistedHeadState.value?.messages)
      ? (persistedHeadState.value?.messages as Message[])
      : []

    if (preferPersistedProjection.value && persistedMessages.length > 0) {
      return persistedMessages
    }

    if (stream.isLoading.value || liveMessages.length > 0) {
      if (persistedMessages.length === 0) {
        return liveMessages
      }
      const persistedIds = new Set(persistedMessages.map((m) => m.id).filter(Boolean))
      const additionalLive = liveMessages.filter((m) => !m.id || !persistedIds.has(m.id))
      return [...persistedMessages, ...additionalLive]
    }

    return persistedMessages
  })

  // === 新增的解析层，不破坏原有 messages ===
  const uiMessages = computed<AgentDisplayMessage[]>(() => {
    const rawToolCalls = streamMatchesActiveThread.value ? stream.toolCalls.value : []
    return streamMessagesToUi(messages.value, rawToolCalls)
  })

  const messageMetadataById = computed(() =>
    buildChatMessageMetadata(messages.value, historyStates.value, branchContext.value)
  )

  const interruptPayload = computed(() => {
    const liveInterrupts = streamMatchesActiveThread.value ? stream.interrupts.value : []
    if (liveInterrupts.length === 1) {
      return liveInterrupts[0]
    }
    if (liveInterrupts.length > 1) {
      return liveInterrupts
    }

    return extractInterruptPayload({
      ...(displayState.value || {}),
      tasks: displayState.value?.tasks
    })
  })
  const threadFailureMessage = computed(() =>
    extractThreadFailureMessage(
      displayState.value,
      options.activeThreadStatus.value,
      options.activeThreadError.value
    )
  )
  const isViewingBranch = computed(() => options.selectedBranch.value.trim().length > 0)
  const sending = computed(() => commandPending.value || stream.isLoading.value)
  const actions = createPlatformChatStreamActions({
    stream,
    options,
    commandPending,
    isBusy: sending,
    cancelling,
    detailError,
    detailInfo,
    lastRunId,
    lastEventAt,
    messages,
    messageMetadataById,
    interruptPayload
  })

  watch(
    () => options.activeThreadId.value,
    () => {
      preferPersistedProjection.value = false
    }
  )

  watch(
    () => stream.isLoading.value,
    (isLoading) => {
      if (isLoading) {
        commandPending.value = false
        lastEventAt.value = new Date().toISOString()
      }
    },
    { immediate: true }
  )

  watch(
    () => stream.error.value,
    (streamError) => {
      if (streamError !== undefined && streamError !== null) {
        detailError.value = normalizeRuntimeGatewayError(streamError, '对话运行失败').message
      }
    }
  )

  return {
    cancelling,
    cancelActiveRun: actions.cancelActiveRun,
    clearDetailFeedback: actions.clearDetailFeedback,
    detailError,
    detailInfo,
    displayState,
    editHumanMessage: actions.editHumanMessage,
    historyItems: options.historyItems,
    interruptPayload,
    isViewingBranch,
    lastEventAt,
    lastRunId,
    latestMessagePreview: computed(() => {
      const lastMessage = messages.value[messages.value.length - 1]
      return lastMessage ? summarizeMessageContent(lastMessage.content) : ''
    }),
    messageMetadataById,
    messages,
    uiMessages, // <== 新增暴露
    resetStreamView: actions.resetStreamView,
    resumeAllInterruptedRuns: actions.resumeAllInterruptedRuns,
    resumeInterruptedRun: actions.resumeInterruptedRun,
    retryMessage: actions.retryMessage,
    selectBranch: actions.selectBranch,
    selectedBranch: options.selectedBranch,
    sendMessage: (content: string, attachments: ChatAttachmentBlock[] = []) =>
      actions.sendMessage(content, attachments),
    sending,
    streamHandle: stream,
    threadFailureMessage,
    toolCalls: computed(() =>
      streamMatchesActiveThread.value ? stream.toolCalls.value : []
    )
  }
}
