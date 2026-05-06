import requests
import pandas as pd
from bs4 import BeautifulSoup
import re
import time
from datetime import datetime, timedelta

COMPANY_NAME = "Delta Velocity"
KEYWORD = "Delta Velocity"
LOCATION = "Worldwide"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0"}
COLUMNS = ["Job_name", "Job_description", "Posting_date(dd_mm_yyyy)", "Experience",
           "Location", "Company_name", "Job_application_link", "Type"]


def parse_date(s):
    if not s: return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        pass
    sl, today = s.lower(), datetime.utcnow()
    if "today" in sl: return today
    if "yesterday" in sl: return today - timedelta(days=1)
    m = re.search(r'(\d+)\s*(hour|day|week|month)', sl)
    if m and "ago" in sl:
        n, u = int(m.group(1)), m.group(2)
        if u == "day": return today - timedelta(days=n)
        if u == "week": return today - timedelta(weeks=n)
        if u == "month": return today - timedelta(days=n * 30)
    return None


def get_type(text):
    s = text.lower()
    if "remote" in s and "hybrid" not in s: return "Remote"
    if "hybrid" in s: return "Hybrid"
    return "Onsite"


def get_experience(text):
    m = re.search(r'(\d+\s*[-–]\s*\d+|\d+)\+?\s*(?:years|yrs)', text.lower())
    return m.group(1) + " years" if m else "NA"


def fetch_detail(url):
    for _ in range(2):
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                d = soup.find("div", class_="show-more-less-html__markup")
                return d.get_text(" ", strip=True) if d else ""
            time.sleep(2)
        except Exception:
            time.sleep(1)
    return ""


def fetch_page(start):
    url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={KEYWORD}&location={LOCATION}&start={start}"
    r = requests.get(url, headers=HEADERS, timeout=20)
    if r.status_code != 200: return []
    soup = BeautifulSoup(r.text, "html.parser")
    out = []
    for c in soup.find_all(["li", "div"], class_=re.compile(r"base-card|job-search-card")):
        t = c.find(class_=re.compile(r"base-search-card__title")) or c.find("h3")
        a = c.find("a", class_=re.compile(r"base-card__full-link"))
        l = c.find(class_=re.compile(r"job-search-card__location"))
        tm = c.find("time")
        if not t: continue
        out.append({
            "title": t.get_text(" ", strip=True),
            "link": a.get("href", "") if a else "",
            "location": l.get_text(" ", strip=True) if l else "NA",
            "date": parse_date(tm.get("datetime") if tm else "")
        })
    return out


def get_jobs():
    cards, seen, start = [], set(), 0
    for _ in range(20):
        page = fetch_page(start)
        if not page: break
        new = sum(1 for j in page if j["link"] and j["link"] not in seen and (seen.add(j["link"]) or cards.append(j) or True))
        if new == 0: break
        start += 25

    jobs = []
    for i, c in enumerate(cards):
        desc = fetch_detail(c["link"]) or "NA"
        if i < len(cards) - 1: time.sleep(0.3)
        jobs.append({
            "Job_name": c["title"],
            "Job_description": desc,
            "Posting_date(dd_mm_yyyy)": c["date"],
            "Experience": get_experience(c["title"] + " " + desc),
            "Location": c["location"],
            "Company_name": COMPANY_NAME,
            "Job_application_link": c["link"],
            "Type": get_type(c["title"] + " " + desc + " " + c["location"]),
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
        df.at[0, "Company_name"] = COMPANY_NAME
    else:
        df = pd.DataFrame(jobs)
        df["Posting_date(dd_mm_yyyy)"] = pd.to_datetime(df["Posting_date(dd_mm_yyyy)"], errors="coerce", utc=True)
        df = filter_recent(df)
    df = df[COLUMNS]
    df.to_csv("delta_velocity_jobs.csv", index=False, encoding="utf-8", date_format="%d/%m/%Y")
    print(f"Saved {len(df)} jobs")
