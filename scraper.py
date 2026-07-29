import requests

url = "https://hstu.ac.bd/page/notice_all"

headers = {
    "User-Agent": "Mozilla/5.0"
}

try:
    r = requests.get(url, headers=headers, timeout=30)

    print("Status:", r.status_code)

    with open("page.html", "w", encoding="utf-8") as f:
        f.write(r.text)

except Exception as e:
    print(e)
