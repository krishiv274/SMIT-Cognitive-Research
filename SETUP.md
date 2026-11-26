# SETUP

Requirements: **Python 3.11+** (tested with 3.14.2), **Node.js 20+** (tested with 26.7) and npm, a desktop browser (Chrome/Edge recommended). No paid services or API keys are needed.

## macOS

```bash
xcode-select --install          # if git/compilers are missing
brew install python node        # or use python.org / nodejs.org installers
```

```bash
git clone https://github.com/krishiv274/SMIT-Cognitive-Research.git
```

```bash
cd SMIT-Cognitive-Research && ./scripts/setup.sh
```

Edit `.env` (created from `.env.example`) and set a strong `SMIT_ADMIN_PASSWORD`, `SMIT_SECRET_KEY` and `SMIT_EMAIL_PEPPER`. Then:

```bash
./scripts/start.sh
```

Open http://127.0.0.1:8000 — participants use `/participate`, researchers use `/researcher`.

## Linux (Debian/Ubuntu)

```bash
sudo apt update && sudo apt install -y python3 python3-venv python3-pip nodejs npm sqlite3
```

Node from the distribution may be old; if `node --version` is below 20 install a current LTS from nodejs.org. Then run the same `./scripts/setup.sh` and `./scripts/start.sh` as on macOS.

## Windows 10/11

Install Python 3.11+ (python.org, tick "Add to PATH") and Node.js LTS (nodejs.org). In PowerShell:

```powershell
git clone https://github.com/krishiv274/SMIT-Cognitive-Research.git
cd SMIT-Cognitive-Research
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
powershell -ExecutionPolicy Bypass -File scripts\start.ps1
```

## Letting other computers on the same network connect

`start.sh` listens only on this computer (127.0.0.1). To allow other computers on the same Wi-Fi/LAN:

```bash
./scripts/start_network.sh
```

It binds to all network interfaces, prints the shareable link (e.g. `http://<your-ip>:8000/participate`) and refuses to run while the default researcher password is in use. Data stay on this computer. Computers on other networks cannot reach it; for that you would need an online deployment (see `docs/Security_and_Deployment.md`).

## Docker (optional)

```bash
cp .env.example .env
```

```bash
docker compose up --build -d
```

The app is then on http://127.0.0.1:8000 and data persist in the `smit-data` volume. Back up with `docker compose cp smit:/data/smit.db ./smit_backup.db`. (The Docker files are provided but were not built in the development environment because the Docker daemon was not running — see `pilot/Technical_Dry_Run_Report.md`.)

## Development mode (hot reload)

```bash
cd backend && ../.venv/bin/uvicorn app.main:app --reload --port 8000
```

```bash
cd frontend && npm run dev
```

The Vite dev server (http://localhost:5173) proxies `/api` to port 8000.

## Running the tests

```bash
./scripts/run_all_tests.sh
```

Playwright needs its browser once: `cd frontend && npx playwright install chromium`.

## Troubleshooting

| Problem | Fix |
|---|---|
| `The study is not open yet` | Lock a configuration (Researcher → Configuration → Lock). Pilot sessions work without locking. |
| Blank page at `/` | The frontend is not built: `cd frontend && npm run build`. |
| `Cannot reach the SMIT server` | The backend is not running, or another program uses port 8000 (`SMIT_PORT=8010 ./scripts/start.sh`). |
| Login fails | Check `SMIT_ADMIN_PASSWORD` in `.env`; restart the server after editing `.env`. |
| Timing warnings in pilot | Close other apps, use Chrome/Edge, plug in the laptop, disable battery saver, use the built-in display or a single monitor. |
| Python package build errors | Use Python 3.11–3.14 and upgrade pip (`.venv/bin/pip install --upgrade pip`). |
| Reset everything (deletes ALL data) | Stop the server and delete the `data/` folder. |
