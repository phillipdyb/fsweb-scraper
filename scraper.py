import urllib.request
import json
import os
import sys
from playwright.sync_api import Playwright, sync_playwright


def scrape(playwright: Playwright) -> list[dict]:
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    # login
    page.goto("https://fsweb.no/studentweb/velgInstitusjon.jsf")
    page.locator('[id="institusjonsvalg:institusjonsMenu"]').select_option("FSNTNU")
    page.get_by_role("button", name="Choose").click()
    page.get_by_role("textbox", name="Norwegian ID (11 digits):").fill(os.environ["STUDENT_ID"])
    page.get_by_role("textbox", name="PIN code (4 digits):").fill(os.environ["STUDENT_PW"])
    page.get_by_role("button", name="Log in").click()
    page.wait_for_load_state("networkidle")

    # results page
    page.goto("https://fsweb.no/studentweb/resultater.jsf")
    page.wait_for_selector("table.table-standard tbody tr")
    page.wait_for_load_state("networkidle")

    # scrape
    results = []
    rows = page.locator("table.table-standard tbody tr")
    for i in range(rows.count()):
        row = rows.nth(i)
        code = row.locator("td.col2Emne .uuHidden").inner_text().strip()
        grade = row.locator("td.col6Resultat .infoLinje").inner_text().strip()
        date = row.locator("td.col4ResultatDato").inner_text().strip()
        vurdering = row.locator("td.col3Vurdering").inner_text().strip()
        name = row.locator("td.col2Emne .infoLinje").last.text_content().strip()
        if grade:
            results.append({"code": code, "name": name, "vurdering": vurdering, "grade": grade, "date": date})

    context.close()
    browser.close()
    return results


def load_old(path: str) -> list[dict]:
    if os.path.exists(path):
        try:
            with open(path) as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"State file corrupted, starting fresh: {e}", file=sys.stderr)
    return []


def save(results: list[dict], path: str) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def notify(r: dict) -> None:
    course = r.get("name") or r["code"]
    message = f"{course} - {r['vurdering']}: {r['grade']}"
    req = urllib.request.Request(
        os.environ['NTFY_URL'],
        data=message.encode("utf-8"),
        headers={"Title": "Ny karakter!", "Priority": "high", "Tags": "mortar_board"},
    )
    try:
        urllib.request.urlopen(req, timeout=10)
        print(f"Notified: {message}")
    except Exception as e:
        print(f"Notification failed for {message}: {e}", file=sys.stderr)


def main() -> None:
    REQUIRED_ENV = ["STUDENT_ID", "STUDENT_PW", "NTFY_URL", "FILES_PWD"]
    missing = [v for v in REQUIRED_ENV if not os.environ.get(v)]
    if missing:
        sys.exit(f"Missing required environment variables: {', '.join(missing)}")

    state_file = os.path.join(os.environ["FILES_PWD"], "results.json")

    first_run = not os.path.exists(state_file)
    old = load_old(state_file)

    with sync_playwright() as playwright:
        new = scrape(playwright)

    def key(r):
        return (r["code"], r.get("vurdering", ""), r["grade"], r["date"])

    old_keys = {key(r) for r in old}
    new_entries = [r for r in new if key(r) not in old_keys]

    if first_run:
        print(f"First run: saved {len(new)} existing results as baseline.")
    elif new_entries:
        for r in new_entries:
            notify(r)
    else:
        print("No new results.")

    if not new:
        print("No results returned — skipping save to avoid wiping state.", file=sys.stderr)
        return

    save(new, state_file)


if __name__ == "__main__":
    main()
