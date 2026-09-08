<script setup lang="ts">
import { computed, ref } from 'vue'
import BaseIcon from '@/components/base/BaseIcon.vue'
import type { ToolExecutionChunk } from '../agent-types'

const props = defineProps<{
  chunk: ToolExecutionChunk
}>()

const isExpanded = ref(false)

const statusIcon = computed(() => {
  switch (props.chunk.status) {
    case 'completed': return 'check'
    case 'error': return 'x' // or alert
    case 'in_progress':
    case 'pending':
    default: return 'refresh' // we can add a spin class
  }
})

const statusColor = computed(() => {
  switch (props.chunk.status) {
    case 'completed': return 'text-green-600'
    case 'error': return 'text-red-600'
    default: return 'text-blue-600 animate-spin'
  }
})

const formattedInput = computed(() => {
  if (!props.chunk.input) return ''
  try {
    return JSON.stringify(props.chunk.input, null, 2)
  } catch {
    return String(props.chunk.input)
  }
})
</script>

<template>
  <div class="chat-tool-call-card overflow-hidden rounded-xl border border-gray-200/80 bg-gray-50/70 p-3.5 shadow-xs text-xs font-sans transition-all dark:border-dark-800 dark:bg-dark-900/40">
    <div 
      class="flex items-center gap-2 cursor-pointer select-none"
      @click="isExpanded = !isExpanded"
    >
      <BaseIcon :name="statusIcon" :class="statusColor" size="sm" />
      <span class="font-medium text-gray-800 dark:text-dark-200">{{ chunk.title }}</span>
      <span v-if="chunk.elapsedMs" class="text-xs text-gray-400 ml-auto">{{ chunk.elapsedMs }}ms</span>
      <BaseIcon :name="isExpanded ? 'chevron-down' : 'chevron-right'" size="xs" class="text-gray-400" />
    </div>

    <div v-show="isExpanded" class="mt-3 text-xs flex flex-col gap-2.5">
      <div v-if="formattedInput && formattedInput !== '{}'" class="rounded-lg border border-gray-200/60 bg-white/80 p-3 dark:border-dark-800 dark:bg-dark-950/60 overflow-x-auto">
        <div class="font-semibold text-gray-500 dark:text-dark-400 mb-1">Input</div>
        <pre class="text-gray-700 dark:text-dark-200 font-mono text-[11px]">{{ formattedInput }}</pre>
      </div>

      <div v-if="chunk.status === 'completed' || chunk.status === 'error'" class="rounded-lg border border-gray-200/60 bg-white/80 p-3 dark:border-dark-800 dark:bg-dark-950/60 overflow-x-auto max-h-60 overflow-y-auto">
        <div class="font-semibold mb-1" :class="chunk.status === 'error' ? 'text-red-500' : 'text-gray-500 dark:text-dark-400'">
          Output
        </div>
        <pre :class="chunk.status === 'error' ? 'text-red-600 dark:text-red-400' : 'text-gray-700 dark:text-dark-200'" class="whitespace-pre-wrap break-words font-mono text-[11px]">{{ chunk.output || 'No output' }}</pre>
      </div>
    </div>
  </div>
</template>
