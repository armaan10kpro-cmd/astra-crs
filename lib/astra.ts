export type BackendStatus = string | null | undefined

export type EvidenceState = {
  status?: BackendStatus
  value?: unknown
  detail?: string
}

export type AstraEvidence = {
  target?: string
  findingId?: string
  stage?: BackendStatus
  elapsed?: string
  patchVerdict?: BackendStatus
  runtimeMode?: BackendStatus
  modelMode?: BackendStatus
  proofStatus?: BackendStatus
  pipeline?: Record<string, BackendStatus>
  discovery?: Record<string, unknown>
  repair?: Record<string, unknown>
  verification?: Record<string, EvidenceState>
  runtime?: Record<string, unknown>
  evidence?: Record<string, unknown>
}

export type AstraSnapshot = {
  available: boolean
  loading: boolean
  error?: string
  data?: AstraEvidence
}

const API_URL = process.env.NEXT_PUBLIC_ASTRA_API_URL

export function normalizeSnapshot(input: unknown): AstraSnapshot {
  if (!input || typeof input !== 'object') return { available: false, loading: false }
  return { available: true, loading: false, data: input as AstraEvidence }
}

export async function getAstraSnapshot(signal?: AbortSignal): Promise<AstraSnapshot> {
  if (!API_URL) return { available: false, loading: false }
  try {
    const response = await fetch(`${API_URL.replace(/\/$/, '')}/snapshot`, { signal, cache: 'no-store' })
    if (!response.ok) return { available: false, loading: false, error: `Backend returned ${response.status}` }
    return normalizeSnapshot(await response.json())
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw error
    return { available: false, loading: false, error: 'ASTRA backend unavailable' }
  }
}

export function displayStatus(value: BackendStatus, fallback = 'NOT RUN') {
  return value == null || value === '' ? fallback : value
}

export function isExplicit(value: BackendStatus, expected: string) {
  return value === expected
}

export const initialSnapshot: AstraSnapshot = { available: false, loading: true }
export const pipelineStages = ['DISCOVER', 'LOCALIZE', 'REASON', 'REPAIR', 'VERIFY', 'ADVERSARIAL', 'REGRESSION', 'RUNTIME', 'PROOF']

export function readValue(record: Record<string, unknown> | undefined, key: string) {
  const value = record?.[key]
  return typeof value === 'string' || typeof value === 'number' ? String(value) : undefined
}

export function readEvidence(record: Record<string, EvidenceState> | undefined, key: string) {
  return record?.[key]?.status
}

export function seedSnapshotFromEnv(): AstraSnapshot {
  const raw = process.env.NEXT_PUBLIC_ASTRA_INITIAL_EVIDENCE
  if (!raw) return { available: false, loading: false }
  try { return normalizeSnapshot(JSON.parse(raw)) } catch { return { available: false, loading: false, error: 'Invalid initial evidence payload' } }
}
