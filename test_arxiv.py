"""
Test script to debug arXiv API
"""

import requests
import feedparser

# Test 1: Basic arXiv API call
print("=" * 60)
print("TEST 1: Testing arXiv API directly")
print("=" * 60)

url = "http://export.arxiv.org/api/query"
params = {
    'search_query': 'all:machine learning',
    'start': 0,
    'max_results': 10
}

print(f"\n🔗 URL: {url}")
print(f"📝 Params: {params}\n")

try:
    response = requests.get(url, params=params, timeout=15)
    print(f"✅ Status Code: {response.status_code}")
    print(f"📏 Response Length: {len(response.text)} bytes\n")

    print("First 1000 chars of response:")
    print(response.text[:1000])
    print("\n")

    # Try to parse with feedparser
    feed = feedparser.parse(response.content)
    print(f"📄 Feedparser found {len(feed.entries)} entries")

    if feed.entries:
        print("\nFirst entry:")
        entry = feed.entries[0]
        print(f"  Title: {entry.title}")
        print(f"  Authors: {[a.name for a in entry.authors[:2]]}")
        if hasattr(entry, 'summary'):
            print(f"  Summary: {entry.summary[:200]}...")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Try different search query
print("\n" + "=" * 60)
print("TEST 2: Testing different query format")
print("=" * 60)

params2 = {
    'search_query': 'cat:cs.LG AND all:embedding',
    'start': 0,
    'max_results': 5
}

print(f"\n📝 Params: {params2}\n")

try:
    response = requests.get(url, params=params2, timeout=15)
    print(f"✅ Status Code: {response.status_code}")

    feed = feedparser.parse(response.content)
    print(f"📄 Found {len(feed.entries)} entries")

    if feed.entries:
        print(f"\nFirst result: {feed.entries[0].title[:80]}")
    else:
        print("❌ No entries found")

except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 60)
print("TESTS COMPLETE")
print("=" * 60)
