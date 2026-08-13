import json
import requests
import urllib3
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_session():
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Referer': 'https://hstu.ac.bd/'
    })
    return session

SOURCES = [
    {"category": "CSE", "url": "https://hstu.ac.bd/page/all_notice/type/f/id/2"},
    {"category": "Agriculture", "url": "https://hstu.ac.bd/page/all_notice/type/f/id/4"},
    {"category": "BBA", "url": "https://hstu.ac.bd/page/all_notice/type/f/id/3"}
]

def get_direct_file_url(session, url):
    """নোটিশ ডিটেইলস পেজ থেকে সরাসরি PDF বা ফাইল লিংক বের করবে"""
    if not url:
        return ""
    
    url_lower = url.lower()
    if url_lower.endswith('.pdf') or '/uploads/' in url_lower or 'notice_file' in url_lower:
        return url

    try:
        res = session.get(url, timeout=12, verify=False)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # ১. iframe, embed, object ট্যাগে PDF লিংক খোজা
            for tag in soup.find_all(['iframe', 'embed', 'object']):
                src = tag.get('src') or tag.get('data') or ''
                src = src.strip()
                if src and any(ext in src.lower() for ext in ['.pdf', 'drive.google.com', 'uploads', 'notice_file', 'files', 'download']):
                    if not src.startswith('http'):
                        src = f"https://hstu.ac.bd{'' if src.startswith('/') else '/'}{src}"
                    return src

            # ২. <a> ট্যাগে সরাসরি ডাউনলোড লিংক খোজা
            for a in soup.find_all('a', href=True):
                href = a['href'].strip()
                href_lower = href.lower()
                text_lower = a.text.strip().lower()
                
                if any(ext in href_lower for ext in ['.pdf', 'uploads', 'notice_file', 'files', 'drive.google.com']) or \
                   any(kw in text_lower for kw in ['download', 'pdf', 'attachment', 'ডাউনলোড', 'file']):
                    if not href.startswith('http'):
                        href = f"https://hstu.ac.bd{'' if href.startswith('/') else '/'}{href}"
                    return href
    except Exception as e:
        print(f"Error fetching detail page {url}: {e}")

    return url

def scrape_faculty_notices():
    session = get_session()
    all_notices = []

    for source in SOURCES:
        category = source["category"]
        url = source["url"]
        print(f"Fetching {category} notices from: {url}")
        
        try:
            response = session.get(url, timeout=25, verify=False)
            if response.status_code != 200:
                print(f"Failed status code {response.status_code} for {url}")
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
                    raw_link = a_tag['href'].strip()

                    if not title or len(title) < 3 or 'all_notice' in raw_link.lower():
                        continue
                    
                    if not raw_link.startswith('http'):
                        full_link = f"https://hstu.ac.bd{'' if raw_link.startswith('/') else '/'}{raw_link}"
                    else:
                        full_link = raw_link

                    # তারিখ এক্সট্র্যাক্ট করা
                    date = "N/A"
                    for col in cols:
                        text = col.text.strip()
                        if any(char.isdigit() for char in text) and any(sep in text for sep in ['-', '/', ',', '202', '201']):
                            date = text
                            break

                    # সরাসরি PDF বা ফাইলের লিংক নেওয়া
                    direct_link = get_direct_file_url(session, full_link)

                    all_notices.append({
                        "category": category,
                        "title": title,
                        "date": date,
                        "link": direct_link
                    })
                    
                    count += 1
                    if count >= 20: # প্রতি ক্যাটাগরি থেকে ২০টি করে নোটিশ
                        break

        except Exception as e:
            print(f"Error scraping {category}: {e}")

    # ডুপ্লিকেট নোটিশ ফিল্টার
    unique_notices = []
    seen = set()
    for item in all_notices:
        key = (item['title'], item['link'])
        if key not in seen:
            seen.add(key)
            unique_notices.append(item)

    if unique_notices:
        with open('notices.json', 'w', encoding='utf-8') as f:
            json.dump(unique_notices, f, ensure_ascii=False, indent=4)
        print(f"Successfully saved {len(unique_notices)} direct notices to notices.json.")
    else:
        print("No notices collected. notices.json not overwritten.")

if __name__ == '__main__':
    scrape_faculty_notices()
