# Deployment Runbook

Use this runbook when bringing the project onto a new Ubuntu / systemd host, whether you bootstrap from the one-command flow or work step by step after cloning.

Scope:
- clone the project onto a new machine
- create a fresh Python virtual environment
- configure runtime `.env`
- run a manual smoke check
- install a `systemd` service + timer for a fixed daily schedule such as `23:00`

Assumptions:
- host OS uses `systemd`
- Python 3.12 is available
- Chrome / Chromium is available on the host for PDF export
- the host can reach the target MySQL database
- target timezone should be `Asia/Ho_Chi_Minh` unless the deployment intentionally uses another timezone

---

## 1. Recommended operator flow

For the current deployment style, use this order:

1. **B1**: fresh bootstrap + month-end smoke for `2025-05-31`
2. **B2**: change anchor to Sunday `2025-05-18` and run again
3. **B3**: reset `REPORT_ANCHOR_DATE=` back to blank scheduled mode
4. **B4**: only after B3, install or adjust the `systemd` timer
5. **B5**: use the maintenance commands later for update / reinstall / rollback

This order matters because B1 and B2 intentionally use pinned smoke anchors. The timer should only be enabled after B3 has restored blank scheduled mode.

### 1.1 One-command bootstrap option

For a fresh Ubuntu host, prefer the bootstrap script when you want to avoid manual copy/paste drift:

- script: `deploy/bootstrap_ubuntu_host.sh`
- copy/paste text source: `docs/workflows/deployment_copy_paste_commands.txt`

Copy the one-command bootstrap from the plain text file, not from the PDF. PDF readers can wrap long URLs or drop continuation lines.

Current one-command bootstrap intentionally uses the deploy branch `deploy/stable`, not the older reviewed tag `v4.3.0-dev`, because that branch currently carries newer deploy-flow fixes.

Recommended B1 command:

```bash
curl -fsSL "https://raw.githubusercontent.com/trantuyen1991/ETL_EMS_REPORT/deploy/stable/deploy/bootstrap_ubuntu_host.sh" | sudo bash -s -- --mysql-host 192.168.100.82 --mysql-database bms_db --mysql-user admin --anchor-date 2025-05-31 --reset-project
```

Important:
- B1 intentionally does **not** use `--install-systemd`
- do not enable the timer while `REPORT_ANCHOR_DATE` is still pinned for smoke testing
- install or enable the timer only after B3 has restored `REPORT_ANCHOR_DATE=`

### 1.2 Hybrid bootstrap modes

The bootstrap flow should support two operator-facing modes:

1. **Non-interactive mode**
   - best for `curl | sudo bash -s -- ...`
   - best for repeatable copy/paste, headless hosts, and automation
   - every required value should be passed by flag, or the script should fail clearly

2. **Interactive mode**
   - best for a desktop operator sitting at the target machine
   - the script should prompt only for missing values, show sensible defaults, and let the operator press Enter to keep them
   - flags should still win, so already-passed values should not be prompted again

Recommended operator rule:
- keep `curl | bash` for the one-line non-interactive bootstrap
- use a local script file for interactive runs when possible
- if the interactive path reads from TTY directly, it may still work when piped, but the local-file path is the safer operator experience

Suggested interactive entrypoint:

```bash
curl -fsSL -o bootstrap_ubuntu_host.sh "https://raw.githubusercontent.com/trantuyen1991/ETL_EMS_REPORT/deploy/stable/deploy/bootstrap_ubuntu_host.sh"
chmod +x bootstrap_ubuntu_host.sh
sudo ./bootstrap_ubuntu_host.sh --interactive
```

Interactive prompts should normally cover only operator-facing values such as:
- `MYSQL_HOST`
- `MYSQL_PORT`
- `MYSQL_DATABASE`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `PROJECT_ROOT`
- `OUTPUT_DIR`
- `PRINT_STAGING_DIR`
- `REPORT_ANCHOR_DATE`
- whether to run smoke now
- whether to install `systemd` now

The interactive flow should finish with a summary/confirmation screen before any destructive or long-running action starts.

---

## 2. Prepare the new host

Install baseline tools as needed:

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip ca-certificates curl netcat-openbsd poppler-utils
```

Browser runtime requirement:
- prefer Google Chrome `.deb` on Ubuntu hosts used for service-account / `systemd` runs
- Ubuntu `chromium` is commonly installed as a Snap package and may fail under `sudo -u energy-report` or `systemd` with a snap cgroup error
- verify with:

```bash
python3 --version
which google-chrome || which chromium || which chromium-browser
```

Recommended Chrome install path if `google-chrome` is not already present:

```bash
curl -L -o /tmp/google-chrome.deb \
  https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install -y /tmp/google-chrome.deb

