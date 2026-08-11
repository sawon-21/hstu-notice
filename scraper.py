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

SOURCES = [
    {"category": "CSE", "url": "https://hstu.ac.bd/page/all_notice/type/f/id/2"},
    {"category": "Agriculture", "url": "https://hstu.ac.bd/page/all_notice/type/f/id/4"},
    {"category": "BBA", "url": "https://hstu.ac.bd/page/all_notice/type/f/id/3"}
]

def extract_pdf_link(session, page_url):
    """নোটিশের ভেতরের পেইজে ঢুকে সরাসরি PDF লিংক খুঁজে বের করবে"""
    try:
        res = session.get(page_url, timeout=15, verify=False)
        if res.status_code == 200:
            sub_soup = BeautifulSoup(res.text, 'html.parser')
            # আসল PDF ফাইল লিংক খোঁজা
            for a in sub_soup.find_all('a', href=True):
                href = a['href'].strip()
                if '.pdf' in href.lower() or 'notice_file' in href.lower() or 'download' in href.lower() or '/files/' in href.lower():
                    if not href.startswith('http'):
                        href = f"https://hstu.ac.bd{'' if href.startswith('/') else '/'}{href}"
                    return href
    except Exception as e:
        print(f"Error fetching direct PDF from {page_url}: {e}")
    return page_url

def scrape_faculty_notices():
    session = get_session()
    all_notices = []

    for source in SOURCES:
        category = source["category"]
        url = source["url"]
        
        try:
            response = session.get(url, timeout=30, verify=False)
            print(f"[{category}] Status: {response.status_code}")
            
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
                        
                        # সরাসরি PDF লিংক বের করার জন্য দ্বিতীয় ধাপে কল
                        direct_pdf_link = extract_pdf_link(session, link)
                        
                        date = "N/A"
                        for col in cols:
                            text = col.text.strip()
                            if any(char.isdigit() for char in text) and ('-' in text or '/' in text or ',' in text):
                                date = text
                                break
                        
                        all_notices.append({
                            "category": category,
                            "title": title,
                            "date": date,
                            "link": direct_pdf_link  # মূল PDF লিংক সেভ হবে
                        })

        except Exception as e:
            print(f"Error scraping {category} ({url}): {e}")

    # ডুপ্লিকেট নোটিশ বাদ দেওয়া
    unique_notices = []
    seen_links = set()
    for item in all_notices:
        if item['link'] not in seen_links:
            seen_links.add(item['link'])
            unique_notices.append(item)

    if unique_notices:
        with open('notices.json', 'w', encoding='utf-8') as f:
            json.dump(unique_notices, f, ensure_ascii=False, indent=4)
        print(f"Successfully saved {len(unique_notices)} direct PDF notices.")

if __name__ == '__main__':
    scrape_faculty_notices()
