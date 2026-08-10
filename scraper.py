import json
import requests
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# Configured faculty notice endpoints
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
            response = requests.get(url, headers=HEADERS, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'lxml')

            # Parse table rows for notices
            rows = soup.find_all('tr')
            for row in rows:
                a_tag = row.find('a', href=True)
                cols = row.find_all('td')

                if a_tag:
                    title = a_tag.text.strip()
                    link = a_tag['href']
                    if not link.startswith('http'):
                        link = f"https://hstu.ac.bd{'' if link.startswith('/') else '/'}{link}"

                    date = cols[0].text.strip() if cols else "N/A"

                    all_notices.append({
                        "category": category,
                        "title": title,
                        "date": date,
                        "link": link
                    })
        except Exception as e:
            print(f"Error scraping {category} from {url}: {e}")

    # Output merged notices to JSON
    with open('notices.json', 'w', encoding='utf-8') as f:
        json.dump(all_notices, f, ensure_ascii=False, indent=4)
    
    print(f"Successfully scraped {len(all_notices)} total faculty notices.")

if __name__ == '__main__':
    scrape_faculty_notices()
