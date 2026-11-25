import { execFileSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";
const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default function globalSetup() {
  const root = path.resolve(__dirname, "../..");
  execFileSync(path.join(root, ".venv/bin/python"), [path.join(root, "scripts/make_synthetic_fixture.py")], { cwd: path.join(root, "backend"), stdio: "inherit" });
}
