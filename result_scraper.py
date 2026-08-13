import json
import requests
import urllib3
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_session():
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=2, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://hstu.ac.bd/'
    })
    return session

EXAM_RESULT_URL = "https://hstu.ac.bd/page/exam_result"

def extract_direct_pdf(session, notice_url):
    if notice_url.lower().endswith('.pdf'):
        return notice_url
    
    try:
        res = session.get(notice_url, timeout=12, verify=False)
        if res.status_code == 200:
            sub_soup = BeautifulSoup(res.text, 'html.parser')
            
            for tag in sub_soup.find_all(['iframe', 'embed', 'object']):
                src = tag.get('src') or tag.get('data') or ''
                src = src.strip()
                if src and any(k in src.lower() for k in ['.pdf', 'drive.google.com', 'notice', 'uploads', 'files', 'result']):
                    if not src.startswith('http'):
                        src = f"https://hstu.ac.bd{'' if src.startswith('/') else '/'}{src}"
                    return src
            
            for a in sub_soup.find_all('a', href=True):
                href = a['href'].strip()
                href_lower = href.lower()
                text_lower = a.text.strip().lower()
                
                if any(ext in href_lower for ext in ['.pdf', 'notice_file', 'uploads', 'files', 'drive.google.com']) or \
                   any(kw in text_lower for kw in ['download', 'pdf', 'result', 'ডাউনলোড']):
                    if not href.startswith('http'):
                        href = f"https://hstu.ac.bd{'' if href.startswith('/') else '/'}{href}"
                    return href
    except Exception as e:
        print(f"Error resolving result link {notice_url}: {e}")
        
    return notice_url

def scrape_exam_results():
    session = get_session()
    results = []

    print(f"Scraping exam results from {EXAM_RESULT_URL}...")
    try:
        response = session.get(EXAM_RESULT_URL, timeout=25, verify=False)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            rows = soup.find_all('tr')
            
            count = 0
            for row in rows:
                cols = row.find_all('td')
                if not cols:
                    continue

                a_tag = row.find('a', href=True)
                if a_tag:
                    title = a_tag.text.strip()
                    link = a_tag['href'].strip()

                    if not title or len(title) < 3 or ('exam_result' in link.lower() and link.endswith('exam_result')):
                        continue

                    if not link.startswith('http'):
                        link = f"https://hstu.ac.bd{'' if link.startswith('/') else '/'}{link}"

                    date = "N/A"
                    for col in cols:
                        text = col.text.strip()
                        if any(char.isdigit() for char in text) and ('-' in text or '/' in text or ',' in text or '202' in text or '201' in text):
                            date = text
                            break

                    pdf_link = extract_direct_pdf(session, link)

                    results.append({
                        "category": "Exam Result",
                        "title": title,
                        "date": date,
                        "link": pdf_link
                    })

                    count += 1
                    if count >= 25:
                        break

            # Fallback if tr parsing returned nothing
            if not results:
                for a_tag in soup.find_all('a', href=True):
                    title = a_tag.text.strip()
                    link = a_tag['href'].strip()
                    if len(title) > 5 and ('result' in link.lower() or 'id' in link.lower() or 'file' in link.lower()):
                        if not link.startswith('http'):
                            link = f"https://hstu.ac.bd{'' if link.startswith('/') else '/'}{link}"
                        pdf_link = extract_direct_pdf(session, link)
                        results.append({
                            "category": "Exam Result",
                            "title": title,
                            "date": "N/A",
                            "link": pdf_link
                        })

    except Exception as e:
        print(f"Error scraping exam results: {e}")

    # Deduplicate
    unique_results = []
    seen = set()
    for r in results:
        key = (r['title'], r['link'])
        if key not in seen:
            seen.add(key)
            unique_results.append(r)

    if unique_results:
        with open('results.json', 'w', encoding='utf-8') as f:
            json.dump(unique_results, f, ensure_ascii=False, indent=4)
        print(f"Saved {len(unique_results)} exam results to results.json")
    else:
        print("No exam results scraped. Keeping existing results.json")

if __name__ == '__main__':
    scrape_exam_results()
