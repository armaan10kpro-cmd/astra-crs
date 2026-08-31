'use client'

import { useEffect, useMemo, useState } from 'react'
import {
  Archive,
  ArrowRight,
  CheckCircle2,
  ChevronRight,
  CircleDot,
  Code2,
  Database,
  FileCheck2,
  FileText,
  KeyRound,
  LayoutDashboard,
  Menu,
  Radio,
  RefreshCw,
  Search,
  ShieldCheck,
  Siren,
  X,
} from 'lucide-react'

import {
  displayStatus,
  getAstraSnapshot,
  initialSnapshot,
  isExplicit,
  pipelineStages,
  readValue,
  seedSnapshotFromEnv,
  type AstraSnapshot,
} from './astra'

type View =
  | 'overview'
  | 'discovery'
  | 'repair'
  | 'verification'
  | 'runtime'
  | 'evidence'

const nav = [
  ['overview', 'Mission Overview', LayoutDashboard],
  ['discovery', 'Discovery', Search],
  ['repair', 'Repair', Code2],
  ['verification', 'Verification', ShieldCheck],
  ['runtime', 'Runtime Shield', Radio],
  ['evidence', 'Evidence', FileText],
] as const

function StatusPill({
  value,
  tone = 'muted',
}: {
  value?: string | null
  tone?: 'cyan' | 'green' | 'amber' | 'red' | 'muted'
}) {
  const actual = displayStatus(value, 'UNAVAILABLE')

  return (
    <span className={`status-pill ${tone}`}>
      <span className="status-dot" />
      {actual}
    </span>
  )
}

function Panel({
  title,
  eyebrow,
  action,
  children,
  className = '',
}: {
  title: string
  eyebrow?: string
  action?: React.ReactNode
  children: React.ReactNode
  className?: string
}) {
  return (
    <section className={`tactical-panel ${className}`}>
      <div className="panel-heading">
        <div>
          <p className="eyebrow">{eyebrow}</p>
          <h2>{title}</h2>
        </div>
        {action}
      </div>
      {children}
    </section>
  )
}

function Metric({
  label,
  value,
  accent = false,
}: {
  label: string
  value: string
  accent?: boolean
}) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong className={accent ? 'accent-value' : ''}>
        {value}
      </strong>
    </div>
  )
}

function Empty({
  title = 'Evidence unavailable',
  detail = 'Connect an ASTRA backend to populate this view.',
}: {
  title?: string
  detail?: string
}) {
  return (
    <div className="empty-state">
      <Database size={20} />
      <strong>{title}</strong>
      <p>{detail}</p>
    </div>
  )
}

