import json
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://hstu.ac.bd"
URL = f"{BASE_URL}/page/exam_result"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/138.0 Safari/537.36"
    )
}


def clean(text):
    if not text:
        return ""
    return " ".join(text.split())


def scrape():
    response = requests.get(URL, headers=HEADERS, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    results = []
    seen = set()

    for item in soup.select("li.related_post_sec.single_post"):

        title_el = item.select_one("h6.note a")
        if not title_el:
            continue

        title = clean(title_el.get_text())

        pdf = title_el.get("href", "")
        pdf = urljoin(BASE_URL, pdf)

        date = ""
        date_el = item.select_one("span.date")
        if date_el:
            date = clean(date_el.get_text(" ", strip=True))

        time = ""
        time_el = item.select_one(".event-time")
        if time_el:
            time = clean(time_el.get_text())

        key = (title, pdf)

        if key in seen:
            continue

        seen.add(key)

        results.append({
            "title": title,
            "date": date,
            "time": time,
            "pdf": pdf
        })

    with open("results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"✅ Saved {len(results)} results to results.json")


if __name__ == "__main__":
    scrape()
