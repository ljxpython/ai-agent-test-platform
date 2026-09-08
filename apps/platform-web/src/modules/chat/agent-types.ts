export type AcpToolKind =
  | 'read'
  | 'edit'
  | 'delete'
  | 'move'
  | 'search'
  | 'execute'
  | 'think'
  | 'fetch'
  | 'slack'
  | 'linear'
  | 'task'
  | 'other'

export type AcpToolStatus = 'pending' | 'in_progress' | 'completed' | 'error'

export interface AcpToolLocation {
  path: string
  line?: number
}

export interface DiffData {
  originalContent: string | null
  newContent: string
  filePath: string
  isNewFile: boolean
  isBinary: boolean
  isTruncated: boolean
  totalLines: number
}

export type OutputIframeDisplay =
  | {
      type: 'output_iframe'
      previewUrl: string
      downloadUrl: string
      title: string
      filename: string
    }
  | {
      type: 'output_iframe'
      html: string
      title: string
      filename: string
    }

export interface ToolExecutionChunk {
  kind: 'tool-execution'
  toolCallId: string
  timestamp?: string
  title: string
  toolKind: AcpToolKind
  input?: Record<string, unknown>
  status: AcpToolStatus
  output?: string
  display?: OutputIframeDisplay
  elapsedMs?: number
  diffData?: DiffData
  diffs?: Array<DiffData>
  locations?: Array<AcpToolLocation>
  subagentNamespace?: Array<string>
}

export interface TextChunk {
  kind: 'text'
  text: string
}

export interface ReasoningChunk {
  kind: 'reasoning'
  text: string
}

export interface CodeChunk {
  kind: 'code'
  text: string
  language?: string
}

export interface ErrorChunk {
  kind: 'error'
  text: string
}

export interface ListChunk {
  kind: 'list'
  lines: Array<string>
}

export interface ImageChunk {
  kind: 'image'
  base64: string
  mimeType: string
  fileName?: string
}

export type Chunk =
  | TextChunk
  | ReasoningChunk
  | CodeChunk
  | ErrorChunk
  | ListChunk
  | ToolExecutionChunk
  | ImageChunk

export interface AgentDisplayMessage {
  id: string
  author: 'user' | 'agent' | 'system'
  timestamp: string
  startedAt?: string
  timestampIsFallback?: boolean
  chunks: Array<Chunk>
}
