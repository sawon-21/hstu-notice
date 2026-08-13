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

SOURCES = [
    {"category": "CSE", "url": "https://hstu.ac.bd/page/all_notice/type/f/id/2"},
    {"category": "Agriculture", "url": "https://hstu.ac.bd/page/all_notice/type/f/id/4"},
    {"category": "BBA", "url": "https://hstu.ac.bd/page/all_notice/type/f/id/3"}
]

def extract_direct_pdf(session, notice_url):
    """Fetches notice detail page to find direct PDF/file link if available."""
    if notice_url.lower().endswith('.pdf'):
        return notice_url
    
    try:
        res = session.get(notice_url, timeout=12, verify=False)
        if res.status_code == 200:
            sub_soup = BeautifulSoup(res.text, 'html.parser')
            
            # Check iframe, embed, object
            for tag in sub_soup.find_all(['iframe', 'embed', 'object']):
                src = tag.get('src') or tag.get('data') or ''
                src = src.strip()
                if src and any(k in src.lower() for k in ['.pdf', 'drive.google.com', 'notice', 'uploads', 'files', 'download']):
                    if not src.startswith('http'):
                        src = f"https://hstu.ac.bd{'' if src.startswith('/') else '/'}{src}"
                    return src
            
            # Check anchors inside detail page
            for a in sub_soup.find_all('a', href=True):
                href = a['href'].strip()
                href_lower = href.lower()
                text_lower = a.text.strip().lower()
                
                if any(ext in href_lower for ext in ['.pdf', 'notice_file', 'uploads', 'files', 'drive.google.com']) or \
                   any(kw in text_lower for kw in ['download', 'pdf', 'attachment', 'ডাউনলোড']):
                    if not href.startswith('http'):
                        href = f"https://hstu.ac.bd{'' if href.startswith('/') else '/'}{href}"
                    return href
    except Exception as e:
        print(f"Error resolving detail link {notice_url}: {e}")
        
    return notice_url

def scrape_faculty_notices():
    session = get_session()
    all_notices = []

    for source in SOURCES:
        category = source["category"]
        url = source["url"]
        print(f"Scraping {category} from {url}...")
        
        try:
            response = session.get(url, timeout=25, verify=False)
            if response.status_code != 200:
                print(f"Failed to load {url}, status code: {response.status_code}")
                continue

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

                    # Skip invalid titles or self-referencing list links
                    if not title or len(title) < 3 or 'all_notice' in link.lower():
                        continue
                    
                    if not link.startswith('http'):
                        link = f"https://hstu.ac.bd{'' if link.startswith('/') else '/'}{link}"
                    
                    # Extract date
                    date = "N/A"
                    for col in cols:
                        text = col.text.strip()
                        if any(char.isdigit() for char in text) and ('-' in text or '/' in text or ',' in text or '202' in text or '201' in text):
                            date = text
                            break

                    # Get direct PDF/file link from detail page
                    pdf_link = extract_direct_pdf(session, link)
                    
                    all_notices.append({
                        "category": category,
                        "title": title,
                        "date": date,
                        "link": pdf_link
                    })
                    
                    count += 1
                    if count >= 20: # Limit per faculty
                        break

        except Exception as e:
            print(f"Error scraping {category}: {e}")

    # Deduplicate
    unique_notices = []
    seen = set()
    for n in all_notices:
        key = (n['title'], n['link'])
        if key not in seen:
            seen.add(key)
            unique_notices.append(n)

    if unique_notices:
        with open('notices.json', 'w', encoding='utf-8') as f:
            json.dump(unique_notices, f, ensure_ascii=False, indent=4)
        print(f"Saved {len(unique_notices)} notices to notices.json")
    else:
        print("No notices scraped. Keeping existing notices.json")

if __name__ == '__main__':
    scrape_faculty_notices()
