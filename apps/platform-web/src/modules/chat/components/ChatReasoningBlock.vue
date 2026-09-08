<script setup lang="ts">
import { ref, computed } from 'vue'
import BaseIcon from '@/components/base/BaseIcon.vue'
import MarkdownContent from '@/components/platform/MarkdownContent.vue'

const props = withDefaults(
  defineProps<{
    content: string
    defaultOpen?: boolean
  }>(),
  {
    defaultOpen: false
  }
)

const isOpen = ref(props.defaultOpen)

function toggle() {
  isOpen.value = !isOpen.value
}

const summaryText = computed(() => {
  const len = props.content.trim().length
  if (len === 0) return '深度思考过程'
  return `思考过程 (${len} 字)`
})
</script>

<template>
  <div class="overflow-hidden rounded-xl border border-gray-200/80 bg-gray-50/70 shadow-xs transition-all dark:border-dark-800 dark:bg-dark-900/40">
    <button
      type="button"
      class="flex w-full items-center justify-between px-4 py-2.5 text-left text-xs font-medium text-gray-600 transition-colors hover:bg-gray-100/70 dark:text-dark-300 dark:hover:bg-dark-800/60"
      @click="toggle"
    >
      <div class="flex items-center gap-2">
        <BaseIcon
          name="sparkle"
          size="xs"
          class="text-primary-600 dark:text-primary-400 shrink-0"
        />
        <span class="font-medium text-gray-700 dark:text-dark-200">{{ summaryText }}</span>
        <span class="rounded bg-gray-200/60 px-1.5 py-0.5 text-[10px] text-gray-500 dark:bg-dark-800 dark:text-dark-400">
          {{ isOpen ? '收起' : '展开' }}
        </span>
      </div>
      <BaseIcon
        :name="isOpen ? 'chevron-down' : 'chevron-right'"
        size="xs"
        class="text-gray-400 dark:text-dark-500 shrink-0"
      />
    </button>

    <div
      v-show="isOpen"
      class="border-t border-gray-200/60 bg-white/50 px-4 py-3 text-xs leading-relaxed text-gray-700 dark:border-dark-800/80 dark:bg-dark-950/20 dark:text-dark-300"
    >
      <MarkdownContent :content="content" />
    </div>
  </div>
</template>
