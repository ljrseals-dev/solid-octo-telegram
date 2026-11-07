import glob, json
from pathlib import Path

import jsonschema
from lfs.core.preset import example_local_first_signal
from lfs.semantic.bank_loader import load_all
from lfs.semantic.prompt_compiler_v2 import compile_variants

ROOT = Path(__file__).resolve().parents[1]


def test_banks_validate_against_schema():
    schema = json.loads((ROOT / "schemas" / "bank.schema.json").read_text())
    files = glob.glob(str(ROOT / "banks" / "*.json"))
    assert files
    for f in files:
        jsonschema.validate(json.loads(Path(f).read_text()), schema)


def test_bank_prompts_deterministic():
    banks = load_all(ROOT / "banks")
    p = example_local_first_signal()
    a = compile_variants(p, banks, n_variants=3, global_seed=7)
    b = compile_variants(p, banks, n_variants=3, global_seed=7)
    c = compile_variants(p, banks, n_variants=3, global_seed=8)
    assert a == b
    assert a != c
    assert a[0]["banks_hash"] == banks.banks_hash
