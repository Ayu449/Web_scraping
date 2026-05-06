import requests
import pandas as pd
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta

LIST_URL = "https://paypal.wd1.myworkdayjobs.com/wday/cxs/paypal/jobs/jobs"
DETAIL_URL = "https://paypal.wd1.myworkdayjobs.com/wday/cxs/paypal/jobs"
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json", "Content-Type": "application/json"}
COLUMNS = ["Job_name", "Job_description", "Posting_date(dd_mm_yyyy)", "Experience",
           "Location", "Company_name", "Job_application_link", "Type"]


def clean(s):
    return BeautifulSoup(s, "html.parser").get_text(" ", strip=True) if s else ""


def strip_boilerplate(text):
    markers = ["Job Description", "Position Overview", "About the Role", "Responsibilities", "Key Responsibilities"]
    earliest = -1
    for m in markers:
        idx = text.lower().find(m.lower())
        if idx > 100 and (earliest == -1 or idx < earliest):
            earliest = idx
    return text[earliest:] if earliest > 0 else text


def parse_date(s):
    if not s: return None
    sl = s.lower()
    today = datetime.utcnow()
    if "today" in sl: return today
    if "yesterday" in sl: return today - timedelta(days=1)
    m = re.search(r'(\d+)\+?\s*day', sl)
    return today - timedelta(days=int(m.group(1))) if m else None


def get_experience(text):
    m = re.search(r'(\d+\s*[-–]\s*\d+|\d+)\+?\s*(?:years|yrs)', text.lower())
    return m.group(1) + " years" if m else "NA"


def get_type(rt, loc):
    s = ((rt or "") + " " + (loc or "")).lower()
    if "remote" in s and "hybrid" not in s: return "Remote"
    if "hybrid" in s: return "Hybrid"
    return "Onsite"


def get_jobs(max_detail=10):
    payload = {"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": ""}
    listings = requests.post(LIST_URL, json=payload, headers=HEADERS, timeout=30).json().get("jobPostings", [])
    jobs = []
    for p in listings[:max_detail]:
        ext = p.get("externalPath", "")
        try:
            info = requests.get(DETAIL_URL + ext, headers=HEADERS, timeout=30).json().get("jobPostingInfo") or {}
        except Exception:
            info = {}
        desc = strip_boilerplate(clean(info.get("jobDescription")))
        try:
            dt = datetime.strptime(info["startDate"], "%Y-%m-%d") if info.get("startDate") else parse_date(p.get("postedOn"))
        except Exception:
            dt = parse_date(p.get("postedOn"))
        jobs.append({
            "Job_name": info.get("title") or p.get("title", "NA"),
            "Job_description": desc,
            "Posting_date(dd_mm_yyyy)": dt,
            "Experience": get_experience(desc),
            "Location": info.get("location") or p.get("locationsText", "NA"),
            "Company_name": "PayPal",
            "Job_application_link": info.get("externalUrl") or "https://paypal.wd1.myworkdayjobs.com/jobs" + ext,
            "Type": get_type(info.get("remoteType"), info.get("location")),
        })
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
    df = pd.DataFrame(get_jobs())
    df["Posting_date(dd_mm_yyyy)"] = pd.to_datetime(df["Posting_date(dd_mm_yyyy)"], errors="coerce")
    df = filter_recent(df)
    df = df[COLUMNS]
    df.to_csv("paypal_jobs.csv", index=False, encoding="utf-8", date_format="%d/%m/%Y")
    print(f"Saved {len(df)} jobs")
