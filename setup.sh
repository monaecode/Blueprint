#!/usr/bin/env bash
# setup.sh — one-shot environment setup for the pentest-report-agent MVP.
#
# Installs:
#   1. Python virtualenv (.venv) + Python dependencies from requirements.txt
#   2. External scanner binaries: nmap, nuclei, subfinder (checked, with
#      install guidance if missing — these need sudo / network access)
#
# Usage:
#   ./setup.sh
#   source .venv/bin/activate
#   python -m pentest_agent.cli --help
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "==> [1/3] Python virtual environment"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "    created .venv"
else
    echo "    .venv already exists"
fi
.venv/bin/pip install --upgrade pip -q
.venv/bin/pip install -r requirements.txt
echo "    python dependencies installed"

echo "==> [2/3] External scanner binaries (graceful-degradation check)"
missing=0
for bin in nmap nuclei subfinder; do
    if command -v "$bin" >/dev/null 2>&1; then
        echo "    OK: $bin ($("$bin" --version 2>/dev/null | head -1 || echo present))"
    else
        echo "    MISSING: $bin"
        missing=1
    fi
done

if [ "$missing" -eq 1 ]; then
    cat <<'EOF'

    Some scanner binaries are missing. The agent degrades gracefully —
    recon/vulnscan steps will skip with a clear warning instead of crashing —
    but for full functionality install them:

      nmap:      sudo apt install nmap            (or: brew install nmap)
      nuclei:    https://github.com/projectdiscovery/nuclei#install
                 go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
      subfinder: https://github.com/projectdiscovery/subfinder#install
                 go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest

    After installing, run:  nuclei -update-templates
EOF
else
    echo "    all scanner binaries present"
fi

echo "==> [3/3] Smoke checks"
.venv/bin/python -m py_compile pentest_agent/*.py && echo "    py_compile OK"
.venv/bin/python -m pytest --collect-only -q 2>&1 | tail -2

cat <<'EOF'

Setup complete. Next steps:
  source .venv/bin/activate
  # Lab demo (requires Docker):
  ./scripts/run_lab_pipeline.sh
  # Manual run:
  python -m pentest_agent.cli --scope scope.lab.yaml --i-am-authorized --output reports/
EOF
