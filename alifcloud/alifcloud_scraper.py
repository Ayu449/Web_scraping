import requests
import pandas as pd
from bs4 import BeautifulSoup
import re
import html
import json
from datetime import datetime

URL = "https://recruit.alifconsulting.com/jobs/alifconsulting"
JOB_URL = "https://recruit.alifconsulting.com/jobs/alifconsulting/{job_id}"
COMPANY_NAME = "AlifCloud IT Consulting Pvt. Ltd."
HEADERS = {"User-Agent": "Mozilla/5.0"}
COLUMNS = ["Job_name", "Job_description", "Posting_date(dd_mm_yyyy)", "Experience",
           "Location", "Company_name", "Job_application_link", "Type"]


def get_experience(text):
    m = re.search(r'(\d+\s*[-–]\s*\d+|\d+)\+?\s*(?:years|yrs)', text.lower())
    return m.group(1) + " years" if m else "NA"


def get_type(remote_flag, loc, desc):
    if remote_flag is True: return "Remote"
    s = (loc + " " + desc).lower()
    if "remote" in s and "hybrid" not in s: return "Remote"
    if "hybrid" in s: return "Hybrid"
    return "Onsite"


def get_jobs():
    r = requests.get(URL, headers=HEADERS, timeout=30)
    soup = BeautifulSoup(r.text, "html.parser")
    jobs = []
    for inp in soup.find_all("input", type="hidden"):
        val = inp.get("value", "")
        if "Posting_Title" not in val: continue
        try:
            zoho_jobs = json.loads(html.unescape(val))
        except json.JSONDecodeError:
            continue
        for j in zoho_jobs:
            desc = j.get("Job_Description") or ""
            location = ", ".join([p for p in (j.get("City"), j.get("State"), j.get("Country")) if p]) or "NA"
            try:
                dt = datetime.strptime(j["Date_Opened"].strip(), "%Y-%m-%d") if j.get("Date_Opened") else None
            except Exception:
                dt = None
            jobs.append({
                "Job_name": j.get("Posting_Title", "NA"),
                "Job_description": desc,
                "Posting_date(dd_mm_yyyy)": dt,
                "Experience": str(j.get("Work_Experience") or "").strip() or get_experience(desc),
                "Location": location,
                "Company_name": COMPANY_NAME,
                "Job_application_link": JOB_URL.format(job_id=j.get("id", "")),
                "Type": get_type(j.get("Remote_Job"), location, desc),
            })
        break
    return jobs


def filter_recent(df, days=2):
    if df.empty or df["Posting_date(dd_mm_yyyy)"].isna().all(): return df
    now = pd.Timestamp.utcnow().tz_localize(None)
    for w in (days, 30, 90, 360):
        f = df[df["Posting_date(dd_mm_yyyy)"] >= now - pd.Timedelta(days=w)]
        if not f.empty:
            return f.sort_values("Posting_date(dd_mm_yyyy)", ascending=False)
    return df


if __name__ == "__main__":
    jobs = get_jobs()
    if not jobs:
        df = pd.DataFrame([{c: "NA" for c in COLUMNS}])
        df.at[0, "Posting_date(dd_mm_yyyy)"] = "not available"
        df.at[0, "Company_name"] = COMPANY_NAME
    else:
        df = pd.DataFrame(jobs)
        df["Posting_date(dd_mm_yyyy)"] = pd.to_datetime(df["Posting_date(dd_mm_yyyy)"], errors="coerce")
        df = filter_recent(df)
    df = df[COLUMNS]
    df.to_csv("alifcloud_jobs.csv", index=False, encoding="utf-8", date_format="%d/%m/%Y")
    print(f"Saved {len(df)} jobs")
