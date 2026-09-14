# 🚀 Advanced Features & Customization

Extend your research engine with custom features!

---

## 1. Smart Caching

Cache results to avoid re-scraping:

```python
import json
from pathlib import Path

class CachedScraper(GoogleScholarScraper):
    def __init__(self, cache_dir="cache"):
        super().__init__()
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def get_cache_path(self, query):
        return self.cache_dir / f"{query.replace(' ', '_')}.json"

    def search(self, query, num_results=10, use_cache=True):
        cache_path = self.get_cache_path(query)

        # Return cached if exists
        if use_cache and cache_path.exists():
            with open(cache_path) as f:
                self.articles = json.load(f)
                print(f"✅ Loaded {len(self.articles)} articles from cache")
                return self.articles

        # Otherwise search fresh
        articles = super().search(query, num_results)

        # Save to cache
        with open(cache_path, 'w') as f:
            json.dump(articles, f)

        return articles
```

**Usage:**
```python
scraper = CachedScraper()

# First call - searches Google Scholar
scraper.search("RAG systems", use_cache=True)  # Fresh search

# Second call - loads from cache instantly
scraper.search("RAG systems", use_cache=True)  # From cache!
```

---

## 2. Year-Based Filtering

Only get recent papers:

```python
def filter_by_year(articles, min_year=2020):
    """Filter articles published after min_year"""
    return [
        a for a in articles 
        if a.get('year', 'Unknown') != 'Unknown' 
        and int(a['year']) >= min_year
    ]

# Usage
scraper = GoogleScholarScraper()
articles = scraper.search("machine learning", num_results=20)

recent_articles = filter_by_year(articles, min_year=2023)
print(f"Papers from 2023+: {len(recent_articles)}")
```

---

## 3. Keyword Extraction

Find key topics in abstracts:

```python
from collections import Counter

def extract_keywords(articles, top_n=10):
    """Extract most common keywords from abstracts"""
    stopwords = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'is', 'are', 'was', 'be', 'been', 'being'
    }

    words = []
    for article in articles:
        abstract = article.get('abstract', '').lower()
        # Extract words longer than 4 chars
        article_words = [
            w.strip(',.;:') 
            for w in abstract.split() 
            if len(w) > 4 and w.lower() not in stopwords
        ]
        words.extend(article_words)

    # Get most common
    return Counter(words).most_common(top_n)

# Usage
keywords = extract_keywords(articles)
print("\n🔑 Top Keywords:")
for keyword, count in keywords:
    print(f"  {keyword}: {count} mentions")
```

---

## 4. Citation Graph Analysis

Track which papers cite which:

```python
def build_citation_graph(articles):
    """Create a citation network"""
    graph = {}

    for article in articles:
        # Extract citations from abstract (simple heuristic)
        abstract = article.get('abstract', '')
        citations = [
            w for w in abstract.split() 
            if w[0].isupper() and len(w) > 2
        ]

        graph[article['title']] = {
            'authors': article['authors'],
            'year': article['year'],
            'potential_citations': citations[:5],  # First 5 capitalized words
            'link': article['link']
        }

    return graph

# Usage
graph = build_citation_graph(articles)
```

---

## 5. Batch Processing Multiple Topics

```python
import time

def batch_search(topics, num_results=10, delay=60):
    """Search multiple topics with delay between"""
    scraper = GoogleScholarScraper()
    all_results = {}

    for idx, topic in enumerate(topics, 1):
        print(f"\n[{idx}/{len(topics)}] Searching: {topic}")
        articles = scraper.search(topic, num_results)
        all_results[topic] = articles

        # Respectful delay
        if idx < len(topics):
            print(f"⏳ Waiting {delay}s before next search...")
            time.sleep(delay)

    return all_results

# Usage
topics = [
    "RAG systems",
    "vector embeddings",
    "semantic search",
    "LLM fine-tuning"
]

results = batch_search(topics, num_results=10, delay=120)

for topic, articles in results.items():
    print(f"\n{topic}: {len(articles)} papers found")
```

---

## 6. Database Integration

Store results in SQLite:

```python
import sqlite3
from datetime import datetime

def store_in_database(articles, db_file="research.db"):
    """Store articles in SQLite for analysis"""
    conn = sqlite3.connect(db_file)
    c = conn.cursor()

    # Create table
    c.execute('''CREATE TABLE IF NOT EXISTS articles
        (id INTEGER PRIMARY KEY,
         title TEXT,
         authors TEXT,
         publication TEXT,
         year INTEGER,
         abstract TEXT,
         link TEXT,
         date_added TIMESTAMP)''')

    # Insert articles
    for article in articles:
        c.execute('''INSERT INTO articles 
            (title, authors, publication, year, abstract, link, date_added)
            VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (article['title'],
             article['authors'],
             article['publication'],
             article.get('year', 'Unknown'),
             article['abstract'],
             article['link'],
             datetime.now()))

    conn.commit()
    conn.close()
    print(f"✅ Stored {len(articles)} articles in database")

# Usage
store_in_database(articles)

# Query later
conn = sqlite3.connect("research.db")
c = conn.cursor()
c.execute("SELECT title, year FROM articles WHERE year > 2022 ORDER BY year DESC")
recent_papers = c.fetchall()
```

