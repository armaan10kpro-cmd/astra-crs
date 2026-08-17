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

const API_URL = import.meta.env.VITE_ASTRA_API_URL || 'http://localhost:8080'

export function normalizeSnapshot(input: unknown): AstraSnapshot {
  if (!input || typeof input !== 'object') {
    return {
      available: false,
      loading: false,
      error: 'Invalid backend response',
    }
  }

  const payload = input as {
    status?: string
    last_run?: Record<string, unknown> | null
  }

  const run = payload.last_run

  if (!run) {
    return {
      available: true,
      loading: false,
      data: {},
    }
  }

  const finalStatus =
    typeof run.final_status === 'string'
      ? run.final_status
      : payload.status

  const findingId =
    typeof run.finding_id === 'string'
      ? run.finding_id
      : undefined

  const resources =
    run.resources && typeof run.resources === 'object'
      ? (run.resources as { elapsed_seconds?: number })
      : undefined

  const rawDiscovery =
    run.discovery && typeof run.discovery === 'object'
      ? (run.discovery as Record<string, unknown>)
      : undefined

  const finding =
    rawDiscovery?.finding &&
    typeof rawDiscovery.finding === 'object'
      ? (rawDiscovery.finding as Record<string, unknown>)
      : undefined

  const fuzz =
    rawDiscovery?.fuzz &&
    typeof rawDiscovery.fuzz === 'object'
      ? (rawDiscovery.fuzz as Record<string, unknown>)
      : undefined

  const fuzzCrash =
    fuzz?.crash &&
    typeof fuzz.crash === 'object'
      ? (fuzz.crash as Record<string, unknown>)
      : undefined

  const runtimeLayer =
    run.runtime_layer &&
    typeof run.runtime_layer === 'object'
      ? (run.runtime_layer as Record<string, unknown>)
      : undefined

  const symbolic =
    run.symbolic_verification &&
    typeof run.symbolic_verification === 'object'
      ? (run.symbolic_verification as Record<string, unknown>)
      : undefined

  const adversarial =
    run.adversarial &&
    typeof run.adversarial === 'object'
      ? (run.adversarial as Record<string, unknown>)
      : undefined

  const regression =
    run.regression &&
    typeof run.regression === 'object'
      ? (run.regression as Record<string, unknown>)
      : undefined

  const attempts = Array.isArray(run.attempts)
    ? run.attempts
    : []

  const firstAttempt =
    attempts.length > 0 &&
    typeof attempts[0] === 'object' &&
    attempts[0] !== null
      ? (attempts[0] as Record<string, unknown>)
      : undefined

  const events = Array.isArray(runtimeLayer?.events)
    ? runtimeLayer.events
    : []

  const latestEvent =
    events.length > 0
      ? events[events.length - 1]
      : undefined

  const discovery: Record<string, unknown> = {
    severity:
      typeof finding?.severity === 'string'
        ? finding.severity
        : undefined,

    function:
      typeof finding?.function === 'string'
        ? finding.function
        : undefined,

    file:
      typeof finding?.source_file === 'string'
        ? finding.source_file
        : undefined,

    location:
      finding?.line != null
        ? String(finding.line)
        : undefined,

    sanitizer:
      typeof finding?.sanitizer === 'string'
        ? finding.sanitizer
        : undefined,

    fuzzingMode:
      typeof fuzz?.engine === 'string'
        ? fuzz.engine
        : undefined,

    crashId:
  typeof fuzzCrash?.crash_id === 'string'
    ? fuzzCrash.crash_id
    : typeof (
        rawDiscovery?.crash as Record<string, unknown> | undefined
      )?.crash_id === 'string'
      ? (
          rawDiscovery?.crash as Record<string, unknown>
        ).crash_id as string
      : undefined,
    reproducer:
      typeof finding?.reproducer === 'string'
        ? finding.reproducer
        : undefined,

    stackTrace:
      typeof finding?.stack_trace === 'string'
        ? finding.stack_trace
        : undefined,

    sourceContext:
      typeof finding?.source_slice === 'string'
        ? finding.source_slice
        : undefined,
  }

  const repair: Record<string, unknown> = {
  candidateAttempts: attempts.length,

  compileStatus:
    firstAttempt?.built === true
      ? 'PASS'
      : firstAttempt?.built === false
        ? 'FAIL'
        : undefined,

  compileLog:
    typeof firstAttempt?.compiler_log === 'string'
      ? firstAttempt.compiler_log
      : undefined,

  diff:
    typeof firstAttempt?.patch_diff === 'string'
      ? firstAttempt.patch_diff
      : undefined,

  verdict:
    typeof firstAttempt?.verdict === 'string'
      ? firstAttempt.verdict
      : undefined,

  proposalStatus:
    typeof firstAttempt?.proposal_status === 'string'
      ? firstAttempt.proposal_status
      : undefined,

  patchScore:
    firstAttempt?.patch_score != null
      ? String(firstAttempt.patch_score)
      : undefined,

  rootCause:
    typeof finding?.root_cause === 'string'
      ? finding.root_cause
      : typeof run.root_cause === 'string'
        ? run.root_cause
        : undefined,

  modelProposal:
    typeof firstAttempt?.proposal === 'string'
      ? firstAttempt.proposal
      : typeof firstAttempt?.model_proposal === 'string'
        ? firstAttempt.model_proposal
        : undefined,
}
  const verification: Record<string, EvidenceState> = {
    securityProperty: {
      status:
        typeof symbolic?.status === 'string'
          ? symbolic.status
          : undefined,
      detail:
        typeof symbolic?.property === 'string'
          ? symbolic.property
          : undefined,
    },

    z3: {
      status:
        typeof symbolic?.result === 'string'
          ? symbolic.result
          : undefined,
      detail:
        typeof symbolic?.engine === 'string'
          ? symbolic.engine
          : undefined,
    },

    adversarial: {
      status:
        adversarial?.pass === true
          ? 'PASS'
          : typeof adversarial?.status === 'string'
            ? adversarial.status
            : undefined,
      detail:
        typeof adversarial?.attacks_executed === 'number'
          ? `${adversarial.attacks_executed} attacks executed`
          : undefined,
    },

    regression: {
      status:
        regression?.pass === true
          ? 'PASS'
          : typeof regression?.status === 'string'
            ? regression.status
            : undefined,
      detail:
        typeof regression?.passed === 'number' &&
        typeof regression?.mandatory_tests === 'number'
          ? `${regression.passed}/${regression.mandatory_tests} tests passed`
          : undefined,
    },

    patchJudge: {
      status:
        firstAttempt?.verdict === 'FIX_VERIFIED'
          ? 'FIX_VERIFIED'
          : finalStatus,
    },
  }

  const runtime: Record<string, unknown> = {
    verdict:
      typeof runtimeLayer?.attached === 'boolean'
        ? runtimeLayer.attached
          ? 'ATTACHED'
          : 'NOT ATTACHED'
        : undefined,

    mode:
      typeof runtimeLayer?.mode === 'string'
        ? runtimeLayer.mode
        : undefined,

    probe:
      typeof runtimeLayer?.backend === 'string'
        ? runtimeLayer.backend
        : undefined,

    pid:
      latestEvent &&
      typeof latestEvent === 'object' &&
      latestEvent !== null &&
      'pid' in latestEvent &&
      typeof latestEvent.pid === 'number'
        ? String(latestEvent.pid)
        : runtimeLayer?.pid != null
          ? String(runtimeLayer.pid)
          : undefined,

    executable:
      typeof runtimeLayer?.binary === 'string'
        ? runtimeLayer.binary
        : typeof runtimeLayer?.executable === 'string'
          ? runtimeLayer.executable
          : typeof run.discovery === 'object' &&
              run.discovery !== null &&
              'crash' in run.discovery &&
              typeof run.discovery.crash === 'object' &&
              run.discovery.crash !== null &&
              'binary' in run.discovery.crash &&
              typeof run.discovery.crash.binary === 'string'
            ? run.discovery.crash.binary
            : undefined,

    eventCount:
      typeof runtimeLayer?.events_count === 'number'
        ? runtimeLayer.events_count
        : events.length,

    latestEvent:
      latestEvent && typeof latestEvent === 'object'
        ? JSON.stringify(latestEvent, null, 2)
        : typeof latestEvent === 'string'
          ? latestEvent
          : undefined,
  }

  const evidence: Record<string, unknown> = {
    selected:
      typeof run.report_dir === 'string'
        ? `Report directory: ${run.report_dir}`
        : undefined,

    reportDir:
      typeof run.report_dir === 'string'
        ? run.report_dir
        : undefined,
  }

  const pipeline: Record<string, BackendStatus> = {}

  pipeline.DISCOVER = rawDiscovery?.status === 'confirmed'
    ? 'CONFIRMED'
    : undefined

  pipeline.LOCALIZE = rawDiscovery?.localization
    ? 'CONFIRMED'
    : rawDiscovery?.status === 'confirmed'
      ? 'CONFIRMED'
      : undefined

  pipeline.REASON =
    attempts.length > 0
      ? 'PASS'
      : undefined

  pipeline.REPAIR =
    firstAttempt?.built === true
      ? 'PASS'
      : undefined

  pipeline.VERIFY =
    firstAttempt?.checks &&
    typeof firstAttempt.checks === 'object'
      ? 'PASS'
      : undefined

  pipeline.ADVERSARIAL =
    adversarial?.pass === true
      ? 'PASS'
      : undefined

  pipeline.REGRESSION =
    regression?.pass === true
      ? 'PASS'
      : undefined

  pipeline.RUNTIME =
    runtimeLayer?.attached === true
      ? 'ATTACHED'
      : undefined

  pipeline.PROOF =
    typeof run.report_dir === 'string'
      ? 'GENERATED'
      : undefined

  const data: AstraEvidence = {
    target: 'demo_vuln',

    findingId,

    stage: finalStatus,

    elapsed:
      typeof resources?.elapsed_seconds === 'number'
        ? `${resources.elapsed_seconds}s`
        : undefined,

    patchVerdict: finalStatus,

    runtimeMode:
      typeof runtimeLayer?.mode === 'string'
        ? runtimeLayer.mode
        : undefined,

    modelMode:
      typeof run.mode === 'string'
        ? run.mode
        : undefined,

    proofStatus:
      typeof run.report_dir === 'string'
        ? 'GENERATED'
        : finalStatus,

    pipeline,

    discovery,

    repair,

    verification,

    runtime,

    evidence,
  }

  return {
    available: true,
    loading: false,
    data,
  }
}

