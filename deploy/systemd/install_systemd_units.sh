#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_PATH="${SCRIPT_DIR}/$(basename -- "${BASH_SOURCE[0]}")"
SERVICE_SRC="${SCRIPT_DIR}/energy-report-etl.service"
TIMER_SRC="${SCRIPT_DIR}/energy-report-etl.timer"
TARGET_DIR="/etc/systemd/system"
SERVICE_DST="${TARGET_DIR}/energy-report-etl.service"
TIMER_DST="${TARGET_DIR}/energy-report-etl.timer"
STAMP="$(date +%Y%m%d_%H%M%S)"

if [[ "${EUID}" -ne 0 ]]; then
  if command -v sudo >/dev/null 2>&1; then
    exec sudo -- "$SCRIPT_PATH" "$@"
  fi
  echo "This installer must run as root (or with sudo)." >&2
  exit 1
fi

for src in "$SERVICE_SRC" "$TIMER_SRC"; do
  if [[ ! -f "$src" ]]; then
    echo "Missing required source file: $src" >&2
    exit 1
  fi
done

backup_if_exists() {
  local dst="$1"
  if [[ -f "$dst" ]]; then
    local backup="${dst}.bak.${STAMP}"
    cp -a "$dst" "$backup"
    echo "Backed up existing unit: $backup"
  fi
}

echo "Installing sample systemd units for the recommended baseline:"
echo "  user/group      : energy-report"
echo "  project root    : /srv/energy-report"
echo "  timer schedule  : 23:00 host local time"
echo

echo "If your deployment differs from that baseline, edit the files in deploy/systemd/ before running this installer."
echo

backup_if_exists "$SERVICE_DST"
backup_if_exists "$TIMER_DST"

install -m 0644 "$SERVICE_SRC" "$SERVICE_DST"
install -m 0644 "$TIMER_SRC" "$TIMER_DST"

systemctl daemon-reload
systemctl enable --now energy-report-etl.timer

echo
echo "Installed units:"
echo "  $SERVICE_DST"
echo "  $TIMER_DST"
echo
systemctl status energy-report-etl.timer --no-pager || true
echo
systemctl list-timers energy-report-etl.timer --all || true
