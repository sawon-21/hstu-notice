import requests

url = "https://hstu.ac.bd/page/notice_all"

headers = {
    "User-Agent": "Mozilla/5.0"
}

r = requests.get(url, headers=headers, timeout=30)

print("Status:", r.status_code)
print("Final URL:", r.url)
print("Content-Type:", r.headers.get("content-type"))

with open("page.html", "w", encoding="utf-8") as f:
    f.write(r.text)

print("Saved page.html")
