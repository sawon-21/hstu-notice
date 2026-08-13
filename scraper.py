import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime


URL = "https://hstu.ac.bd/page/notice_all"

headers = {
    "User-Agent": "Mozilla/5.0"
}


def get_category(text):
    text = text.lower()

    if "cse" in text or "computer" in text:
        return "CSE"

    if "sastc" in text:
        return "SASTC"

    if "bba" in text or "business" in text:
        return "BBA"

    if "agri" in text or "agriculture" in text:
        return "Agriculture"

    return "General"



def scrape():

    r = requests.get(
        URL,
        headers=headers,
        timeout=30
    )

    print("Status:", r.status_code)

    soup = BeautifulSoup(
        r.text,
        "lxml"
    )


    notices = []


    items = soup.select(
        "li.related_post_sec.single_post"
    )


    print("Found:", len(items))


    for item in items:

        title_tag = item.select_one(
            "h5.note"
        )

        date_tag = item.select_one(
            "span.date"
        )

        dept_tag = item.select_one(
            "span.event-time"
        )

        link_tag = item.select_one(
            "a.btn-success"
        )


        if not title_tag:
            continue


        title = title_tag.get_text(
            strip=True
        )


        date = (
            date_tag.get_text(strip=True)
            if date_tag else ""
        )


        department = (
            dept_tag.get_text(strip=True)
            if dept_tag else ""
        )


        link = (
            link_tag.get("href")
            if link_tag else ""
        )


        if link and link.startswith("/"):
            link = "https://hstu.ac.bd" + link


        category = get_category(
            title + " " + department
        )


        notices.append({

            "title": title,

            "date": date,

            "department": department,

            "category": category,

            "url": link

        })



    data = {

        "updated":

        datetime.now().isoformat(),

        "total":

        len(notices),

        "notices":

        notices

    }


    with open(
        "notices.json",
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )


    print(
        "Saved notices.json"
    )



if __name__ == "__main__":
    scrape()