function Overview({
  snapshot,
}: {
  snapshot: AstraSnapshot
}) {
  const data = snapshot.data

  const pipeline = data?.pipeline ?? {}

  const progress = pipelineStages.reduce(
    (count, stage) => pipeline[stage] ? count + 1 : count,
    0,
  )

  const discoveryStatus = pipeline.DISCOVER ?? 'UNAVAILABLE'
  const reasonStatus = pipeline.REASON ?? 'UNAVAILABLE'
  const repairStatus = pipeline.REPAIR ?? 'UNAVAILABLE'
  const verifyStatus = pipeline.VERIFY ?? 'UNAVAILABLE'
  const adversarialStatus = pipeline.ADVERSARIAL ?? 'UNAVAILABLE'
  const regressionStatus = pipeline.REGRESSION ?? 'UNAVAILABLE'
  const runtimeStatus =
    data?.runtime?.mode
      ? String(data.runtime.mode)
      : data?.runtimeMode
        ? String(data.runtimeMode)
        : pipeline.RUNTIME ?? 'UNAVAILABLE'

  const proofStatus =
    data?.proofStatus
      ? String(data.proofStatus)
      : pipeline.PROOF ?? 'UNAVAILABLE'

  const finalStatus = data?.patchVerdict ?? 'UNAVAILABLE'

  return (
    <div className="view-stack">
      <div className="hero-row">
        <div>
          <p className="eyebrow">
            MISSION CONTROL / LIVE TELEMETRY
          </p>

          <h1>
            ASTRA-CRS <span>Mission Overview</span>
          </h1>

          <p className="subtle">
            Autonomous cyber-reasoning and verified repair system
          </p>
        </div>

        <div className="hero-status">
          <span className="live-indicator" />
          {snapshot.available
            ? 'BACKEND CONNECTED'
            : 'BACKEND NOT CONFIGURED'}
        </div>
      </div>

      <div className="metric-grid">
        <Metric
          label="TARGET"
          value={displayStatus(data?.target)}
        />

        <Metric
          label="CURRENT STAGE"
          value={displayStatus(data?.stage)}
          accent
        />

        <Metric
          label="ELAPSED"
          value={displayStatus(data?.elapsed)}
        />

        <Metric
          label="FINDING ID"
          value={displayStatus(data?.findingId)}
        />
      </div>

      <Panel
        title="Mission Pipeline"
        eyebrow="ORCHESTRATION / 09 STAGES"
        action={
          <span className="mono small">
            {progress > 0
              ? `${progress} / ${pipelineStages.length}`
              : 'NO RUN'}
          </span>
        }
      >
        <div className="pipeline">
          {pipelineStages.map((stage, index) => {
            const value = pipeline[stage]

            return (
              <div
                className={`pipeline-stage ${
                  value ? 'has-state' : ''
                }`}
                key={stage}
              >
                <div className="stage-number">
                  {String(index + 1).padStart(2, '0')}
                </div>

                <div className="stage-line" />

                <div className="stage-copy">
                  <strong>{stage}</strong>
                  <span>{displayStatus(value)}</span>
                </div>
              </div>
            )
          })}
        </div>
      </Panel>

      <div className="three-grid">
        <Panel
          title="Patch Verdict"
          eyebrow="SECURITY AUTHORITY"
        >
          <div className="verdict-block">
            <CheckCircle2
              size={28}
              className={
                isExplicit(
                  data?.patchVerdict,
                  'FIX_VERIFIED',
                )
                  ? 'icon-green'
                  : 'icon-muted'
              }
            />

            <div>
              <strong>
                {displayStatus(data?.patchVerdict)}
              </strong>

              <p>Explicit backend evidence only</p>
            </div>
          </div>
        </Panel>

        <Panel
          title="Runtime Mode"
          eyebrow="EXECUTION CONTEXT"
        >
          <div className="verdict-block">
            <Radio size={28} className="icon-cyan" />

            <div>
              <strong>
                {runtimeStatus}
              </strong>

              <p>Backend-reported runtime state</p>
            </div>
          </div>
        </Panel>

        <Panel
          title="Proof Status"
          eyebrow="EVIDENCE CHAIN"
        >
          <div className="verdict-block">
            <FileCheck2
              size={28}
              className="icon-amber"
            />

            <div>
              <strong>
                {proofStatus}
              </strong>

              <p>Proof generation authority</p>
            </div>
          </div>
        </Panel>
      </div>

      <Panel
        title="Evidence Chain"
        eyebrow="PROOF-CARRYING VERIFICATION"
      >
        <div className="three-grid">
          <Metric
            label="DISCOVERY"
            value={discoveryStatus}
          />

          <Metric
            label="REASON"
            value={reasonStatus}
          />

          <Metric
            label="REPAIR"
            value={repairStatus}
          />
        </div>

        <div className="three-grid">
          <Metric
            label="VERIFY"
            value={verifyStatus}
          />

          <Metric
            label="ADVERSARIAL"
            value={adversarialStatus}
          />

          <Metric
            label="REGRESSION"
            value={regressionStatus}
          />
        </div>

        <div className="three-grid">
          <Metric
            label="RUNTIME"
            value={runtimeStatus}
          />

          <Metric
            label="PROOF"
            value={proofStatus}
          />

          <Metric
            label="FINAL"
            value={displayStatus(finalStatus)}
            accent
          />
        </div>
      </Panel>
    </div>
  )
}

function Discovery({
  snapshot,
}: {
  snapshot: AstraSnapshot
}) {
  const d = snapshot.data?.discovery

  return (
    <div className="view-stack">
      <ViewHeader
        eyebrow="PIPELINE / DISCOVER + LOCALIZE"
        title="Discovery"
      />

      <div className="two-grid">
        <Panel
          title="Finding Profile"
          eyebrow="BACKEND EVIDENCE"
        >
          <div className="detail-list">
            <Metric
              label="SEVERITY"
              value={
                readValue(d, 'severity') ?? 'NOT RUN'
              }
            />

            <Metric
              label="FUNCTION"
              value={
                readValue(d, 'function') ?? 'NOT RUN'
              }
            />

            <Metric
              label="SOURCE FILE"
              value={
                readValue(d, 'file') ?? 'NOT RUN'
              }
            />

            <Metric
              label="LOCATION"
              value={
                readValue(d, 'location') ?? 'NOT RUN'
              }
            />
          </div>
        </Panel>

        <Panel
          title="Fuzzing & Sanitizer"
          eyebrow="REPRODUCER TELEMETRY"
        >
          <div className="detail-list">
            <Metric
              label="SANITIZER"
              value={
                readValue(d, 'sanitizer') ?? 'NOT RUN'
              }
            />

            <Metric
              label="FUZZING MODE"
              value={
                readValue(d, 'fuzzingMode') ?? 'NOT RUN'
              }
            />

            <Metric
              label="CRASH ID"
              value={
                readValue(d, 'crashId') ?? 'NOT RUN'
              }
            />

            <Metric
              label="REPRODUCER"
              value={
                readValue(d, 'reproducer') ?? 'NOT RUN'
              }
            />
          </div>
        </Panel>
      </div>

      <Panel
        title="Stack Trace & Source Context"
        eyebrow="INSPECTION"
      >
        <EvidenceText value={d?.stackTrace} />
        <EvidenceText value={d?.sourceContext} />
      </Panel>
    </div>
  )
}

