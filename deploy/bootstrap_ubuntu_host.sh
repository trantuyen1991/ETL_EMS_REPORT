#!/usr/bin/env bash
set -euo pipefail

SERVICE_USER="energy-report"
PROJECT_ROOT="/srv/energy-report"
OUTPUT_DIR="/srv/energy-report-output"
PRINT_STAGING_DIR=""
REPO_URL="https://github.com/trantuyen1991/ETL_EMS_REPORT.git"
DEPLOY_REF="deploy/stable"
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
INTERACTIVE=0

ARG_MYSQL_HOST=0
ARG_MYSQL_PORT=0
ARG_MYSQL_DATABASE=0
ARG_MYSQL_USER=0
ARG_MYSQL_PASSWORD=0
ARG_PROJECT_ROOT=0
ARG_OUTPUT_DIR=0
ARG_PRINT_STAGING_DIR=0
ARG_ANCHOR_DATE=0
ARG_INSTALL_SYSTEMD=0
ARG_SKIP_SMOKE=0

usage() {
  cat <<'EOF'
Usage:
  sudo bash deploy/bootstrap_ubuntu_host.sh --mysql-host HOST --mysql-database DB --mysql-user USER [options]
  sudo bash deploy/bootstrap_ubuntu_host.sh --interactive [options]

Options:
  --interactive                  Prompt for missing operator-facing values via TTY.
  --mysql-host HOST
  --mysql-port PORT              Default: 3306
  --mysql-database DB
  --mysql-user USER
  --mysql-password PASSWORD      If omitted, the script prompts securely.
  --deploy-ref REF               Default: deploy/stable
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

Examples:
  sudo bash deploy/bootstrap_ubuntu_host.sh \
    --mysql-host 192.168.100.82 \
    --mysql-database ems_db \
    --mysql-user admin \
    --install-systemd

  sudo bash deploy/bootstrap_ubuntu_host.sh --interactive

One-command remote usage (non-interactive):
  curl -fsSL https://raw.githubusercontent.com/trantuyen1991/ETL_EMS_REPORT/deploy/stable/deploy/bootstrap_ubuntu_host.sh | sudo bash -s -- \
    --mysql-host 192.168.100.82 \
    --mysql-database ems_db \
    --mysql-user admin

Interactive recommendation:
  curl -fsSL -o bootstrap_ubuntu_host.sh https://raw.githubusercontent.com/trantuyen1991/ETL_EMS_REPORT/deploy/stable/deploy/bootstrap_ubuntu_host.sh
  chmod +x bootstrap_ubuntu_host.sh
  sudo ./bootstrap_ubuntu_host.sh --interactive
EOF
}

log() {
  printf '\n==> %s\n' "$*"
}

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

has_tty() {
  [[ -r /dev/tty && -w /dev/tty ]]
}

tty_echo() {
  if has_tty; then
    printf '%s\n' "$*" > /dev/tty
  else
    printf '%s\n' "$*"
  fi
}

as_service_user() {
  if command -v sudo >/dev/null 2>&1; then
    sudo -u "${SERVICE_USER}" "$@"
  else
    runuser -u "${SERVICE_USER}" -- "$@"
  fi
}

prompt_text() {
  local __var_name="$1"
  local label="$2"
  local default_value="${3:-}"
  local required="${4:-0}"
  local value=""

  has_tty || die "Interactive prompts require a TTY. Download the script locally or pass all required flags non-interactively."

  while true; do
    if [[ -n "${default_value}" ]]; then
      read -r -p "${label} [${default_value}]: " value < /dev/tty || die "Failed to read ${label} from TTY."
    else
      read -r -p "${label}: " value < /dev/tty || die "Failed to read ${label} from TTY."
    fi

    if [[ -z "${value}" ]]; then
      value="${default_value}"
    fi

    if [[ "${required}" -eq 1 && -z "${value}" ]]; then
      tty_echo "Value is required."
      continue
    fi

    printf -v "${__var_name}" '%s' "${value}"
    return 0
  done
}