which google-chrome
google-chrome --version

sudo -u "$(whoami)" google-chrome \
  --headless \
  --disable-gpu \
  --no-sandbox \
  --dump-dom about:blank >/tmp/chrome-smoke.html
```

Timezone rule:
- the scheduled ETL run uses the host timezone
- if the job must fire at `23:00` Vietnam time, confirm the host timezone first

```bash
timedatectl
```

If needed:

```bash
sudo timedatectl set-timezone Asia/Ho_Chi_Minh
```

---

## 3. Clone the project and create a fresh venv

Recommended baseline for the sample `systemd` files in this repo:
- Linux user/group: `energy-report`
- project root: `/srv/energy-report`

Reviewed release reference for older rollback or exact snapshot deploy:
- release tag: `v4.3.0-dev`
- repo URL: `https://github.com/trantuyen1991/ETL_EMS_REPORT.git`
- GitHub release page: `https://github.com/trantuyen1991/ETL_EMS_REPORT/releases/tag/v4.3.0-dev`
- release tag page: `https://github.com/trantuyen1991/ETL_EMS_REPORT/tree/v4.3.0-dev`
- release archive: `https://github.com/trantuyen1991/ETL_EMS_REPORT/archive/refs/tags/v4.3.0-dev.zip`

If the host should deploy the exact older reviewed snapshot instead of the newer deploy branch, clone the tag directly:

```bash
sudo useradd --system --no-create-home --home-dir /srv/energy-report --shell /usr/sbin/nologin energy-report || true
sudo mkdir -p /srv
sudo chown energy-report:energy-report /srv
sudo -u energy-report git clone --branch v4.3.0-dev --depth 1 \
  https://github.com/trantuyen1991/ETL_EMS_REPORT.git \
  /srv/energy-report
cd /srv/energy-report
sudo -u energy-report python3 -m venv venv
sudo -u energy-report ./venv/bin/pip install --upgrade pip
sudo -u energy-report ./venv/bin/pip install -r requirements.txt
```

Important:
- do **not** copy an old `venv/` from another machine
- always recreate the virtual environment on the new host
- `--no-create-home` is intentional; using `--create-home` creates `/srv/energy-report` before `git clone`, which makes clone fail because the destination exists and is not empty
- if you intentionally deploy a moving branch instead of the reviewed release tag, change the `git clone --branch ...` target on purpose
- if you do not use the `energy-report` service account or `/srv/energy-report` path, update the sample `systemd` files before installing them

Reset only Step 2 on a test host:

```bash
sudo bash -lc 'set -e
rm -rf /srv/energy-report
id energy-report >/dev/null 2>&1 && userdel energy-report || true
useradd --system --no-create-home --home-dir /srv/energy-report --shell /usr/sbin/nologin energy-report
mkdir -p /srv
chown energy-report:energy-report /srv
sudo -u energy-report git clone --branch v4.3.0-dev --depth 1 https://github.com/trantuyen1991/ETL_EMS_REPORT.git /srv/energy-report
cd /srv/energy-report
sudo -u energy-report python3 -m venv venv
sudo -u energy-report ./venv/bin/pip install --upgrade pip
sudo -u energy-report ./venv/bin/pip install -r requirements.txt
'
```

---

## 4. Configure `config/.env`

The application loads runtime values from:
- `config/.env`
- `config/app.yaml`

### 4.1 Operator-first copy/paste block

To avoid opening `config/.env` and editing line by line, use the block below.

What the installer must change before pasting:
- `MYSQL_HOST`
- `MYSQL_PORT`
- `MYSQL_DATABASE`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `OUTPUT_DIR` if the host should store final monthly report artifacts somewhere other than `/srv/energy-report-output`
- `PRINT_STAGING_DIR` if Chromium staging should use somewhere other than `/srv/energy-report-output/_staging`
- optionally `WORKSHOP_NAME` and `ENERGY_UNIT`

Paste-ready block:

```bash
sudo tee /srv/energy-report/config/.env >/dev/null <<'EOF'
# --- Change these values to match the target system ---
MYSQL_HOST=__FILL_DB_HOST__
MYSQL_PORT=3306
MYSQL_DATABASE=__FILL_DB_NAME__
MYSQL_USER=__FILL_DB_USER__
MYSQL_PASSWORD=__FILL_DB_PASSWORD__

# --- Change these paths only if your host uses a different storage layout ---
OUTPUT_DIR=/srv/energy-report-output
PRINT_STAGING_DIR=/srv/energy-report-output/_staging

# --- Usually keep these values as-is ---
REPORT_FILENAME=energy_automatic_report
LOG_LEVEL=INFO
WORKSHOP_NAME=ENERGY REPORT
ENERGY_UNIT=kWh

# --- Keep blank in normal scheduled production mode ---
REPORT_ANCHOR_DATE=
EOF

sudo chown energy-report:energy-report /srv/energy-report/config/.env
sudo chmod 640 /srv/energy-report/config/.env
sudo mkdir -p /srv/energy-report/logs /srv/energy-report-output /srv/energy-report-output/_staging
sudo chown -R energy-report:energy-report /srv/energy-report/logs /srv/energy-report-output /srv/energy-report-output/_staging
```