---

## 7. Email Integration

Auto-send reports:

```python
import smtplib
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.encoders import encode_base64

def send_report_email(pdf_bytes, recipient_email, topic):
    """Send PDF report via email"""
    sender = "your-email@gmail.com"
    password = "your-app-password"

    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = recipient_email
    msg['Subject'] = f"Research Report: {topic}"

    body = f"""
    Hi,

    I've completed a research search on: {topic}

    Please find the report attached.

    All papers are peer-reviewed and links are provided.

    Best regards
    """

    msg.attach(MIMEText(body, 'plain'))

    # Attach PDF
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(pdf_bytes)
    encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename= research.pdf')
    msg.attach(part)

    # Send
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login(sender, password)
    server.sendmail(sender, recipient_email, msg.as_string())
    server.quit()

    print(f"✅ Report sent to {recipient_email}")

# Usage
scraper = GoogleScholarScraper()
articles = scraper.search("AI ethics", num_results=10)
pdf_data = scraper.generate_pdf()

send_report_email(pdf_data, "colleague@email.com", "AI ethics")
```

---

## 8. Custom Ranking

Rank papers by quality metrics:

```python
def rank_articles(articles):
    """Simple ranking based on available signals"""
    scored = []

    for article in articles:
        score = 0

        # Newer is better
        year = article.get('year', '2000')
        if year.isdigit():
            score += int(year) - 2000

        # Longer abstract = more detail
        abstract_len = len(article.get('abstract', ''))
        score += min(abstract_len // 100, 10)

        # Known journals/publishers get boost
        publication = article.get('publication', '').lower()
        if any(x in publication for x in ['nature', 'science', 'ieee']):
            score += 5

        scored.append((article, score))

    # Sort by score
    return sorted(scored, key=lambda x: x[1], reverse=True)

# Usage
ranked = rank_articles(articles)

print("\n🏆 Top Papers by Quality Score:")
for article, score in ranked[:5]:
    print(f"  [{score}] {article['title'][:60]}...")
```

---

## 9. Integration with Notion

Push results to Notion:

```python
import requests

def push_to_notion(articles, notion_token, database_id):
    """Add articles to Notion database"""
    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }

    for article in articles:
        data = {
            "parent": {"database_id": database_id},
            "properties": {
                "Title": {"title": [{"text": {"content": article['title']}}]},
                "Authors": {"rich_text": [{"text": {"content": article['authors']}}]},
                "Year": {"number": int(article['year']) if article['year'].isdigit() else 0},
                "Link": {"url": article['link']},
                "Summary": {"rich_text": [{"text": {"content": article['summary']}}]},
            }
        }

        requests.post("https://api.notion.com/v1/pages", json=data, headers=headers)

    print(f"✅ Pushed {len(articles)} articles to Notion")

# Usage (requires Notion API token & database ID)
# push_to_notion(articles, "your_token", "database_id")
```

---

## 10. Performance Optimization

### Parallel Searches
```python
from concurrent.futures import ThreadPoolExecutor

def parallel_search(topics, num_results=10):
    """Search multiple topics in parallel"""
    scraper = GoogleScholarScraper()
    results = {}

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(scraper.search, topic, num_results): topic
            for topic in topics
        }

        for future in futures:
            topic = futures[future]
            results[topic] = future.result()

    return results
```

### Smart Caching with TTL
```python
from time import time

class TTLCache:
    def __init__(self, ttl_seconds=3600):
        self.cache = {}
        self.ttl = ttl_seconds

    def get(self, key):
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time() - timestamp < self.ttl:
                return value
        return None

    def set(self, key, value):
        self.cache[key] = (value, time())
```

---

## Example: Full Advanced Pipeline

```python
# Combine everything!

scraper = GoogleScholarScraper()

# 1. Search with cache
articles = scraper.search("RAG systems", use_cache=True)

# 2. Filter by year
recent = filter_by_year(articles, min_year=2023)

# 3. Rank by quality
ranked = rank_articles(recent)

# 4. Extract keywords
keywords = extract_keywords(ranked)

# 5. Store in DB
store_in_database(ranked)

# 6. Generate PDF
pdf = scraper.generate_pdf()

# 7. Send email
send_report_email(pdf, "team@company.com", "RAG Systems")

# 8. Push to Notion (optional)
# push_to_notion(ranked, notion_token, db_id)

print(f"✅ Pipeline complete! {len(ranked)} papers processed")
```

---

## Tips for Production Use

1. **Rate Limiting** - Add delays between requests
2. **Error Handling** - Wrap in try/except
3. **Logging** - Track what's happening
4. **Validation** - Check data quality
5. **Backups** - Save results locally
6. **Monitoring** - Alert on failures

---

## Next Steps

- 📦 Package as Python library (`pip install research-engine`)
- 🐳 Containerize with Docker
- 🚀 Deploy as cloud service
- 📱 Create mobile app
- 🤖 Add more LLM models for summarization
- 🔗 Build knowledge graph from citations

---

Happy advancing! 🚀📚
