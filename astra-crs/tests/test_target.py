from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from discovery.target import TargetConfig
from agent.orchestrator import run_pipeline


def test_target_config_loader(tmp_path):
    manifest = tmp_path / "astra.yaml"
    manifest.write_text("""
name: test_app
language: c
source: test.c
build: gcc test.c -o test
binary: test
entrypoint: test_func
""")
    cfg = TargetConfig.from_manifest(manifest)
    assert cfg.name == "test_app"
    assert cfg.language == "c"
    assert cfg.source_file == "test.c"
    assert cfg.binary == "test"
    assert cfg.entrypoint_function == "test_func"


def test_orchestrator_with_target_manifest():
    manifest = ROOT / "targets/demo_app/astra.yaml"
    res = run_pipeline(root=ROOT, mode="mock", provider_name="mock", clean=True, target=manifest)
    assert res["final_status"] == "FIX_VERIFIED"
