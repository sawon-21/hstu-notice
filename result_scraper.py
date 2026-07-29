import requests
from bs4 import BeautifulSoup
import json

url = "https://hstu.ac.bd/page/exam_result"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(url, headers=headers)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

results = []

# TODO: পরে selector অনুযায়ী data collect হবে

with open("results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("results.json created.")
