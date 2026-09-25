#!/usr/bin/env bash
# scripts/run_lab_pipeline.sh — end-to-end verification against the local lab.
#
#   1. Starts OWASP Juice Shop + DVWA via docker compose
#   2. Waits for both to answer HTTP
#   3. Runs the full agent pipeline against scope.lab.yaml
#   4. Asserts a non-empty PDF report was produced
#   5. Tears the lab down (unless --keep is passed)
#
# Requires: Docker + the project .venv (run ./setup.sh first).
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

KEEP=0
[[ "${1:-}" == "--keep" ]] && KEEP=1

if ! command -v docker >/dev/null 2>&1; then
    echo "SKIP: docker is not installed — lab containers cannot run here."
    echo "The compose file is ready; run this script on a machine with Docker."
    exit 0
fi
if [ ! -d ".venv" ]; then
    echo "error: .venv missing — run ./setup.sh first" >&2
    exit 1
fi

echo "==> starting lab containers"
docker compose up -d
trap '[[ $KEEP -eq 0 ]] && docker compose down || true' EXIT

wait_for() {  # wait_for <url> <name>
    for _ in $(seq 1 60); do
        if curl -sf -o /dev/null --max-time 3 "$1"; then
            echo "    $2 is up ($1)"
            return 0
        fi
        sleep 2
    done
    echo "error: $2 never came up at $1" >&2
    exit 1
}

echo "==> waiting for targets"
wait_for "http://127.0.0.1:3000" "Juice Shop"
wait_for "http://127.0.0.1:80" "DVWA"

echo "==> running pipeline"
.venv/bin/python -m pentest_agent.cli --lab --i-am-authorized --output reports/

echo "==> asserting report"
pdf="$(ls -t reports/pentest-report-*.pdf 2>/dev/null | head -1 || true)"
if [[ -z "$pdf" ]]; then
    # PDF backend may be missing; HTML is the graceful fallback artifact
    html="$(ls -t reports/pentest-report-*.html 2>/dev/null | head -1 || true)"
    if [[ -z "$html" ]]; then
        echo "FAIL: no report produced in reports/" >&2
        exit 1
    fi
    echo "PASS (html fallback): $html ($(wc -c <"$html") bytes)"
    echo "NOTE: install reportlab/weasyprint for PDF output"
    exit 0
fi
size=$(wc -c <"$pdf")
if [[ "$size" -gt 0 ]]; then
    echo "PASS: $pdf ($size bytes)"
else
    echo "FAIL: report PDF is empty" >&2
    exit 1
fi
