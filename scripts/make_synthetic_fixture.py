"""Write a SYNTHETIC workbook for automated E2E tests (never for research use)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from tests.fixtures.synthetic import write_synthetic_workbook  # noqa: E402

out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "tests" / "artifacts" / "SYNTHETIC_e2e.xlsx"
out.parent.mkdir(parents=True, exist_ok=True)
print(write_synthetic_workbook(out, n=24, effect={"A": 0.85, "B": 0.8, "C": 0.72}))
