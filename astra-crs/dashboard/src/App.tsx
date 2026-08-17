import { useEffect, useState } from 'react'

type RunData = {
  final_status?: string
  finding_id?: string
  mode?: string
  provider?: string
  pipeline?: string[]
  discovery?: { finding?: Record<string, unknown>; status?: string }
  symbolic_verification?: Record<string, unknown>
  adversarial?: Record<string, unknown>
  regression?: Record<string, unknown>
  runtime_layer?: Record<string, unknown>
  resources?: { elapsed_seconds?: number }
  report_dir?: string
}

type Screen = 'overview' | 'discovery' | 'repair' | 'verification' | 'runtime' | 'evidence'

const SCREENS: { id: Screen; label: string }[] = [
  { id: 'overview', label: 'Mission Overview' },
  { id: 'discovery', label: 'Discovery' },
  { id: 'repair', label: 'Repair' },
  { id: 'verification', label: 'Verification' },
  { id: 'runtime', label: 'Runtime Shield' },
  { id: 'evidence', label: 'Evidence' },
]

export default function App() {
  const [screen, setScreen] = useState<Screen>('overview')
  const [data, setData] = useState<RunData | null>(null)
  const [proof, setProof] = useState('')
  const [patch, setPatch] = useState('')

  useEffect(() => {
    fetch('/run.json')
      .then((r) => (r.ok ? r.json() : null))
      .then(setData)
      .catch(() => setData(null))
    fetch('/proof_of_fix.md').then((r) => (r.ok ? r.text() : '')).then(setProof)
    fetch('/patch.diff').then((r) => (r.ok ? r.text() : '')).then(setPatch)
  }, [])

  const finding = data?.discovery?.finding as Record<string, unknown> | undefined
  const verdictOk = data?.final_status === 'FIX_VERIFIED'

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="logo">ASTRA-CRS</div>
        <div className="logo-sub">Verified Repair System</div>
        <nav className="nav">
          {SCREENS.map((s) => (
            <button key={s.id} className={screen === s.id ? 'active' : ''} onClick={() => setScreen(s.id)}>
              {s.label}
            </button>
          ))}
        </nav>
      </aside>
      <main className="main">
        <header className="header">
          <h1>{SCREENS.find((s) => s.id === screen)?.label}</h1>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <span className={`badge ${verdictOk ? 'ok' : 'fail'}`}>{data?.final_status ?? 'NO DATA'}</span>
            {data?.runtime_layer?.mode === 'mock' && <span className="badge mock">DEMO / MOCK MODE</span>}
          </div>
        </header>

        {!data && (
          <div className="card">
            <p>No run data. Execute <code className="mono">make demo</code> then <code className="mono">make dashboard-export</code>.</p>
          </div>
        )}

        {data && screen === 'overview' && (
          <>
            <div className="pipeline">
              {(data.pipeline ?? []).map((s) => (
                <span key={s} className="stage done">{s}</span>
              ))}
            </div>
            <div className="grid">
              <Card title="System Status" value={data.final_status ?? '-'} sub="Pipeline verdict" />
              <Card title="Target" value="demo_vuln" sub="targets/demo_app/" />
              <Card title="Finding" value={data.finding_id ?? '-'} sub="Active finding ID" />
              <Card title="Provider" value={data.provider ?? '-'} sub={`Mode: ${data.mode}`} />
              <Card title="Elapsed" value={`${data.resources?.elapsed_seconds ?? '-'}s`} sub="Last run" />
              <Card title="Runtime" value={String(data.runtime_layer?.attached ?? false)} sub={String(data.runtime_layer?.backend ?? '')} />
            </div>
          </>
        )}

        {data && screen === 'discovery' && finding && (
          <div className="grid">
            <div className="card" style={{ gridColumn: '1 / -1' }}>
              <h3>Finding</h3>
              <pre>{JSON.stringify(finding, null, 2)}</pre>
            </div>
          </div>
        )}

        {data && screen === 'repair' && (
          <div className="grid">
            <div className="card">
              <h3>Root cause</h3>
              <pre>{String((data.discovery as { finding?: { evidence?: unknown } })?.finding ? 'See finding.json' : 'Run pipeline')}</pre>
            </div>
            <div className="card" style={{ gridColumn: '1 / -1' }}>
              <h3>Patch diff</h3>
              <pre>{patch || 'No patch.diff exported'}</pre>
            </div>
          </div>
        )}

        {data && screen === 'verification' && (
          <div className="grid">
            <Card title="Symbolic" value={String(data.symbolic_verification?.status ?? '-')} sub={String(data.symbolic_verification?.engine ?? '')} />
            <Card title="Adversarial" value={String(data.adversarial?.status ?? '-')} sub={`${data.adversarial?.attacks_executed ?? 0} attacks`} />
            <Card title="Regression" value={String(data.regression?.status ?? '-')} sub={`${data.regression?.passed ?? 0}/${data.regression?.mandatory_tests ?? 0} tests`} />
            <div className="card" style={{ gridColumn: '1 / -1' }}>
              <h3>Details</h3>
              <pre>{JSON.stringify({ symbolic: data.symbolic_verification, adversarial: data.adversarial, regression: data.regression }, null, 2)}</pre>
            </div>
          </div>
        )}

        {data && screen === 'runtime' && (
          <div className="grid">
            <Card title="eBPF Status" value={String(data.runtime_layer?.ebpf_kernel_support ?? false)} sub="Kernel BPF compile target" />
            <Card title="Attached" value={String(data.runtime_layer?.attached ?? false)} sub={String(data.runtime_layer?.mode ?? '')} />
            <div className="card" style={{ gridColumn: '1 / -1' }}>
              <h3>Events</h3>
              <pre>{JSON.stringify(data.runtime_layer?.events ?? [], null, 2)}</pre>
            </div>
          </div>
        )}

        {data && screen === 'evidence' && (
          <div className="card">
            <h3>Proof of Fix</h3>
            <pre>{proof || `Report directory: ${data.report_dir}`}</pre>
          </div>
        )}
      </main>
    </div>
  )
}

function Card({ title, value, sub }: { title: string; value: string; sub: string }) {
  return (
    <div className="card">
      <h3>{title}</h3>
      <div className="stat">{value}</div>
      <div className="label">{sub}</div>
    </div>
  )
}
