"""Generate the PRELIMINARY deliverables (no participant data exist yet):
  reports/Preliminary_Research_Report.{pdf,docx,html}
  presentation/SMIT_Presentation.pptx
  experiment/stimuli/*.png (design diagrams)
Results, Discussion and Conclusion are marked as pending.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.reports.design_figures import generate_all  # noqa: E402
from app.reports.generate import write_report_files  # noqa: E402
from app.reports.presentation import build_presentation  # noqa: E402
from app.services.configs import load_default_config  # noqa: E402
from app.services.settings_store import DEFAULT_SETTINGS  # noqa: E402

cfg = load_default_config()
generate_all(ROOT / "experiment" / "stimuli", cfg)
files, final = write_report_files(ROOT / "reports", cfg, dict(DEFAULT_SETTINGS), None, None, None,
                                  basename="Preliminary_Research_Report")
assert not final
print("report:", [f["name"] for f in files])
print("presentation:", build_presentation(ROOT / "presentation" / "SMIT_Presentation.pptx", cfg, dict(DEFAULT_SETTINGS), None, None))
