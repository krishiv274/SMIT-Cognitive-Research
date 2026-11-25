"""Create pilot/Human_Pilot_Testing_Checklist.xlsx (blank; to be completed by the research team)."""
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).resolve().parents[1]
HEAD = PatternFill("solid", fgColor="1F3A93")
wb = Workbook()


def sheet(title, headers, rows, widths):
    ws = wb.create_sheet(title)
    for j, h in enumerate(headers, 1):
        c = ws.cell(row=1, column=j, value=h)
        c.fill, c.font = HEAD, Font(bold=True, color="FFFFFF")
        c.alignment = Alignment(wrap_text=True, vertical="center")
    for i, r in enumerate(rows, 2):
        for j, v in enumerate(r, 1):
            ws.cell(row=i, column=j, value=v).alignment = Alignment(wrap_text=True, vertical="top")
    for j, w in enumerate(widths, 1):
        ws.column_dimensions[chr(64 + j)].width = w
    ws.freeze_panes = "A2"
    return ws


wb.remove(wb.active)
intro = wb.create_sheet("README")
for i, line in enumerate([
    "HUMAN PILOT-TESTING CHECKLIST — SMIT",
    "Complete this workbook yourselves during human pilot testing (3–5 volunteers who will NOT take part in the main study).",
    "It is intentionally blank: never enter invented observations. Automated software tests are documented separately in Technical_Dry_Run_Report.md and are NOT pilot testing.",
    "Protocol: experiment/documentation/Pilot_Testing_Protocol.md. Record summary observations in the dashboard (Settings → Pilot observations) so they appear in the report.",
], 1):
    intro.cell(row=i, column=1, value=line).font = Font(bold=(i == 1), size=14 if i == 1 else 11)
intro.column_dimensions["A"].width = 150

items = [
    ("Before", "Same computer, monitor, wired keyboard and room as planned for the main study"),
    ("Before", "SMIT_ADMIN_PASSWORD and SMIT_SECRET_KEY set in .env (not the defaults)"),
    ("Before", "Settings page completed (university, contacts, ethics statement, apparatus)"),
    ("Before", "Browser: latest Chrome/Edge; notifications off; other applications closed"),
    ("Before", "Display at native resolution; refresh rate noted"),
    ("Before", "Draft configuration selected in Pilot mode"),
    ("Before", "Volunteer is an adult, will not take part in the main study, and gave consent"),
    ("During", "Volunteer understood consent and registration screens without help"),
    ("During", "Volunteer could explain the task rules back after the instructions"),
    ("During", "Practice feedback was understood; note whether practice was repeated"),
    ("During", "Full-screen mode worked and stayed active"),
    ("During", "No visible flicker, lag or stimulus distortion"),
    ("During", "Break screens and block instructions understood"),
    ("During", "Total duration (minutes) recorded"),
    ("After", "Completion screen confirmed that all trials were saved"),
    ("After", "Pilot session inspected in dashboard: timing flags, measured vs planned durations"),
    ("After", "Control-condition accuracy within ≈ 70–92 %"),
    ("After", "Interference conditions clearly above chance (50 %)"),
    ("After", "Secondary-task accuracy ≥ 85 % and similar for arithmetic vs symmetry"),
    ("After", "Recognition timeouts < 10 %"),
    ("After", "Debrief questions asked (sheet Debrief)"),
    ("After", "Any parameter change documented (sheet Calibration_Decisions) and re-piloted"),
    ("Final", "Configuration locked with justification; version ID recorded"),
    ("Final", "Pilot observations entered in dashboard Settings"),
]
ws = sheet("Checklist", ["Phase", "Item", "Pilot 1", "Pilot 2", "Pilot 3", "Pilot 4", "Pilot 5", "Notes"],
           [[p, it, None, None, None, None, None, None] for p, it in items], [10, 70, 9, 9, 9, 9, 9, 40])
dv = DataValidation(type="list", formula1='"Yes,No,N/A"', allow_blank=True)
dv.add("C2:G60")
ws.add_data_validation(dv)

sheet("Pilot_Log", ["Pilot ID (from dashboard)", "Date", "Configuration version", "Refresh rate (Hz)", "Control accuracy",
                    "Numerical accuracy", "Visual accuracy", "Arithmetic task accuracy", "Symmetry task accuracy",
                    "Recognition timeouts (%)", "Timing flags (warning/invalid)", "Duration (min)", "Practice repeats", "Observer notes"],
      [], [16, 12, 22, 12, 12, 12, 12, 14, 14, 14, 18, 11, 11, 50])
qs = ["Were the instructions clear? What was confusing?", "Did you understand that only the blue pattern had to be remembered?",
      "How difficult were the equations? (1 = very easy … 5 = very hard)", "How difficult were the symmetry judgements? (1–5)",
      "How difficult was remembering the blue pattern in each block? (1–5)", "Was the 2-second response window long enough?",
      "Did you use any strategy (e.g. verbal labels, shapes)?", "Did you feel tired or lose concentration? When?",
      "Was anything on screen distracting, flickering or delayed?", "Any other comments?"]
sheet("Debrief", ["Question", "Pilot 1", "Pilot 2", "Pilot 3", "Pilot 4", "Pilot 5"], [[q] + [None] * 5 for q in qs], [60, 30, 30, 30, 30, 30])
sheet("Calibration_Decisions", ["Date", "Parameter", "Old value", "New value", "Evidence from pilot (observed, not assumed)", "New config version", "Decided by"],
      [], [12, 26, 12, 12, 60, 22, 16])
out = ROOT / "pilot" / "Human_Pilot_Testing_Checklist.xlsx"
wb.save(out)
print(out)
