# ASTRA-CRS

**Autonomous Cyber-Reasoning & Verified Repair System**

A defensive cybersecurity prototype that explores how candidate code repairs can be tested and assessed with explicit evidence, rather than trusting an AI-generated patch on its own.

**Demo:** https://astra-crs.vercel.app  
**Repository:** https://github.com/armaan10kpro-cmd/astra-crs

> **DISCOVER → LOCALIZE → REASON → REPAIR → VERIFY → ADVERSARIAL TEST → PROTECT → REPORT**

## Why this project

AI can suggest a code fix, but a suggestion is not proof that the fix works. ASTRA-CRS separates patch generation from patch acceptance: a deterministic judge aggregates the configured checks, and the result is reported as `FIX_VERIFIED` or `REJECTED`.

The project is designed for a controlled local lab using a deliberately vulnerable synthetic C target. It is a prototype and does not claim universal vulnerability coverage or a general proof of software security.

## What it does

1. Builds and analyzes a synthetic C target in a controlled environment.
2. Uses sanitizer-guided discovery, with a deterministic fallback when optional fuzzing tools are unavailable.
3. Localizes a likely root cause from collected diagnostic evidence.
4. Produces a candidate patch through a configured Mock, Local, or API model provider.
5. Tests the candidate in an isolated workspace with compilation, explicit property checks, adversarial checks, and regression tests.
6. Uses a deterministic patch judge to accept or reject the candidate based on configured checks.
7. Writes a report bundle under `reports/<finding_id>/` so the decision can be inspected.
8. Demonstrates a runtime-observation layer through eBPF-related code or an explicitly labelled mock/dry-run mode.

## Key engineering principles

- **AI is not the final judge.** A model proposal is only a candidate; configured checks determine the reported verdict.
- **Failures remain visible.** Failed repair attempts are retained within the bounded repair loop rather than silently discarded.
- **Fallbacks are labelled.** When optional tools such as Z3, AFL++, or runtime eBPF dependencies are unavailable, the project reports the relevant fallback or mock mode.
- **Evidence is inspectable.** Reports are intended to show the finding, proposed diff, test results, and final decision.
- **Scope is deliberately limited.** The demo patcher handles the controlled vulnerability pattern; results should not be generalized to arbitrary programs.

## Run locally

### Requirements

- Linux or WSL
- Python 3.10+
- Clang with AddressSanitizer/UndefinedBehaviorSanitizer support
- Optional: Z3, AFL++, Node.js/npm, and the relevant eBPF toolchain for those modes

### Setup

```bash
git clone https://github.com/armaan10kpro-cmd/astra-crs.git
cd astra-crs

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python3 scripts/check_env.py
make build
```

### Run the demo

```bash
make demo
```

The demo writes run output and reports under `reports/`. For the longer walkthrough and expected artifacts, see [the demo guide](docs/DEMO.md).

### Run tests

```bash
make test
```

### Launch the dashboard locally

After running the demo and exporting its dashboard data:

```bash
make dashboard-export
cd dashboard
npm install
npm run dev
```

The local dashboard runs at `http://localhost:5173` when the development server starts successfully.

## Architecture

| Component | Responsibility |
|---|---|
| Discovery | Finds and records the controlled demo issue |
| Reasoning | Produces a structured candidate patch through the selected provider |
| Patch workspace | Applies and compiles the candidate in isolation |
| Verification | Runs configured property, adversarial, and regression checks |
| Patch judge | Aggregates check results into `FIX_VERIFIED` or `REJECTED` |
| Evidence reports | Stores artifacts supporting the reported decision |
| Runtime layer | Demonstrates observation/policy signalling; real eBPF operation depends on the local toolchain |
| Dashboard | Displays pipeline progress, results, and report evidence |

For the module-level design, see [Architecture](docs/ARCHITECTURE.md).

## Runtime modes and limitations

- The default demo can run with the mock reasoning provider; a live model/API is optional.
- The symbolic check may use Z3 when installed; otherwise a labelled arithmetic fallback may be used. A fallback result is **not** a universal mathematical proof.
- eBPF mock/dry-run modes are demonstrations, not kernel enforcement. Real observer operation requires a compatible environment and supporting tools.
- The runtime layer does not perform arbitrary live-binary patching.
- ASTRA-CRS is intended for a controlled defensive lab. It does not scan external systems.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Demo guide](docs/DEMO.md)
- [Verification philosophy](docs/VERIFICATION.md)
- [eBPF requirements and modes](docs/EBPF.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Demonstrable claims and limitations](docs/PITCH_FACTS.md)
- [Initial build assessment](docs/BUILD_STATUS.md)

## Safety boundary

Use the project only in its controlled synthetic lab. Do not point it at systems you do not own or have explicit authorization to test. This repository is a prototype for exploring defensive repair verification, not a production security guarantee.
