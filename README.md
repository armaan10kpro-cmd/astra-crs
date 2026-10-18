# ASTRA-CRS

**Autonomous Cyber-Reasoning & Verified Repair System**

A defensive cybersecurity prototype exploring how candidate code repairs can be evaluated through independent checks and inspectable evidence rather than trusting an AI-generated patch alone.

**Live dashboard/demo:** https://astra-crs.vercel.app

> **DISCOVER → LOCALIZE → REASON → REPAIR → VERIFY → ADVERSARIAL TEST → PROTECT → REPORT**

ASTRA-CRS is designed for a **controlled local lab** using a deliberately vulnerable synthetic C target. It combines deterministic security tooling—sanitizers, property checks, adversarial tests, and regression tests—with an optional LLM reasoning layer and an eBPF-related runtime-observation component.

**Core principle:** the LLM is not the final authority on patch correctness. The configured verification stages and deterministic judge decide whether a candidate is reported as `FIX_VERIFIED` or `REJECTED`.

## What it does

1. Builds a deliberately vulnerable synthetic C target.
2. Discovers memory-safety flaws using sanitizer-guided fuzzing, with a deterministic fallback.
3. Localizes a likely root cause from diagnostic evidence.
4. Proposes candidate patches through Mock, Local, or API model providers.
5. Tests a candidate in an isolated workspace using compilation, property checks, adversarial checks, and regression tests.
6. Aggregates configured check results into `FIX_VERIFIED` or `REJECTED`.
7. Generates evidence reports under `reports/<finding_id>/`.
8. Demonstrates runtime observation through eBPF-related code or clearly labelled mock/dry-run modes.

## Quick start

**Requirements:** Linux or WSL, Python 3.10+, and Clang with AddressSanitizer/UndefinedBehaviorSanitizer support. Optional features may require Z3, Node.js/npm, or an eBPF toolchain.

Clone the repository and set up the Python environment:

```bash
git clone https://github.com/armaan10kpro-cmd/astra-crs.git
cd astra-crs

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python3 scripts/check_env.py
make build
```

Run the demo:

```bash
make demo
```

The demo writes run output and evidence reports under `reports/`. The longer walkthrough is in [docs/DEMO.md](docs/DEMO.md).

Run tests:

```bash
make test
```

## Dashboard

After running the demo and exporting its dashboard data:

```bash
make dashboard-export
cd dashboard
npm install
npm run dev
```

When the development server starts successfully, open http://localhost:5173.

## Architecture

| Component | Role |
|---|---|
| Discovery | Finds and records the controlled demo issue |
| Reasoning | Creates a structured candidate patch using the selected model provider |
| Patch workspace | Applies and compiles the candidate in an isolated workspace |
| Verification | Runs configured property, adversarial, and regression checks |
| Patch judge | Aggregates check results into a reported verdict |
| Evidence reports | Stores artifacts for inspecting the decision |
| Runtime layer | Demonstrates observation/policy signalling, with mock modes clearly labelled |
| Dashboard | Presents pipeline progress, results, and evidence |

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the module-level design.

## Verification philosophy

- The model proposes a repair; it does not independently certify that repair.
- Failed repair attempts are retained within the bounded repair loop.
- The symbolic check may use Z3 when installed; an arithmetic fallback is not a universal mathematical proof.
- Adversarial and regression checks are scoped to the implemented synthetic demonstration.
- A reported `FIX_VERIFIED` result means the configured checks passed for this controlled case; it is not a guarantee that arbitrary software is secure.

More detail: [docs/VERIFICATION.md](docs/VERIFICATION.md).

## Runtime modes and limitations

- The demo target is synthetic. ASTRA-CRS is not intended to scan external systems.
- The demo patcher handles the controlled buffer-overflow pattern; it should not be treated as a general-purpose repair system for all vulnerabilities.
- AFL++ is used only when available; otherwise the deterministic fuzz fallback is used.
- Real eBPF observation requires a compatible Linux environment and supporting tools. Mock/dry-run modes are demonstrations, not kernel enforcement.
- The runtime layer is for observation/policy signalling; it does not perform arbitrary live-binary rewriting.

See [docs/EBPF.md](docs/EBPF.md) and [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Demo guide](docs/DEMO.md)
- [Verification philosophy](docs/VERIFICATION.md)
- [eBPF runtime notes](docs/EBPF.md)
- [eBPF setup notes](docs/EBPF_SETUP.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Pitch facts and supported claims](docs/PITCH_FACTS.md)
- [Initial build assessment](docs/BUILD_STATUS.md)
- [Upgrade status and roadmap](docs/UPGRADE_STATUS.md)

## Safety boundary

Use ASTRA-CRS only in its controlled synthetic lab or in other environments for which you have explicit authorization. This project is a defensive engineering prototype, not a production security guarantee.