function Repair({
  snapshot,
}: {
  snapshot: AstraSnapshot
}) {
  const d = snapshot.data?.repair

  return (
    <div className="view-stack">
      <ViewHeader
        eyebrow="PIPELINE / REASON + REPAIR"
        title="Repair"
      />

      <div className="three-grid">
        <Panel
          title="Root Cause"
          eyebrow="MODEL OUTPUT"
        >
          <EvidenceText
            value={
              d?.rootCause ??
              'Backend did not emit a separate root-cause artifact for this run.'
            }
          />
        </Panel>

        <Panel
          title="Candidate Attempts"
          eyebrow="PATCH SEARCH"
        >
          <Metric
            label="ATTEMPTS"
            value={
              readValue(d, 'candidateAttempts') ??
              'UNAVAILABLE'
            }
          />

          <Metric
            label="PATCH VERDICT"
            value={
              readValue(d, 'verdict') ??
              'UNAVAILABLE'
            }
          />

          <Metric
            label="COMPILE"
            value={
              readValue(d, 'compileStatus') ??
              'UNAVAILABLE'
            }
          />
        </Panel>

        <Panel
          title="Proposal"
          eyebrow="MODEL MODE"
        >
          <EvidenceText
            value={
              d?.modelProposal ??
              'Backend did not emit a separate model-proposal artifact. The verified candidate patch is shown below.'
            }
          />
        </Panel>
      </div>

      <Panel
        title="Unified Diff"
        eyebrow="PATCH HISTORY"
        action={
          <StatusPill
            value={readValue(d, 'compileStatus')}
            tone="green"
          />
        }
      >
        <pre className="code-view">
          {typeof d?.diff === 'string'
            ? d.diff
            : 'No patch evidence available.'}
        </pre>
      </Panel>
    </div>
  )
}

function Verification({
  snapshot,
}: {
  snapshot: AstraSnapshot
}) {
  const d = snapshot.data?.verification

  const cards = [
    ['securityProperty', 'Security Property'],
    ['z3', 'Symbolic Verification'],
    ['adversarial', 'Adversarial Validation'],
    ['regression', 'Regression Suite'],
    ['patchJudge', 'Deterministic Patch Judge'],
  ] as const

  const symbolicDetail = d?.z3?.detail

  return (
    <div className="view-stack">
      <ViewHeader
        eyebrow="PIPELINE / VERIFY + ADVERSARIAL + REGRESSION"
        title="Verification"
      />

      <div className="verification-grid">
        {cards.map(([key, label]) => {
          const evidence = d?.[key]
          const value = evidence?.status

          return (
            <div
              className="verification-card"
              key={key}
            >
              <div className="verification-icon">
                <ShieldCheck size={20} />
              </div>

              <div>
                <span>{label}</span>

                <strong
                  className={
                    value === 'PASS'
                      ? 'text-green'
                      : value === 'FAIL'
                        ? 'text-red'
                        : ''
                  }
                >
                  {displayStatus(value)}
                </strong>

                {key === 'z3' &&
                  symbolicDetail && (
                    <small className="mono">
                      {symbolicDetail}
                    </small>
                  )}
              </div>

              <ChevronRight size={16} />
            </div>
          )
        })}
      </div>

      <Panel
        title="Verification Authority"
        eyebrow="NO FRONTEND INFERENCE"
      >
        <Empty
          title="Raw verification evidence"
          detail="Each result above is rendered from explicit backend evidence. Symbolic verification also reports the backend-selected verification engine."
        />
      </Panel>
    </div>
  )
}