prompt_secret() {
  local __var_name="$1"
  local label="$2"
  local default_value="${3:-}"
  local required="${4:-0}"
  local value=""
  local prompt_label="${label}: "

  has_tty || die "A TTY is required to prompt securely for ${label}. Pass --mysql-password explicitly for non-interactive runs."

  if [[ -n "${default_value}" ]]; then
    prompt_label="${label} [press Enter to keep current]: "
  fi

  while true; do
    read -r -s -p "${prompt_label}" value < /dev/tty || die "Failed to read ${label} from TTY."
    printf '\n' > /dev/tty

    if [[ -z "${value}" ]]; then
      value="${default_value}"
    fi

    if [[ "${required}" -eq 1 && -z "${value}" ]]; then
      tty_echo "Value is required."
      continue
    fi

    printf -v "${__var_name}" '%s' "${value}"
    return 0
  done
}

prompt_yes_no() {
  local __var_name="$1"
  local label="$2"
  local default_value="$3"
  local hint="y/N"
  local value=""

  has_tty || die "Interactive yes/no prompts require a TTY."

  if [[ "${default_value}" -eq 1 ]]; then
    hint="Y/n"
  fi

  while true; do
    read -r -p "${label} [${hint}]: " value < /dev/tty || die "Failed to read ${label} from TTY."
    value="${value,,}"

    case "${value}" in
      "")
        printf -v "${__var_name}" '%s' "${default_value}"
        return 0
        ;;
      y|yes)
        printf -v "${__var_name}" '%s' 1
        return 0
        ;;
      n|no)
        printf -v "${__var_name}" '%s' 0
        return 0
        ;;
      *)
        tty_echo "Please answer yes or no."
        ;;
    esac
  done
}

suggest_interactive_output_dir() {
  if [[ -n "${SUDO_USER:-}" && "${SUDO_USER}" != "root" && -d "/home/${SUDO_USER}" ]]; then
    printf '/home/%s/Reports' "${SUDO_USER}"
  else
    printf '%s' "${OUTPUT_DIR}"
  fi
}

validate_configuration() {
  [[ "${EUID}" -eq 0 ]] || die "Run this script as root, for example with sudo."
  [[ -n "${MYSQL_HOST}" ]] || die "--mysql-host is required."
  [[ -n "${MYSQL_DATABASE}" ]] || die "--mysql-database is required."
  [[ -n "${MYSQL_USER}" ]] || die "--mysql-user is required."

  if [[ -z "${PRINT_STAGING_DIR}" ]]; then
    PRINT_STAGING_DIR="${OUTPUT_DIR%/}/_staging"
  fi

  if [[ -z "${MYSQL_PASSWORD}" ]]; then
    prompt_secret MYSQL_PASSWORD "MySQL password for ${MYSQL_USER}" "" 1
  fi

  if [[ "${INSTALL_SYSTEMD}" -eq 1 && -n "${REPORT_ANCHOR_DATE}" ]]; then
    die "--install-systemd cannot be combined with a pinned REPORT_ANCHOR_DATE. Restore scheduled mode first, then enable the timer."
  fi
}