If the operator wants to keep everything on the recommended baseline, the only lines that usually need changing are the MySQL values.

### 4.2 Critical operational notes

- `OUTPUT_DIR` is now the **canonical final artifact root** for operators, with monthly folders created directly under `OUTPUT_DIR/YYYY_MM/`
- `PRINT_STAGING_DIR` is the Chromium-safe staging path and should normally be a separate subfolder such as `/srv/energy-report-output/_staging`
- after a successful run, runtime removes current-batch staging files and prunes an empty `_staging` folder
- both `OUTPUT_DIR` and `PRINT_STAGING_DIR` should point to a **non-hidden writable path**
- if either path lives under `/home/<user>/...`, `deploy/bootstrap_ubuntu_host.sh` now auto-installs `acl`, grants the `energy-report` service user traverse/write ACLs, and grants the home owner ACLs to open generated report files from the desktop
- if an operator changes those paths manually later in `config/.env`, rerun the bootstrap or apply equivalent `setfacl` commands so the service account can still write there
- do not set `PRINT_STAGING_DIR` to a personal desktop/home path such as `/home/trantuyen/Desktop/Report`; the `energy-report` service account usually cannot write there
- `REPORT_FILENAME` should stay aligned with the accepted runtime naming: `energy_automatic_report`
- `REPORT_ANCHOR_DATE` must normally be **blank** in scheduled production mode
- only set `REPORT_ANCHOR_DATE` temporarily for smoke tests or backfill-style manual runs

Why `REPORT_ANCHOR_DATE` must be blank for scheduled mode:
- if it stays pinned to a fixed date, the daily timer will keep regenerating that old anchor day instead of the current date

---

## 5. Check release asset compatibility

For release tag `v4.3.0-dev`, if rendering fails with missing `assets/icon/outline/*.svg` while loading Sensor Monitoring templates, create these compatibility links before the smoke run:

```bash
cd /srv/energy-report

sudo -u energy-report bash -lc '
set -e
cd /srv/energy-report
mkdir -p src/templates/assets/icon/outline
cd src/templates/assets/icon/outline

ln -sf ../sensor/capacity.svg snowflake.svg
ln -sf ../sensor/flow.svg wind.svg
ln -sf ../steam.svg flame.svg
ln -sf ../water.svg droplet.svg
ln -sf ../energy.svg activity.svg
ln -sf ../sensor/power.svg bell.svg
ln -sf ../sensor/pressure.svg gauge.svg
ln -sf ../sensor/temperature.svg thermometer.svg
ln -sf ../sensor/power.svg alert-circle.svg
ln -sf ../sensor/power.svg circle-check.svg
'
```

This is a deployment workaround for the reviewed tag and should be replaced by a source release fix in the next release.

---

## 6. Run B2 and B3 before enabling schedule

If B1 already finished successfully with anchor `2025-05-31`, the next recommended operator flow is:

### B2. Change anchor to Sunday and run again

```bash
sudo sed -i 's|^REPORT_ANCHOR_DATE=.*|REPORT_ANCHOR_DATE=2025-05-18|' /srv/energy-report/config/.env
sudo grep '^REPORT_ANCHOR_DATE=' /srv/energy-report/config/.env
cd /srv/energy-report
sudo -u energy-report ./venv/bin/python -m src.main
OUTPUT_ROOT="$(sudo grep '^OUTPUT_DIR=' /srv/energy-report/config/.env | cut -d= -f2-)"
OUTPUT_ROOT="${OUTPUT_ROOT:-/srv/energy-report-output}"
find "$OUTPUT_ROOT" \
  -path "$OUTPUT_ROOT/_staging" -prune -o \
  -type f -print | sort | tail -n 30
```

Expected B2 behavior:
- `daily` artifacts are generated for `2025-05-18`
- `weekly` artifacts are generated for `2025-05-18`

### B3. Restore blank scheduled mode

```bash
sudo sed -i 's|^REPORT_ANCHOR_DATE=.*|REPORT_ANCHOR_DATE=|' /srv/energy-report/config/.env
sudo grep '^REPORT_ANCHOR_DATE=' /srv/energy-report/config/.env
```

Expected B3 result:
- `REPORT_ANCHOR_DATE=` is blank again
- only after this point should the timer be installed or enabled

## 7. Install the ready-made `systemd` files

