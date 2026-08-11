import json
import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

SOURCES = [
    {"category": "CSE", "url": "https://hstu.ac.bd/page/all_notice/type/f/id/2"},
    {"category": "Agriculture", "url": "https://hstu.ac.bd/page/all_notice/type/f/id/4"},
    {"category": "BBA", "url": "https://hstu.ac.bd/page/all_notice/type/f/id/3"}
]

def scrape_faculty_notices():
    all_notices = []

    for source in SOURCES:
        category = source["category"]
        url = source["url"]
        
        try:
            response = requests.get(url, headers=HEADERS, timeout=20, verify=False)
            response.raise_for_status()
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

                    link = a_tag['href']
                    if not link.startswith('http'):
                        link = f"https://hstu.ac.bd{'' if link.startswith('/') else '/'}{link}"

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
                        "link": link
                    })

        except Exception as e:
            print(f"Error scraping {category} from {url}: {e}")

    with open('notices.json', 'w', encoding='utf-8') as f:
        json.dump(all_notices, f, ensure_ascii=False, indent=4)

    print(f"Scraped {len(all_notices)} faculty notices.")

if __name__ == '__main__':
    scrape_faculty_notices()
