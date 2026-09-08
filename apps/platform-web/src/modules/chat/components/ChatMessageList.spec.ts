import type { Message } from '@langchain/langgraph-sdk'
import type { AnyStream } from '@langchain/vue'
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import type { AgentDisplayMessage } from '../agent-types'
import ChatMessageList from './ChatMessageList.vue'

function buildAgentDisplayMessage(): AgentDisplayMessage {
  return {
    id: 'msg-1',
    author: 'agent',
    timestamp: new Date().toISOString(),
    chunks: [
      {
        kind: 'reasoning',
        text: 'This is some internal reasoning.'
      },
      {
        kind: 'tool-execution',
        toolCallId: 'tool-1',
        timestamp: new Date().toISOString(),
        title: 'search_docs',
        toolKind: 'search',
        input: { query: 'langgraph streaming' },
        status: 'completed',
        output: 'found 3 results'
      },
      {
        kind: 'text',
        text: '这里是一次带工具调用的回复。'
      }
    ]
  }
}

describe('ChatMessageList', () => {
  it('renders reasoning, tool execution, and text chunks properly', async () => {
    const displayMessage = buildAgentDisplayMessage()
    const wrapper = mount(ChatMessageList, {
      props: {
        displayMessages: [displayMessage],
        allMessages: [],
        editingMessageId: '',
        editingMessageValue: '',
        isRunning: false,
        streamHandle: {} as AnyStream,
        toolCalls: [],
        getMessageMeta: () => undefined,
        getMessageBranchIndex: () => 0,
        hasBranchSwitcher: () => false,
        canEditMessage: () => false,
        canRetryMessage: () => false
      },
      global: {
        stubs: {
          ChatMessageRuntimeMetadata: {
            props: ['stream', 'messageId'],
            template: '<slot :metadata="undefined" />'
          },
          MarkdownContent: {
            props: ['content'],
            template: '<div class="markdown-content">{{ content }}</div>'
          },
          BaseIcon: {
            props: ['name'],
            template: '<span :class="name"></span>'
          }
        }
      }
    })

    // Contains reasoning summary
    expect(wrapper.text()).toContain('思考过程')
    // Contains tool execution title
    expect(wrapper.text()).toContain('search_docs')
    // Contains text
    expect(wrapper.text()).toContain('这里是一次带工具调用的回复。')
  })
})