export async function getAstraSnapshot(
  signal?: AbortSignal,
): Promise<AstraSnapshot> {
  try {
    const response = await fetch(
      `${API_URL.replace(/\/$/, '')}/api/status`,
      {
        signal,
        cache: 'no-store',
      },
    )

    if (!response.ok) {
      return {
        available: false,
        loading: false,
        error: `Backend returned ${response.status}`,
      }
    }

    const json: unknown = await response.json()
    return normalizeSnapshot(json)
  } catch (error) {
    if (
      error instanceof DOMException &&
      error.name === 'AbortError'
    ) {
      throw error
    }

    return {
      available: false,
      loading: false,
      error: 'ASTRA backend unavailable',
    }
  }
}

export function displayStatus(
  value: BackendStatus,
  fallback = 'NOT RUN',
) {
  return value == null || value === '' ? fallback : value
}

export function isExplicit(
  value: BackendStatus,
  expected: string,
) {
  return value === expected
}

export const initialSnapshot: AstraSnapshot = {
  available: false,
  loading: true,
}

export const pipelineStages = [
  'DISCOVER',
  'LOCALIZE',
  'REASON',
  'REPAIR',
  'VERIFY',
  'ADVERSARIAL',
  'REGRESSION',
  'RUNTIME',
  'PROOF',
]

export function readValue(
  record: Record<string, unknown> | undefined,
  key: string,
) {
  const value = record?.[key]

  return typeof value === 'string' || typeof value === 'number'
    ? String(value)
    : undefined
}

export function readEvidence(
  record: Record<string, EvidenceState> | undefined,
  key: string,
) {
  return record?.[key]?.status
}

export function seedSnapshotFromEnv(): AstraSnapshot {
  const raw = import.meta.env.VITE_ASTRA_INITIAL_EVIDENCE

  if (!raw) {
    return {
      available: false,
      loading: false,
    }
  }

  try {
    return normalizeSnapshot(JSON.parse(raw))
  } catch {
    return {
      available: false,
      loading: false,
      error: 'Invalid initial evidence payload',
    }
  }
}
