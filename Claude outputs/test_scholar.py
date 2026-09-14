"""
Test script to debug what Google Scholar is actually returning
"""

import requests
import random
from bs4 import BeautifulSoup

user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
]

headers = {
    'User-Agent': random.choice(user_agents),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

url = "https://scholar.google.com/scholar"
params = {
    'q': 'machine learning',
    'hl': 'en',
    'as_sdt': '1,5',
    'num': 10,
    'start': 0
}

print(f"🔍 Testing URL: {url}")
print(f"📝 Headers: {headers}")
print(f"🔎 Params: {params}\n")

try:
    response = requests.get(url, params=params, headers=headers, timeout=15)
    print(f"✅ Status Code: {response.status_code}")
    print(f"📏 Response Length: {len(response.text)} bytes\n")

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')

        # Check for common results
        results = soup.find_all('div', class_='gs_ri')
        print(f"📄 Found {len(results)} results with class 'gs_ri'")

        # Try alternative selectors
        alt_results = soup.find_all('div', class_='gs_r')
        print(f"📄 Found {len(alt_results)} results with class 'gs_r'")

        # Show HTML snippet
        print("\n📋 First 500 chars of response:")
        print(response.text[:500])

        # Check if we're getting blocked
        if "did not match any documents" in response.text:
            print("\n⚠️  Google Scholar returned no results (blocked or empty)")
        if "automated access" in response.text.lower():
            print("\n🚫 Detected automated access block!")
        if response.status_code == 403:
            print("\n🚫 HTTP 403 - Access Denied!")

    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text[:500])

except Exception as e:
    print(f"❌ Exception: {e}")
