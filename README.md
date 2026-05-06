# Job Scraper System

Python-based job scraping system that collects job postings from 5 company career pages.

## Companies Covered
1. Delta Velocity
2. AlifCloud IT Consulting Pvt. Ltd.
3. PayPal
4. Education Dynamics, Inc.
5. YASH Technologies

## Tech Stack
- Python
- Requests
- Pandas
- BeautifulSoup
- Selenium

## CSV Format

```
Job_name, Job_description, Posting_date(dd_mm_yyyy), Experience,
Location, Company_name, Job_application_link, Type
```

- `Posting_date(dd_mm_yyyy)` is formatted as `DD/MM/YYYY` (or `not available` if unknown).
- `Type` is one of `Remote`, `Hybrid`, `Onsite`, or `NA`.

## Run Project

```bash
pip install -r requirements.txt

python paypal/paypal_scraper.py
python yash_technologies/yash_technologies_scraper.py
python alifcloud/alifcloud_scraper.py
python education_dynamics/education_dynamics_scraper.py
python delta_velocity/delta_velocity_scraper.py
```

Or run all at once:

```bash
bash run_all.sh
```

Each scraper writes its CSV inside its own folder (e.g., `paypal/paypal_jobs.csv`).
