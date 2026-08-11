import json
import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Referer': 'https://hstu.ac.bd/'
}

EXAM_RESULT_URL = "https://hstu.ac.bd/page/exam_result"

def scrape_exam_results():
    results = []

    try:
        response = requests.get(EXAM_RESULT_URL, headers=HEADERS, timeout=25, verify=False)
        print(f"Fetching Exam Results: Status {response.status_code}")

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

                    link = a_tag['href']
                    if not link.startswith('http'):
                        link = f"https://hstu.ac.bd{'' if link.startswith('/') else '/'}{link}"

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
                        "link": link
                    })

    except Exception as e:
        print(f"Error scraping exam results: {e}")

    # SAFETY: Only overwrite JSON if new results were successfully found
    if results:
        with open('results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
        print(f"Successfully saved {len(results)} results to results.json.")
    else:
        print("WARNING: Scraping returned 0 exam results. Keeping existing results.json.")

if __name__ == '__main__':
    scrape_exam_results()