function Runtime({
  snapshot,
}: {
  snapshot: AstraSnapshot
}) {
  const d = snapshot.data?.runtime

  return (
    <div className="view-stack">
      <ViewHeader
        eyebrow="PIPELINE / RUNTIME"
        title="Runtime Shield"
      />

      <div className="two-grid">
        <Panel
          title="Runtime Verdict"
          eyebrow="EXECUTION MODE"
        >
          <div className="runtime-hero">
            <Siren size={30} />

            <div>
              <strong>
                {readValue(d, 'verdict') ??
                  'UNAVAILABLE'}
              </strong>

              <p>
                {readValue(d, 'mode') ??
                  'UNAVAILABLE'}{' '}
                / explicit backend state
              </p>
            </div>
          </div>

          <div className="runtime-banner">
            {readValue(d, 'mode') ??
              'UNAVAILABLE'}
          </div>
        </Panel>

        <Panel
          title="Target Process"
          eyebrow="OBSERVED SUBJECT"
        >
          <div className="detail-list">
            <Metric
              label="PROBE"
              value={
                readValue(d, 'probe') ??
                'NOT RUN'
              }
            />

            <Metric
              label="PID"
              value={
                readValue(d, 'pid') ??
                'NOT RUN'
              }
            />

            <Metric
              label="EXECUTABLE"
              value={
                readValue(d, 'executable') ??
                'NOT RUN'
              }
            />

            <Metric
              label="EVENT COUNT"
              value={
                readValue(d, 'eventCount') ??
                'NOT RUN'
              }
            />
          </div>
        </Panel>
      </div>

      <Panel
        title="Latest Runtime Event"
        eyebrow="EVENT STREAM"
      >
        <EvidenceText value={d?.latestEvent} />
      </Panel>
    </div>
  )
}

function Evidence({
  snapshot,
}: {
  snapshot: AstraSnapshot
}) {
  const d = snapshot.data?.evidence

  const [selected, setSelected] =
    useState('proof_of_fix.md')

  const artifacts = [
    'finding.json',
    'root cause',
    'patch.diff',
    'compiler logs',
    'symbolic results',
    'adversarial results',
    'regression results',
    'runtime results',
    'proof_of_fix.md',
  ]

  const getArtifactValue = (
    name: string,
  ) => {
    if (name === 'patch.diff') {
      const diff = snapshot.data?.repair?.diff

      return typeof diff === 'string'
        ? diff
        : 'Patch artifact unavailable.'
    }

    if (name === 'finding.json') {
      const finding =
        snapshot.data?.discovery

      return finding
        ? JSON.stringify(
            finding,
            null,
            2,
          )
        : 'Finding artifact unavailable.'
    }

    if (name === 'symbolic results') {
      const value =
        snapshot.data?.verification?.z3

      return value
        ? JSON.stringify(
            value,
            null,
            2,
          )
        : 'Symbolic artifact unavailable.'
    }

    if (
      name ===
      'adversarial results'
    ) {
      const value =
        snapshot.data?.verification
          ?.adversarial

      return value
        ? JSON.stringify(
            value,
            null,
            2,
          )
        : 'Adversarial artifact unavailable.'
    }

    if (
      name === 'regression results'
    ) {
      const value =
        snapshot.data?.verification
          ?.regression

      return value
        ? JSON.stringify(
            value,
            null,
            2,
          )
        : 'Regression artifact unavailable.'
    }

    if (name === 'runtime results') {
      const value =
        snapshot.data?.runtime

      return value
        ? JSON.stringify(
            value,
            null,
            2,
          )
        : 'Runtime artifact unavailable.'
    }

    if (name === 'root cause') {
      return (
        (snapshot.data?.repair
          ?.rootCause as
          | string
          | undefined) ??
        'Backend did not emit a separate root-cause artifact.'
      )
    }

    if (name === 'compiler logs') {
      return (
        (snapshot.data?.repair
          ?.compileLog as
          | string
          | undefined) ??
        'Compiler log unavailable.'
      )
    }

    if (name === 'proof_of_fix.md') {
      return (
        typeof d?.selected ===
        'string'
          ? d.selected
          : 'Proof-of-fix artifact is referenced by the backend report directory.'
      )
    }

    return 'Artifact unavailable.'
  }

  return (
    <div className="view-stack">
      <ViewHeader
        eyebrow="PROOF / EVIDENCE ARTIFACTS"
        title="Evidence"
      />

      <Panel
        title="Proof of Fix"
        eyebrow="FINAL EVIDENCE CHAIN"
      >
        <div className="evidence-grid">
          {artifacts.map((key) => (
            <button
              className={`evidence-item ${
                selected === key
                  ? 'active'
                  : ''
              }`}
              key={key}
              onClick={() =>
                setSelected(key)
              }
            >
              <Archive size={16} />
              <span>{key}</span>
              <ArrowRight size={15} />
            </button>
          ))}
        </div>
      </Panel>

      <Panel
        title="Artifact Inspector"
        eyebrow={`SELECTED / ${selected.toUpperCase()}`}
      >
        <EvidenceText
          value={getArtifactValue(
            selected,
          )}
        />
      </Panel>
    </div>
  )
}

