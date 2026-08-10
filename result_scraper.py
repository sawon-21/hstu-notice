import json
import requests
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

EXAM_RESULT_URL = "https://hstu.ac.bd/page/exam_result"

def scrape_exam_results():
    results = []

    try:
        response = requests.get(EXAM_RESULT_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')

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

                results.append({
                    "category": "Exam Result",
                    "title": title,
                    "date": date,
                    "link": link
                })

        with open('results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)

        print(f"Successfully scraped {len(results)} exam results.")

    except Exception as e:
        print(f"Error scraping exam results: {e}")

if __name__ == '__main__':
    scrape_exam_results()
