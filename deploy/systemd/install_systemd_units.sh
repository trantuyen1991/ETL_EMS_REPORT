#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_PATH="${SCRIPT_DIR}/$(basename -- "${BASH_SOURCE[0]}")"
SERVICE_SRC="${SCRIPT_DIR}/energy-report-etl.service"
TIMER_SRC="${SCRIPT_DIR}/energy-report-etl.timer"
WEB_SERVICE_SRC="${SCRIPT_DIR}/energy-report-web.service"
TARGET_DIR="/etc/systemd/system"
SERVICE_DST="${TARGET_DIR}/energy-report-etl.service"
TIMER_DST="${TARGET_DIR}/energy-report-etl.timer"
WEB_SERVICE_DST="${TARGET_DIR}/energy-report-web.service"
STAMP="$(date +%Y%m%d_%H%M%S)"
SERVICE_USER="energy-report"
PROJECT_ROOT="/srv/energy-report"
WEB_HOST="0.0.0.0"
WEB_PORT="8000"
INSTALL_ETL=1
INSTALL_WEB=0

usage() {
  cat <<'EOF'
Usage:
  sudo ./deploy/systemd/install_systemd_units.sh [options]

Options:
  --with-web                   Install/start the optional Web UI service in addition to ETL timer.
  --web-only                   Install/start only the Web UI service.
  --service-user USER          Default: energy-report
  --project-root PATH          Default: /srv/energy-report
  --web-host HOST              Default: 0.0.0.0
  --web-port PORT              Default: 8000
  -h, --help
EOF
}

die() {
  echo "ERROR: $*" >&2
  exit 1
}

sed_escape() {
  printf '%s' "$1" | sed -e 's/[\\/&]/\\&/g'
}

if [[ "${EUID}" -ne 0 ]]; then
  if command -v sudo >/dev/null 2>&1; then
    exec sudo -- "$SCRIPT_PATH" "$@"
  fi
  echo "This installer must run as root (or with sudo)." >&2
  exit 1
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --with-web) INSTALL_WEB=1; shift ;;
    --web-only) INSTALL_ETL=0; INSTALL_WEB=1; shift ;;
    --service-user) SERVICE_USER="${2:-}"; shift 2 ;;
    --project-root) PROJECT_ROOT="${2:-}"; shift 2 ;;
    --web-host) WEB_HOST="${2:-}"; shift 2 ;;
    --web-port) WEB_PORT="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) die "Unknown argument: $1" ;;
  esac
done

[[ "${INSTALL_ETL}" -eq 1 || "${INSTALL_WEB}" -eq 1 ]] || die "Nothing to install."
[[ -n "${SERVICE_USER}" ]] || die "--service-user cannot be blank."
[[ -n "${PROJECT_ROOT}" ]] || die "--project-root cannot be blank."
[[ -n "${WEB_HOST}" ]] || die "--web-host cannot be blank."
[[ "${WEB_PORT}" =~ ^[0-9]+$ ]] || die "--web-port must be numeric."

if [[ "${INSTALL_ETL}" -eq 1 ]]; then
  for src in "$SERVICE_SRC" "$TIMER_SRC"; do
    if [[ ! -f "$src" ]]; then
      echo "Missing required source file: $src" >&2
      exit 1
    fi
  done
fi

if [[ "${INSTALL_WEB}" -eq 1 && ! -f "$WEB_SERVICE_SRC" ]]; then
  echo "Missing required source file: $WEB_SERVICE_SRC" >&2
  exit 1
fi

backup_if_exists() {
  local dst="$1"
  if [[ -f "$dst" ]]; then
    local backup="${dst}.bak.${STAMP}"
    cp -a "$dst" "$backup"
    echo "Backed up existing unit: $backup"
  fi
}

render_and_install() {
  local src="$1"
  local dst="$2"
  local tmp
  tmp="$(mktemp)"

  sed \
    -e "s|__SERVICE_USER__|$(sed_escape "${SERVICE_USER}")|g" \
    -e "s|__PROJECT_ROOT__|$(sed_escape "${PROJECT_ROOT}")|g" \
    -e "s|__WEB_HOST__|$(sed_escape "${WEB_HOST}")|g" \
    -e "s|__WEB_PORT__|$(sed_escape "${WEB_PORT}")|g" \
    "$src" > "$tmp"

  install -m 0644 "$tmp" "$dst"
  rm -f "$tmp"
}

echo "Installing sample systemd units for the recommended baseline:"
echo "  user/group      : ${SERVICE_USER}"
echo "  project root    : ${PROJECT_ROOT}"
if [[ "${INSTALL_ETL}" -eq 1 ]]; then
  echo "  timer schedule  : 23:00 host local time"
fi
if [[ "${INSTALL_WEB}" -eq 1 ]]; then
  echo "  web bind        : ${WEB_HOST}:${WEB_PORT}"
fi
echo

echo "This installer renders the repo unit templates with the values shown above."
echo

if [[ "${INSTALL_ETL}" -eq 1 ]]; then
  backup_if_exists "$SERVICE_DST"
  backup_if_exists "$TIMER_DST"
  render_and_install "$SERVICE_SRC" "$SERVICE_DST"
  install -m 0644 "$TIMER_SRC" "$TIMER_DST"
fi

if [[ "${INSTALL_WEB}" -eq 1 ]]; then
  backup_if_exists "$WEB_SERVICE_DST"
  render_and_install "$WEB_SERVICE_SRC" "$WEB_SERVICE_DST"
fi

systemctl daemon-reload

if [[ "${INSTALL_ETL}" -eq 1 ]]; then
  systemctl enable --now energy-report-etl.timer
fi

if [[ "${INSTALL_WEB}" -eq 1 ]]; then
  systemctl enable --now energy-report-web.service
fi

echo
echo "Installed units:"
if [[ "${INSTALL_ETL}" -eq 1 ]]; then
  echo "  $SERVICE_DST"
  echo "  $TIMER_DST"
fi
if [[ "${INSTALL_WEB}" -eq 1 ]]; then
  echo "  $WEB_SERVICE_DST"
fi

if [[ "${INSTALL_ETL}" -eq 1 ]]; then
  echo
  systemctl status energy-report-etl.timer --no-pager || true
  echo
  systemctl list-timers energy-report-etl.timer --all || true
fi

if [[ "${INSTALL_WEB}" -eq 1 ]]; then
  echo
  systemctl status energy-report-web.service --no-pager || true
fi
