from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time
import re

URL = "https://www.educationdynamics.com/job-listings/"
COMPANY_NAME = "EducationDynamics"
COLUMNS = ["Job_name", "Job_description", "Posting_date(dd_mm_yyyy)", "Experience",
           "Location", "Company_name", "Job_application_link", "Type"]


def get_experience(text):
    m = re.search(r'(\d+\s*[-–]\s*\d+|\d+)\+?\s*(?:years|yrs)', text.lower())
    return m.group(1) + " years" if m else "NA"


def get_type(text):
    s = text.lower()
    if "remote" in s and "hybrid" not in s: return "Remote"
    if "hybrid" in s: return "Hybrid"
    if "on-site" in s or "onsite" in s: return "Onsite"
    return "NA"


def get_jobs():
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=opts)
    driver.get(URL)
    time.sleep(5)

    jobs, seen = [], set()
    for el in driver.find_elements(By.XPATH, "//a[contains(@href, '/jobs/') or contains(@href, '/career')]"):
        title, link = el.text.strip(), el.get_attribute("href") or ""
        if not title or len(title) < 5 or len(title) > 200 or link in seen: continue
        seen.add(link)
        jobs.append({
            "Job_name": title,
            "Job_description": "NA",
            "Posting_date(dd_mm_yyyy)": None,
            "Experience": get_experience(title),
            "Location": "NA",
            "Company_name": COMPANY_NAME,
            "Job_application_link": link,
            "Type": get_type(title),
        })
    driver.quit()
    return jobs


if __name__ == "__main__":
    try:
        jobs = get_jobs()
    except Exception as e:
        print(f"Selenium error: {e}")
        jobs = []
    if not jobs:
        df = pd.DataFrame([{c: "NA" for c in COLUMNS}])
        df.at[0, "Posting_date(dd_mm_yyyy)"] = "not available"
        df.at[0, "Company_name"] = COMPANY_NAME
    else:
        df = pd.DataFrame(jobs)
        df["Posting_date(dd_mm_yyyy)"] = pd.to_datetime(df["Posting_date(dd_mm_yyyy)"], errors="coerce")
    df = df[COLUMNS]
    df.to_csv("education_dynamics_jobs.csv", index=False, encoding="utf-8", date_format="%d/%m/%Y")
    print(f"Saved {len(df)} jobs")
