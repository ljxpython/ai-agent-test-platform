import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import ChatModelSelector from './ChatModelSelector.vue'
import type { RuntimeModelItem } from '@/types/management'

const mockModels: RuntimeModelItem[] = [
  {
    id: 'm-1',
    model_id: 'DeepSeek-V4-Flash',
    display_name: 'DeepSeek V4 Flash (中转)',
    provider: 'deepseek-proxy',
    base_url: 'http://120.48.180.39:20002/v1',
    protocol: 'openai-compatible',
    enabled: true,
    credential_configured: true,
    is_default: true
  },
  {
    id: 'm-2',
    model_id: 'gpt-5.6-terra',
    display_name: 'GPT 5.6 Terra (中转)',
    provider: 'gpt-proxy',
    base_url: 'https://wawapii.com/v1',
    protocol: 'openai-compatible',
    enabled: true,
    credential_configured: true,
    is_default: false
  }
]

describe('ChatModelSelector', () => {
  it('renders default model name when selectedModelId is empty', () => {
    const wrapper = mount(ChatModelSelector, {
      props: {
        models: mockModels,
        selectedModelId: '',
        defaultModelName: 'DeepSeek V4 Flash (中转)'
      },
      global: {
        stubs: {
          RouterLink: true
        }
      }
    })

    expect(wrapper.text()).toContain('默认: DeepSeek V4 Flash (中转)')
  })

  it('renders specific model display name and provider badge when selected', () => {
    const wrapper = mount(ChatModelSelector, {
      props: {
        models: mockModels,
        selectedModelId: 'gpt-5.6-terra'
      },
      global: {
        stubs: {
          RouterLink: true
        }
      }
    })

    expect(wrapper.text()).toContain('GPT 5.6 Terra (中转)')
    expect(wrapper.text()).toContain('GPT中转')
  })

  it('opens panel on trigger click and emits update:selectedModelId on option click', async () => {
    const wrapper = mount(ChatModelSelector, {
      props: {
        models: mockModels,
        selectedModelId: ''
      },
      attachTo: document.body,
      global: {
        stubs: {
          RouterLink: true
        }
      }
    })

    const triggerBtn = wrapper.find('button[title="选择对话运行模型"]')
    expect(triggerBtn.exists()).toBe(true)

    // Open dropdown
    await triggerBtn.trigger('click')

    // Find in document.body (due to Teleport)
    const dropdown = document.body.querySelector('.shadow-2xl')
    expect(dropdown).not.toBeNull()
    expect(dropdown?.textContent).toContain('切换对话模型')
    expect(dropdown?.textContent).toContain('DeepSeek V4 Flash (中转)')
    expect(dropdown?.textContent).toContain('GPT 5.6 Terra (中转)')

    // Click on GPT model option
    const gptOption = Array.from(document.body.querySelectorAll('.cursor-pointer')).find((el) =>
      el.textContent?.includes('GPT 5.6 Terra (中转)')
    )
    expect(gptOption).toBeDefined()
    ;(gptOption as HTMLElement)?.click()

    expect(wrapper.emitted('update:selectedModelId')?.[0]).toEqual(['gpt-5.6-terra'])
  })
})
