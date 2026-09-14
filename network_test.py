#!/usr/bin/env python3
"""
Network diagnostic test for arXiv connectivity
Run this on your Mac to see if arXiv is reachable
"""

import socket
import sys

print("=" * 60)
print("NETWORK DIAGNOSTIC TEST")
print("=" * 60)

# Test 1: DNS Resolution
print("\n1️⃣  Testing DNS Resolution...")
try:
    ip = socket.gethostbyname("export.arxiv.org")
    print(f"   ✅ export.arxiv.org → {ip}")
except Exception as e:
    print(f"   ❌ Cannot resolve: {e}")
    sys.exit(1)

# Test 2: Basic HTTP Connection
print("\n2️⃣  Testing HTTP Connection...")
try:
    import urllib.request
    url = "http://export.arxiv.org/api/query?search_query=all:test&max_results=1"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as response:
        print(f"   ✅ HTTP Response: {response.status}")
except Exception as e:
    print(f"   ❌ HTTP Error: {e}")

# Test 3: HTTPS Connection
print("\n3️⃣  Testing HTTPS Connection...")
try:
    import urllib.request
    url = "https://export.arxiv.org/api/query?search_query=all:test&max_results=1"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as response:
        print(f"   ✅ HTTPS Response: {response.status}")
except Exception as e:
    print(f"   ❌ HTTPS Error: {e}")

# Test 4: Requests Library
print("\n4️⃣  Testing requests library...")
try:
    import requests
    url = "https://export.arxiv.org/api/query"
    params = {'search_query': 'all:test', 'max_results': 1}
    response = requests.get(url, params=params, timeout=10)
    print(f"   ✅ requests library: Status {response.status_code}")
    print(f"   📏 Response size: {len(response.text)} bytes")
except Exception as e:
    print(f"   ❌ requests Error: {e}")

print("\n" + "=" * 60)
print("If all tests pass, your network can reach arXiv!")
print("=" * 60)
