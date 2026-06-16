# fsweb-scraper

Scrapes your grades from [Studentweb (fsweb.no)](https://fsweb.no/studentweb/) and sends a push notification via [ntfy](https://ntfy.sh) whenever a new grade appears.

Built for NTNU, but can be adapted for other institutions supported by Studentweb.

---

## How it works

On each run the scraper:
1. Logs in to Studentweb with your student ID and PIN using a headless Chromium browser (Playwright).
2. Reads all graded results from the results page.
3. Compares them against a local `results.json` state file.
4. Sends a push notification for every new grade it hasn't seen before.
5. Saves the updated results to disk.

The first run is treated as a baseline — it saves all existing grades without notifying, so you only get notified for grades that appear after the initial run.

---

## Requirements

- Python 3.10 or newer
- `pip` (comes with Python)
- A free [ntfy.sh](https://ntfy.sh) topic URL (or a self-hosted ntfy instance)

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/phillipdyb/fsweb-scraper.git
cd fsweb-scraper
```

### 2. Install Python dependencies

```bash
pip install playwright
```

### 3. Install the Playwright browser

Playwright needs to download the Chromium browser binary it controls. Run:

```bash
playwright install chromium
```

> If you get a "browser not found" or `executable doesn't exist` error later, this step was missed or ran in a different Python environment.

---

## Configuration

### 1. Copy the example environment file

```bash
cp example.env credentials.env
```

### 2. Fill in your credentials

Open `credentials.env` and replace the placeholder values:

```env
STUDENT_ID=12345677888   # Your 11-digit Norwegian national ID (fødselsnummer)
STUDENT_PW=1234          # Your 4-digit Studentweb PIN
NTFY_URL=https://ntfy.sh/your-topic-name   # The ntfy topic URL to push notifications to
FILES_PWD=/path/to/folder                  # Absolute path to a folder where results.json will be stored
```

**`STUDENT_ID`** — Your 11-digit Norwegian ID number used to log in to Studentweb.

**`STUDENT_PW`** — Your 4-digit PIN for Studentweb.

**`NTFY_URL`** — A unique ntfy topic URL. Pick any name for the topic (e.g. `https://ntfy.sh/my-grades-abc123`). Subscribe to the same topic in the ntfy app on your phone to receive notifications. Keep the topic name private — anyone with it can send messages to it.

**`FILES_PWD`** — Directory where `results.json` is saved between runs. The directory must already exist. Example: `/home/user/fsweb-scraper` or `/Users/me/Documents/grades`.

> `credentials.env` is in `.gitignore` and should never be committed to version control.

---

## Running the scraper

```bash
bash run.sh
```

The script sources `credentials.env` automatically and runs `scraper.py`.

**First run output:**
```
First run: saved 12 existing results as baseline.
```

**Subsequent run with no new grades:**
```
No new results.
```

**Subsequent run with a new grade:**
```
Notified: Algorithms and Data Structures - Skriftlig eksamen: A
```

---

## Automating with cron

To check for new grades automatically, set up a cron job. The recommended minimum interval is once per hour — checking more frequently is unlikely to catch grades sooner and adds unnecessary load.

Open your crontab:

```bash
crontab -e
```

Add a line like the following to run the scraper every hour:

```cron
0 * * * * /bin/bash /absolute/path/to/fsweb-scraper/run.sh >> /absolute/path/to/fsweb-scraper/cron.log 2>&1
```

Replace `/absolute/path/to/fsweb-scraper` with the actual path on your system. The `>> cron.log 2>&1` part appends all output (including errors) to a log file so you can debug if something goes wrong.

To find the absolute path of the repo:

```bash
cd fsweb-scraper && pwd
```

---

## Notifications

Notifications are sent via [ntfy](https://ntfy.sh). Each notification includes:
- **Title:** `Ny karakter!`
- **Body:** `<Course name> - <Assessment type>: <Grade>`
- **Priority:** High

To receive them on your phone, install the ntfy app ([iOS](https://apps.apple.com/app/ntfy/id1625396347) / [Android](https://play.google.com/store/apps/details?id=io.heckel.ntfy)) and subscribe to the same topic URL you set in `NTFY_URL`.

---

## Troubleshooting

**`Missing required environment variables`**
— `credentials.env` is missing or not all four variables are set. Double-check the file exists and has no typos.

**`browser not found` / Playwright error**
— Run `playwright install chromium` again inside the same Python environment where Playwright is installed.

**`State file corrupted, starting fresh`**
— `results.json` was partially written or is invalid JSON. The scraper will recreate it on the next run.

**Cron job not running**
— Ensure the path in the crontab is absolute, `run.sh` is executable (`chmod +x run.sh`), and Python is available at the path used by cron (you may need to use the full path to `python3`).