confirm_interactive_summary() {
  local proceed=1

  [[ "${INTERACTIVE}" -eq 1 ]] || return 0

  tty_echo ""
  tty_echo "Bootstrap summary"
  tty_echo "  MySQL host         : ${MYSQL_HOST}"
  tty_echo "  MySQL port         : ${MYSQL_PORT}"
  tty_echo "  MySQL database     : ${MYSQL_DATABASE}"
  tty_echo "  MySQL user         : ${MYSQL_USER}"
  tty_echo "  MySQL password     : <hidden>"
  tty_echo "  Project root       : ${PROJECT_ROOT}"
  tty_echo "  Output dir         : ${OUTPUT_DIR}"
  tty_echo "  Staging dir        : ${PRINT_STAGING_DIR}"
  tty_echo "  Deploy ref         : ${DEPLOY_REF}"
  tty_echo "  Anchor date        : ${REPORT_ANCHOR_DATE:-<blank>}"
  tty_echo "  Run smoke          : $([[ "${SKIP_SMOKE}" -eq 0 ]] && printf 'yes' || printf 'no')"
  tty_echo "  Install systemd    : $([[ "${INSTALL_SYSTEMD}" -eq 1 ]] && printf 'yes' || printf 'no')"
  tty_echo "  Reset project      : $([[ "${RESET_PROJECT}" -eq 1 ]] && printf 'yes' || printf 'no')"
  if [[ "${OUTPUT_DIR}" == /home/* || "${PRINT_STAGING_DIR}" == /home/* ]]; then
    tty_echo "  Home-path ACL fix  : will be applied automatically"
  fi

  prompt_yes_no proceed "Proceed with these settings?" 1
  [[ "${proceed}" -eq 1 ]] || die "Bootstrap cancelled by operator."
}

configure_interactively() {
  local suggested_output_dir="${OUTPUT_DIR}"
  local run_smoke=1
  local install_systemd_now="${INSTALL_SYSTEMD}"

  [[ "${INTERACTIVE}" -eq 1 ]] || return 0
  has_tty || die "--interactive requires an attached TTY. Download the script locally or run it from a normal terminal."

  tty_echo ""
  tty_echo "Interactive bootstrap mode"
  tty_echo "Press Enter to keep the value shown in brackets."

  [[ "${ARG_MYSQL_HOST}" -eq 1 ]] || prompt_text MYSQL_HOST "MySQL host" "${MYSQL_HOST}" 1
  [[ "${ARG_MYSQL_PORT}" -eq 1 ]] || prompt_text MYSQL_PORT "MySQL port" "${MYSQL_PORT}" 1
  [[ "${ARG_MYSQL_DATABASE}" -eq 1 ]] || prompt_text MYSQL_DATABASE "MySQL database" "${MYSQL_DATABASE}" 1
  [[ "${ARG_MYSQL_USER}" -eq 1 ]] || prompt_text MYSQL_USER "MySQL user" "${MYSQL_USER}" 1

  if [[ "${ARG_MYSQL_PASSWORD}" -eq 0 && -z "${MYSQL_PASSWORD}" ]]; then
    prompt_secret MYSQL_PASSWORD "MySQL password for ${MYSQL_USER}" "" 1
  fi

  [[ "${ARG_PROJECT_ROOT}" -eq 1 ]] || prompt_text PROJECT_ROOT "Project root" "${PROJECT_ROOT}" 1

  if [[ "${ARG_OUTPUT_DIR}" -eq 0 ]]; then
    suggested_output_dir="$(suggest_interactive_output_dir)"
    prompt_text OUTPUT_DIR "Final output dir" "${suggested_output_dir}" 1
  fi

  if [[ "${ARG_PRINT_STAGING_DIR}" -eq 0 ]]; then
    prompt_text PRINT_STAGING_DIR "Print staging dir" "${OUTPUT_DIR%/}/_staging" 1
  fi

  [[ "${ARG_ANCHOR_DATE}" -eq 1 ]] || prompt_text REPORT_ANCHOR_DATE "Smoke anchor date (blank for scheduled mode)" "${REPORT_ANCHOR_DATE}" 0

  if [[ "${ARG_SKIP_SMOKE}" -eq 0 ]]; then
    prompt_yes_no run_smoke "Run smoke now after bootstrap?" 1
    if [[ "${run_smoke}" -eq 1 ]]; then
      SKIP_SMOKE=0
    else
      SKIP_SMOKE=1
    fi
  fi

  if [[ "${ARG_INSTALL_SYSTEMD}" -eq 0 ]]; then
    prompt_yes_no install_systemd_now "Install and enable systemd timer now?" 0
    INSTALL_SYSTEMD="${install_systemd_now}"
  fi
}

grant_service_acl_for_home_path() {
  local target_dir="$1"
  local owner_user="${target_dir#/home/}"
  owner_user="${owner_user%%/*}"
  local owner_home="/home/${owner_user}"
  local traverse_path

  [[ -n "${owner_user}" && "${owner_user}" != "${target_dir}" ]] || die "Cannot infer home owner from path: ${target_dir}"
  id "${owner_user}" >/dev/null 2>&1 || die "Home output owner does not exist: ${owner_user}"
  [[ -d "${owner_home}" ]] || die "Home directory does not exist: ${owner_home}"
  command -v setfacl >/dev/null 2>&1 || die "setfacl is required when output paths live under /home. Install package: acl"

  mkdir -p "${target_dir}"
  chown -R "${owner_user}:${owner_user}" "${target_dir}"

  traverse_path="$(dirname "${target_dir}")"
  while [[ "${traverse_path}" == /home/* ]]; do
    setfacl -m "u:${SERVICE_USER}:--x" "${traverse_path}"
    [[ "${traverse_path}" == "${owner_home}" ]] && break
    traverse_path="$(dirname "${traverse_path}")"
  done

  setfacl -R -m "u:${SERVICE_USER}:rwx" "${target_dir}"
  setfacl -R -d -m "u:${SERVICE_USER}:rwx" "${target_dir}"
}

prepare_runtime_dir() {
  local target_dir="$1"
  if [[ "${target_dir}" == /home/* ]]; then
    grant_service_acl_for_home_path "${target_dir}"
  else
    mkdir -p "${target_dir}"
    chown -R "${SERVICE_USER}:${SERVICE_USER}" "${target_dir}"
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --interactive) INTERACTIVE=1; shift ;;
    --mysql-host) MYSQL_HOST="${2:-}"; ARG_MYSQL_HOST=1; shift 2 ;;
    --mysql-port) MYSQL_PORT="${2:-}"; ARG_MYSQL_PORT=1; shift 2 ;;
    --mysql-database) MYSQL_DATABASE="${2:-}"; ARG_MYSQL_DATABASE=1; shift 2 ;;
    --mysql-user) MYSQL_USER="${2:-}"; ARG_MYSQL_USER=1; shift 2 ;;
    --mysql-password) MYSQL_PASSWORD="${2:-}"; ARG_MYSQL_PASSWORD=1; shift 2 ;;
    --deploy-ref) DEPLOY_REF="${2:-}"; shift 2 ;;
    --repo-url) REPO_URL="${2:-}"; shift 2 ;;
    --project-root) PROJECT_ROOT="${2:-}"; ARG_PROJECT_ROOT=1; shift 2 ;;
    --output-dir) OUTPUT_DIR="${2:-}"; ARG_OUTPUT_DIR=1; shift 2 ;;
    --print-staging-dir) PRINT_STAGING_DIR="${2:-}"; ARG_PRINT_STAGING_DIR=1; shift 2 ;;
    --anchor-date) REPORT_ANCHOR_DATE="${2:-}"; ARG_ANCHOR_DATE=1; shift 2 ;;
    --workshop-name) WORKSHOP_NAME="${2:-}"; shift 2 ;;
    --energy-unit) ENERGY_UNIT="${2:-}"; shift 2 ;;
    --install-systemd) INSTALL_SYSTEMD=1; ARG_INSTALL_SYSTEMD=1; shift ;;
    --reset-project) RESET_PROJECT=1; shift ;;
    --skip-smoke) SKIP_SMOKE=1; ARG_SKIP_SMOKE=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "Unknown argument: $1" ;;
  esac
done

[[ "${EUID}" -eq 0 ]] || die "Run this script as root, for example with sudo."

configure_interactively
validate_configuration
confirm_interactive_summary

export DEBIAN_FRONTEND=noninteractive

log "Installing baseline packages"
apt update
apt install -y git python3 python3-venv python3-pip ca-certificates curl netcat-openbsd poppler-utils acl

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
mkdir -p "${PROJECT_ROOT}/logs"
chown -R "${SERVICE_USER}:${SERVICE_USER}" "${PROJECT_ROOT}/logs"
prepare_runtime_dir "${OUTPUT_DIR}"
prepare_runtime_dir "${PRINT_STAGING_DIR}"

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

If OUTPUT_DIR or PRINT_STAGING_DIR live under /home/<user>, bootstrap has already applied ACL so ${SERVICE_USER} can write there.
EOF
