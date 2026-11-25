"""Generate the blank Excel/CSV data templates in templates/ (no participant data)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.experiment.config import ExperimentConfig  # noqa: E402
from app.reports.workbook import build_collection_workbook, build_summary_template, write_csv_templates  # noqa: E402

cfg = ExperimentConfig.model_validate(json.loads((ROOT / "experiment/configuration/default_config.json").read_text()))
out = ROOT / "templates"
print(build_collection_workbook(out / "SMIT_Data_Collection_Template.xlsx", cfg))
print(build_summary_template(out / "Participant_Summary_Template.xlsx"))
for p in write_csv_templates(out):
    print(p)