After B3 has restored blank scheduled mode, install the repo helper:

```bash
cd /srv/energy-report
sudo ./deploy/systemd/install_systemd_units.sh
```

The repo now includes:
- `deploy/systemd/energy-report-etl.service`
- `deploy/systemd/energy-report-etl.timer`
- `deploy/systemd/install_systemd_units.sh`

What the helper does:
- self-escalates with `sudo` when needed
- backs up existing installed unit files if they already exist
- installs the repo sample service and timer into `/etc/systemd/system/`
- runs `systemctl daemon-reload`
- runs `systemctl enable --now energy-report-etl.timer`
- shows timer status and next/last schedule summary

Sample assumptions baked into the repo unit files:
- `User=energy-report`
- `Group=energy-report`
- `WorkingDirectory=/srv/energy-report`
- `ExecStart=/srv/energy-report/venv/bin/python -m src.main`

If your deployment differs from that baseline, edit the files under `deploy/systemd/` before running the helper.

The application itself already reads `config/.env`, so a separate `EnvironmentFile=` is not required unless you intentionally add more host-level variables.

Manual service test:

```bash
sudo systemctl daemon-reload
sudo systemctl start energy-report-etl.service
sudo systemctl status energy-report-etl.service --no-pager
journalctl -u energy-report-etl.service -n 100 --no-pager
```

If you need additional deterministic smoke anchors later, use the companion runbook:
- `docs/workflows/release_runbook.md`

That runbook already documents the approved smoke anchors for:
- daily-only
- Sunday
- month-end

---

## 8. Confirm the timer baseline

The repo sample timer still uses the same runtime rule:
- `OnCalendar=*-*-* 23:00:00`
- `Persistent=true`
- `Unit=energy-report-etl.service`

Meaning:
- `23:00:00` is interpreted in the **host local timezone**
- `Persistent=true` means if the host was off at the scheduled time, the timer will catch up on the next boot

If you install via the helper, the timer is already enabled and started for you. Manual verification remains:

```bash
sudo systemctl status energy-report-etl.timer --no-pager
systemctl list-timers energy-report-etl.timer --all
```

---

## 9. Recommended deployment validation checklist

Before calling the deployment usable, verify:
- MySQL credentials in `config/.env` are correct
- `REPORT_ANCHOR_DATE` is blank in steady-state scheduled mode
- output path is writable and non-hidden
- runtime app logging is size-rotated in `config/logging.yaml`
- Chrome / Chromium is present and PDF export works
- one manual run succeeds from `./venv/bin/python -m src.main`
- `energy-report-etl.service` succeeds when started manually
- `energy-report-etl.timer` is enabled and shows the expected next run
- generated files land in the expected month-grouped folders under the configured output root

Runtime application log baseline:
- config source: `config/logging.yaml`
- log file: `logs/app.log` under the deployed project root, for example `/srv/energy-report/logs/app.log`
- handler: `logging.handlers.RotatingFileHandler`
- max active log size: `10485760` bytes, about 10 MB
- backup retention: `backupCount: 10`, producing `app.log.1` through `app.log.10`

`systemd` journal logs are separate from the application log file. Use `journalctl -u energy-report-etl.service` for service lifecycle, timer-triggered runs, exit codes, and stdout/stderr from the unit.

---

## 10. Operational troubleshooting notes

If the timer runs but outputs look wrong, check these first:

1. `REPORT_ANCHOR_DATE` was accidentally left pinned
2. host timezone is not the intended timezone
3. `OUTPUT_DIR` or `PRINT_STAGING_DIR` points to an invalid or hidden path, or the reader is accidentally looking inside `_staging` instead of the month folders under `OUTPUT_DIR`
4. Google Chrome is missing, or Chromium Snap cannot print from the service account
5. database connectivity fails under the service user
6. the service user lacks write permission to output/log folders

Useful commands:

```bash
journalctl -u energy-report-etl.service -n 200 --no-pager
timedatectl
systemctl list-timers energy-report-etl.timer --all
OUTPUT_ROOT="$(sudo grep '^OUTPUT_DIR=' /srv/energy-report/config/.env | cut -d= -f2-)"
OUTPUT_ROOT="${OUTPUT_ROOT:-/srv/energy-report-output}"
find "$OUTPUT_ROOT" \
  -path "$OUTPUT_ROOT/_staging" -prune -o \
  -type f -print | sort | tail -n 30
```

---

## 11. Recommended document pairing

Use these together:
- deployment/bootstrap on a new host: `docs/workflows/deployment_runbook.md`
- manual smoke anchors and artifact expectations: `docs/workflows/release_runbook.md`
- release-ready checks: `docs/workflows/release_checklist.md`
- PDF print-path details: `docs/workflows/pdf_export_flow.md`
