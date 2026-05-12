#!/usr/bin/env bash
set -euo pipefail

SERVICE_USER="energy-report"
PROJECT_ROOT="/srv/energy-report"
OUTPUT_DIR="/srv/energy-report-output"
PRINT_STAGING_DIR=""
REPO_URL="https://github.com/trantuyen1991/ETL_EMS_REPORT.git"
DEPLOY_REF="backup-before-pdf-docs-20260426"
MYSQL_HOST=""
MYSQL_PORT="3306"
MYSQL_DATABASE=""
MYSQL_USER=""
MYSQL_PASSWORD="${MYSQL_PASSWORD:-}"
REPORT_FILENAME="energy_automatic_report"
REPORT_ANCHOR_DATE=""
WORKSHOP_NAME="ENERGY REPORT"
ENERGY_UNIT="kWh"
INSTALL_SYSTEMD=0
RESET_PROJECT=0
SKIP_SMOKE=0

usage() {
  cat <<'EOF'
Usage:
  sudo bash deploy/bootstrap_ubuntu_host.sh --mysql-host HOST --mysql-database DB --mysql-user USER [options]

Options:
  --mysql-host HOST
  --mysql-port PORT              Default: 3306
  --mysql-database DB
  --mysql-user USER
  --mysql-password PASSWORD      If omitted, the script prompts securely.
  --deploy-ref REF               Default: backup-before-pdf-docs-20260426
  --repo-url URL                 Default: https://github.com/trantuyen1991/ETL_EMS_REPORT.git
  --project-root PATH            Default: /srv/energy-report
  --output-dir PATH              Default: /srv/energy-report-output (final monthly report root)
  --print-staging-dir PATH       Default: <output-dir>/_staging
  --anchor-date YYYY-MM-DD       Optional smoke/backfill anchor. Blank for scheduled mode.
  --workshop-name NAME           Default: ENERGY REPORT
  --energy-unit UNIT             Default: kWh
  --install-systemd              Install and enable the systemd timer after smoke.
  --reset-project                Remove the existing project root before clone.
  --skip-smoke                   Configure only; do not run src.main.
  -h, --help

Example:
  sudo bash deploy/bootstrap_ubuntu_host.sh \
    --mysql-host 192.168.100.82 \
    --mysql-database ems_db \
    --mysql-user admin \
    --install-systemd

One-command remote usage:
  curl -fsSL https://raw.githubusercontent.com/trantuyen1991/ETL_EMS_REPORT/backup-before-pdf-docs-20260426/deploy/bootstrap_ubuntu_host.sh | sudo bash -s -- \
    --mysql-host 192.168.100.82 \
    --mysql-database ems_db \
    --mysql-user admin
EOF
}

log() {
  printf '\n==> %s\n' "$*"
}

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

as_service_user() {
  if command -v sudo >/dev/null 2>&1; then
    sudo -u "${SERVICE_USER}" "$@"
  else
    runuser -u "${SERVICE_USER}" -- "$@"
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mysql-host) MYSQL_HOST="${2:-}"; shift 2 ;;
    --mysql-port) MYSQL_PORT="${2:-}"; shift 2 ;;
    --mysql-database) MYSQL_DATABASE="${2:-}"; shift 2 ;;
    --mysql-user) MYSQL_USER="${2:-}"; shift 2 ;;
    --mysql-password) MYSQL_PASSWORD="${2:-}"; shift 2 ;;
    --deploy-ref) DEPLOY_REF="${2:-}"; shift 2 ;;
    --repo-url) REPO_URL="${2:-}"; shift 2 ;;
    --project-root) PROJECT_ROOT="${2:-}"; shift 2 ;;
    --output-dir) OUTPUT_DIR="${2:-}"; shift 2 ;;
    --print-staging-dir) PRINT_STAGING_DIR="${2:-}"; shift 2 ;;
    --anchor-date) REPORT_ANCHOR_DATE="${2:-}"; shift 2 ;;
    --workshop-name) WORKSHOP_NAME="${2:-}"; shift 2 ;;
    --energy-unit) ENERGY_UNIT="${2:-}"; shift 2 ;;
    --install-systemd) INSTALL_SYSTEMD=1; shift ;;
    --reset-project) RESET_PROJECT=1; shift ;;
    --skip-smoke) SKIP_SMOKE=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "Unknown argument: $1" ;;
  esac
done

[[ "${EUID}" -eq 0 ]] || die "Run this script as root, for example with sudo."
[[ -n "${MYSQL_HOST}" ]] || die "--mysql-host is required."
[[ -n "${MYSQL_DATABASE}" ]] || die "--mysql-database is required."
[[ -n "${MYSQL_USER}" ]] || die "--mysql-user is required."

if [[ -z "${MYSQL_PASSWORD}" ]]; then
  read -rsp "MySQL password for ${MYSQL_USER}: " MYSQL_PASSWORD
  printf '\n'
fi

if [[ -z "${PRINT_STAGING_DIR}" ]]; then
  PRINT_STAGING_DIR="${OUTPUT_DIR%/}/_staging"
fi

export DEBIAN_FRONTEND=noninteractive

log "Installing baseline packages"
apt update
apt install -y git python3 python3-venv python3-pip ca-certificates curl netcat-openbsd poppler-utils

log "Checking MySQL network access"
nc -vz "${MYSQL_HOST}" "${MYSQL_PORT}"

