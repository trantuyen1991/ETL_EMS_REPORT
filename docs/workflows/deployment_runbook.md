# Deployment Runbook

Use this runbook when bringing the project onto a new Ubuntu / systemd host after cloning the repository.

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

## 1. Prepare the new host

Install baseline tools as needed:

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip poppler-utils
```

Browser runtime requirement:
- ensure Chrome or Chromium is installed and callable on the host
- verify with one of:

```bash
which google-chrome || which chromium || which chromium-browser
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

## 2. Clone the project and create a fresh venv

Recommended baseline for the sample `systemd` files in this repo:
- Linux user/group: `energy-report`
- project root: `/srv/energy-report`

Example using that baseline:

```bash
sudo useradd --system --create-home --home-dir /srv/energy-report --shell /usr/sbin/nologin energy-report || true
sudo mkdir -p /srv
sudo chown energy-report:energy-report /srv
sudo -u energy-report git clone <your-repo-url> /srv/energy-report
cd /srv/energy-report
sudo -u energy-report python3 -m venv venv
sudo -u energy-report ./venv/bin/pip install --upgrade pip
sudo -u energy-report ./venv/bin/pip install -r requirements.txt
```

Important:
- do **not** copy an old `venv/` from another machine
- always recreate the virtual environment on the new host
- if you do not use the `energy-report` service account or `/srv/energy-report` path, update the sample `systemd` files before installing them

---

## 3. Configure `config/.env`

The application loads runtime values from:
- `config/.env`
- `config/app.yaml`

Create or update `config/.env` with the deployment-specific values.

Minimum fields to confirm:

```dotenv
MYSQL_HOST=<db-host>
MYSQL_PORT=<db-port>
MYSQL_DATABASE=<db-name>
MYSQL_USER=<db-user>
MYSQL_PASSWORD=<db-password>

OUTPUT_DIR=/srv/energy-report-output
PRINT_STAGING_DIR=/srv/energy-report-output
REPORT_FILENAME=energy_automatic_report
REPORT_ANCHOR_DATE=
```

Critical operational notes:
- `OUTPUT_DIR` and `PRINT_STAGING_DIR` should point to a **non-hidden writable path**
- `REPORT_FILENAME` should stay aligned with the accepted runtime naming: `energy_automatic_report`
- `REPORT_ANCHOR_DATE` must normally be **blank** in scheduled production mode
- only set `REPORT_ANCHOR_DATE` temporarily for smoke tests or backfill-style manual runs

Why `REPORT_ANCHOR_DATE` must be blank for scheduled mode:
- if it stays pinned to a fixed date, the daily timer will keep regenerating that old anchor day instead of the current date

Also create writable output/log directories if they do not already exist:

```bash
mkdir -p /srv/energy-report-output
mkdir -p logs
```

---

## 4. Run a manual smoke check before enabling schedule

From the project root:

```bash
cd /srv/energy-report
./venv/bin/python -m src.main
```

Expected baseline behavior:
- one `daily` batch is always generated
- `weekly` is added automatically only when the anchor day is Sunday
- `monthly` is added automatically only when the anchor day is month-end
- the daily run also produces one Excel workbook

Check outputs under:

```bash
find /srv/energy-report-output -maxdepth 3 -type f | sort | tail -n 20
```

If you need deterministic smoke anchors, use the companion runbook:
- `docs/workflows/release_runbook.md`

That runbook already documents the approved smoke anchors for:
- daily-only
- Sunday
- month-end

After a temporary smoke anchor, restore:

```dotenv
REPORT_ANCHOR_DATE=
```

---

## 5. Create a `systemd` service for one ETL batch run

Ready-made sample file in the repo:
- `deploy/systemd/energy-report-etl.service`

Install it with:

```bash
sudo cp deploy/systemd/energy-report-etl.service /etc/systemd/system/
```

Sample assumptions:
- `User=energy-report`
- `Group=energy-report`
- `WorkingDirectory=/srv/energy-report`
- `ExecStart=/srv/energy-report/venv/bin/python -m src.main`

If your deployment differs from that baseline, edit the copied file before reloading `systemd`.

The application itself already reads `config/.env`, so a separate `EnvironmentFile=` is not required unless you intentionally add more host-level variables.

Manual service test:

```bash
sudo systemctl daemon-reload
sudo systemctl start energy-report-etl.service
sudo systemctl status energy-report-etl.service --no-pager
```

View logs:

```bash
journalctl -u energy-report-etl.service -n 100 --no-pager
```

---

## 6. Create a `systemd` timer for `23:00` every day

Ready-made sample file in the repo:
- `deploy/systemd/energy-report-etl.timer`

Install it with:

```bash
sudo cp deploy/systemd/energy-report-etl.timer /etc/systemd/system/
```

Meaning:
- `23:00:00` is interpreted in the **host local timezone**
- `Persistent=true` means if the host was off at the scheduled time, the timer will catch up on the next boot

Enable the timer:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now energy-report-etl.timer
sudo systemctl status energy-report-etl.timer --no-pager
```

Verify next/last run:

```bash
systemctl list-timers energy-report-etl.timer --all
```

---

## 7. Recommended deployment validation checklist

Before calling the deployment usable, verify:
- MySQL credentials in `config/.env` are correct
- `REPORT_ANCHOR_DATE` is blank in steady-state scheduled mode
- output path is writable and non-hidden
- Chrome / Chromium is present and PDF export works
- one manual run succeeds from `./venv/bin/python -m src.main`
- `energy-report-etl.service` succeeds when started manually
- `energy-report-etl.timer` is enabled and shows the expected next run
- generated files land in the expected month-grouped folders under the configured output root

---

## 8. Operational troubleshooting notes

If the timer runs but outputs look wrong, check these first:

1. `REPORT_ANCHOR_DATE` was accidentally left pinned
2. host timezone is not the intended timezone
3. `OUTPUT_DIR` or `PRINT_STAGING_DIR` points to an invalid or hidden path
4. Chrome / Chromium is missing or cannot print
5. database connectivity fails under the service user
6. the service user lacks write permission to output/log folders

Useful commands:

```bash
journalctl -u energy-report-etl.service -n 200 --no-pager
timedatectl
systemctl list-timers energy-report-etl.timer --all
find /srv/energy-report-output -maxdepth 3 -type f | sort | tail -n 30
```

---

## 9. Recommended document pairing

Use these together:
- deployment/bootstrap on a new host: `docs/workflows/deployment_runbook.md`
- manual smoke anchors and artifact expectations: `docs/workflows/release_runbook.md`
- release-ready checks: `docs/workflows/release_checklist.md`
- PDF print-path details: `docs/workflows/pdf_export_flow.md`
