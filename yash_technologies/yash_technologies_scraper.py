import requests
import pandas as pd
from bs4 import BeautifulSoup
import re
import html
from datetime import datetime

COMPANY = "YashTechnologies2"
LIST_URL = f"https://api.smartrecruiters.com/v1/companies/{COMPANY}/postings?limit=100"
DETAIL_URL = f"https://api.smartrecruiters.com/v1/companies/{COMPANY}/postings/"
COLUMNS = ["Job_name", "Job_description", "Posting_date(dd_mm_yyyy)", "Experience",
           "Location", "Company_name", "Job_application_link", "Type"]


def clean(s):
    return BeautifulSoup(html.unescape(s), "html.parser").get_text(" ", strip=True) if s else ""


def get_experience(text):
    m = re.search(r'(\d+\s*[-–]\s*\d+|\d+)\+?\s*(?:years|yrs)', text.lower())
    return m.group(1) + " years" if m else "NA"


def get_type(loc):
    if not loc: return "Onsite"
    if loc.get("remote"): return "Remote"
    if loc.get("hybrid"): return "Hybrid"
    return "Onsite"


def get_jobs():
    listings = requests.get(LIST_URL).json().get("content", [])
    jobs = []
    for j in listings:
        uuid = j.get("uuid")
        loc = j.get("location") or {}
        try:
            d = requests.get(DETAIL_URL + uuid).json()
        except Exception:
            d = {}
        sections = (d.get("jobAd") or {}).get("sections") or {}
        desc = " ".join(clean((sections.get(k) or {}).get("text", ""))
                        for k in ("jobDescription", "qualifications", "additionalInformation"))
        try:
            dt = datetime.fromisoformat(j["releasedDate"].replace("Z", "+00:00")) if j.get("releasedDate") else None
        except Exception:
            dt = None
        jobs.append({
            "Job_name": j.get("name", "NA"),
            "Job_description": desc,
            "Posting_date(dd_mm_yyyy)": dt,
            "Experience": (j.get("experienceLevel") or {}).get("label") or get_experience(desc),
            "Location": loc.get("fullLocation") or loc.get("city", "NA"),
            "Company_name": "YASH Technologies",
            "Job_application_link": d.get("applyUrl") or f"https://jobs.smartrecruiters.com/{COMPANY}/{uuid}",
            "Type": get_type(loc),
        })
    return jobs


def filter_recent(df, days=2):
    if df.empty or df["Posting_date(dd_mm_yyyy)"].isna().all(): return df
    now = pd.Timestamp.utcnow()
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
        df.at[0, "Company_name"] = "YASH Technologies"
    else:
        df = pd.DataFrame(jobs)
        df["Posting_date(dd_mm_yyyy)"] = pd.to_datetime(df["Posting_date(dd_mm_yyyy)"], errors="coerce", utc=True)
        df = filter_recent(df)
    df = df[COLUMNS]
    df.to_csv("yash_technologies_jobs.csv", index=False, encoding="utf-8", date_format="%d/%m/%Y")
    print(f"Saved {len(df)} jobs")