log "Installing Google Chrome .deb when needed"
if ! command -v google-chrome >/dev/null 2>&1; then
  rm -f /tmp/google-chrome.deb
  curl -L --fail -o /tmp/google-chrome.deb "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb"
  dpkg-deb --info /tmp/google-chrome.deb >/dev/null
  apt install -y /tmp/google-chrome.deb
fi
command -v google-chrome >/dev/null 2>&1 || die "google-chrome was not installed."
google-chrome --version
google-chrome --headless --disable-gpu --no-sandbox --dump-dom about:blank >/tmp/chrome-smoke.html

log "Preparing service account and project root"
if ! id "${SERVICE_USER}" >/dev/null 2>&1; then
  useradd --system --no-create-home --home-dir "${PROJECT_ROOT}" --shell /usr/sbin/nologin "${SERVICE_USER}"
fi

if [[ -e "${PROJECT_ROOT}" && "${RESET_PROJECT}" -eq 1 ]]; then
  rm -rf "${PROJECT_ROOT}"
fi

if [[ -e "${PROJECT_ROOT}/.git" ]]; then
  log "Existing checkout found at ${PROJECT_ROOT}; updating ${DEPLOY_REF}"
  git -C "${PROJECT_ROOT}" fetch --depth 1 origin "${DEPLOY_REF}"
  git -C "${PROJECT_ROOT}" checkout --force FETCH_HEAD
elif [[ -e "${PROJECT_ROOT}" && -n "$(find "${PROJECT_ROOT}" -mindepth 1 -maxdepth 1 -print -quit)" ]]; then
  die "${PROJECT_ROOT} exists and is not empty. Re-run with --reset-project on a test host if you want to remove it."
else
  mkdir -p "$(dirname "${PROJECT_ROOT}")"
  chown "${SERVICE_USER}:${SERVICE_USER}" "$(dirname "${PROJECT_ROOT}")"
  as_service_user git clone --branch "${DEPLOY_REF}" --depth 1 "${REPO_URL}" "${PROJECT_ROOT}"
fi

chown -R "${SERVICE_USER}:${SERVICE_USER}" "${PROJECT_ROOT}"

log "Creating Python virtual environment"
cd "${PROJECT_ROOT}"
as_service_user python3 -m venv venv
as_service_user ./venv/bin/pip install --upgrade pip
as_service_user ./venv/bin/pip install -r requirements.txt

log "Writing config/.env"
mkdir -p "${PROJECT_ROOT}/logs" "${OUTPUT_DIR}" "${PRINT_STAGING_DIR}"
chown -R "${SERVICE_USER}:${SERVICE_USER}" "${PROJECT_ROOT}/logs" "${OUTPUT_DIR}" "${PRINT_STAGING_DIR}"

cat > "${PROJECT_ROOT}/config/.env" <<EOF
MYSQL_HOST=${MYSQL_HOST}
MYSQL_PORT=${MYSQL_PORT}
MYSQL_DATABASE=${MYSQL_DATABASE}
MYSQL_USER=${MYSQL_USER}
MYSQL_PASSWORD=${MYSQL_PASSWORD}

OUTPUT_DIR=${OUTPUT_DIR}
PRINT_STAGING_DIR=${PRINT_STAGING_DIR}

REPORT_FILENAME=${REPORT_FILENAME}
LOG_LEVEL=INFO
WORKSHOP_NAME=${WORKSHOP_NAME}
ENERGY_UNIT=${ENERGY_UNIT}

REPORT_ANCHOR_DATE=${REPORT_ANCHOR_DATE}
EOF

chown "${SERVICE_USER}:${SERVICE_USER}" "${PROJECT_ROOT}/config/.env"
chmod 640 "${PROJECT_ROOT}/config/.env"

log "Forcing PDF browser_path to Google Chrome"
sed -i 's|^\([[:space:]]*browser_path:\).*|\1 /usr/bin/google-chrome|' "${PROJECT_ROOT}/config/app.yaml"

log "Checking required Sensor Monitoring icons"
for icon in activity snowflake wind flame droplet bell gauge thermometer alert-circle circle-check; do
  [[ -f "${PROJECT_ROOT}/src/templates/assets/icon/outline/${icon}.svg" ]] || die "Missing icon: src/templates/assets/icon/outline/${icon}.svg"
done

log "Testing Chrome as service account"
as_service_user /usr/bin/google-chrome --headless --disable-gpu --no-sandbox --dump-dom about:blank >/tmp/chrome-smoke-energy-report.html

if [[ "${SKIP_SMOKE}" -eq 0 ]]; then
  log "Running manual report smoke"
  as_service_user ./venv/bin/python -m src.main
  if [[ "${PRINT_STAGING_DIR%/}" == "${OUTPUT_DIR%/}" ]]; then
    find "${OUTPUT_DIR}" -type f | sort | tail -n 30
  else
    find "${OUTPUT_DIR}" -path "${PRINT_STAGING_DIR}" -prune -o -type f -print | sort | tail -n 30
  fi
fi

if [[ "${INSTALL_SYSTEMD}" -eq 1 ]]; then
  log "Installing systemd units"
  "${PROJECT_ROOT}/deploy/systemd/install_systemd_units.sh"
fi

cat <<EOF

Bootstrap completed.

Project root : ${PROJECT_ROOT}
Output dir   : ${OUTPUT_DIR}
Staging dir  : ${PRINT_STAGING_DIR}
Deploy ref   : ${DEPLOY_REF}

If this was a smoke test with --anchor-date, restore scheduled mode with:
  sudo sed -i 's|^REPORT_ANCHOR_DATE=.*|REPORT_ANCHOR_DATE=|' ${PROJECT_ROOT}/config/.env
EOF