function EvidenceText({
  value,
}: {
  value: unknown
}) {
  return (
    <pre className="evidence-text">
      {typeof value === 'string'
        ? value
        : 'No evidence available.'}
    </pre>
  )
}

function ViewHeader({
  eyebrow,
  title,
}: {
  eyebrow: string
  title: string
}) {
  return (
    <div className="view-header">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
      </div>

      <span className="mono small">
        ASTRA / CRS
      </span>
    </div>
  )
}

export default function AstraDashboard() {
  const [view, setView] =
    useState<View>('overview')

  const [mobileNav, setMobileNav] =
    useState(false)

  const [snapshot, setSnapshot] =
    useState<AstraSnapshot>(
      initialSnapshot,
    )

  useEffect(() => {
    const controller =
      new AbortController()

    getAstraSnapshot(
      controller.signal,
    ).then((live) => {
      if (live.available) {
        setSnapshot(live)
      } else {
        const seed =
          seedSnapshotFromEnv()

        setSnapshot(seed)
      }
    })

    return () =>
      controller.abort()
  }, [])

  const content = useMemo(() => {
    const props = { snapshot }

    if (view === 'discovery') {
      return <Discovery {...props} />
    }

    if (view === 'repair') {
      return <Repair {...props} />
    }

    if (view === 'verification') {
      return (
        <Verification {...props} />
      )
    }

    if (view === 'runtime') {
      return <Runtime {...props} />
    }

    if (view === 'evidence') {
      return <Evidence {...props} />
    }

    return <Overview {...props} />
  }, [snapshot, view])

  return (
    <main className="astra-shell">
      <aside
        className={
          mobileNav
            ? 'sidebar open'
            : 'sidebar'
        }
      >
        <div className="brand">
          <div className="brand-mark">
            A
          </div>

          <div>
            <strong>
              ASTRA-CRS
            </strong>

            <span>
              MISSION CONTROL
            </span>
          </div>

          <button
            className="icon-button mobile-close"
            onClick={() =>
              setMobileNav(false)
            }
            aria-label="Close navigation"
          >
            <X size={18} />
          </button>
        </div>

        <nav aria-label="Primary navigation">
          {nav.map(
            ([key, label, Icon]) => (
              <button
                className={
                  view === key
                    ? 'nav-item active'
                    : 'nav-item'
                }
                key={key}
                onClick={() => {
                  setView(key)
                  setMobileNav(false)
                }}
              >
                <Icon size={17} />

                <span>{label}</span>

                {view === key && (
                  <CircleDot
                    size={11}
                    className="nav-active-dot"
                  />
                )}
              </button>
            ),
          )}
        </nav>

        <div className="sidebar-footer">
          <div className="system-state">
            <span className="live-indicator" />

            <div>
              <strong>
                SYSTEM READY
              </strong>

              <span>
                AUTHORITY: BACKEND
              </span>
            </div>
          </div>

          <span className="mono small">
            v0.1 / LOCAL
          </span>
        </div>
      </aside>

      <div className="content">
        <header className="topbar">
          <button
            className="icon-button menu-button"
            onClick={() =>
              setMobileNav(true)
            }
            aria-label="Open navigation"
          >
            <Menu size={20} />
          </button>

          <div className="breadcrumbs">
            <span>ASTRA</span>
            <ChevronRight
              size={14}
            />

            <strong>
              {
                nav.find(
                  ([key]) =>
                    key === view,
                )?.[1]
              }
            </strong>
          </div>

          <div className="top-actions">
            <span className="connection-label">
              <span className="live-indicator" />
              TELEMETRY
            </span>

            <button
              className="icon-button"
              onClick={() =>
                window.location.reload()
              }
              aria-label="Refresh dashboard"
            >
              <RefreshCw size={17} />
            </button>

            <button className="profile">
              <KeyRound size={15} />
              OPERATOR
            </button>
          </div>
        </header>

        <div className="content-inner">
          {content}
        </div>
      </div>
    </main>
  )
}