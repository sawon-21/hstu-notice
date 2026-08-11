import json
import requests
import urllib3
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_session():
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=1)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Referer': 'https://hstu.ac.bd/'
    })
    return session

EXAM_RESULT_URL = "https://hstu.ac.bd/page/exam_result"

def extract_pdf_link(session, page_url):
    try:
        res = session.get(page_url, timeout=15, verify=False)
        if res.status_code == 200:
            sub_soup = BeautifulSoup(res.text, 'html.parser')
            for a in sub_soup.find_all('a', href=True):
                href = a['href'].strip()
                if '.pdf' in href.lower() or 'notice_file' in href.lower() or 'download' in href.lower() or '/files/' in href.lower():
                    if not href.startswith('http'):
                        href = f"https://hstu.ac.bd{'' if href.startswith('/') else '/'}{href}"
                    return href
    except Exception as e:
        print(f"Error fetching direct PDF from {page_url}: {e}")
    return page_url

def scrape_exam_results():
    session = get_session()
    results = []

    try:
        response = session.get(EXAM_RESULT_URL, timeout=30, verify=False)
        print(f"[Exam Results] Status: {response.status_code}")

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            rows = soup.find_all('tr')
            
            for row in rows:
                cols = row.find_all('td')
                if not cols:
                    continue

                a_tag = row.find('a', href=True)
                if a_tag:
                    title = a_tag.text.strip()
                    if not title or len(title) < 3:
                        continue

                    link = a_tag['href'].strip()
                    if not link.startswith('http'):
                        link = f"https://hstu.ac.bd{'' if link.startswith('/') else '/'}{link}"

                    direct_pdf_link = extract_pdf_link(session, link)

                    date = "N/A"
                    for col in cols:
                        text = col.text.strip()
                        if any(char.isdigit() for char in text) and ('-' in text or '/' in text or ',' in text):
                            date = text
                            break

                    results.append({
                        "category": "Exam Result",
                        "title": title,
                        "date": date,
                        "link": direct_pdf_link
                    })

    except Exception as e:
        print(f"Error scraping exam results: {e}")

    unique_results = []
    seen_links = set()
    for item in results:
        if item['link'] not in seen_links:
            seen_links.add(item['link'])
            unique_results.append(item)

    if unique_results:
        with open('results.json', 'w', encoding='utf-8') as f:
            json.dump(unique_results, f, ensure_ascii=False, indent=4)
        print(f"Successfully saved {len(unique_results)} exam result PDFs to results.json.")

if __name__ == '__main__':
    scrape_exam_results()
