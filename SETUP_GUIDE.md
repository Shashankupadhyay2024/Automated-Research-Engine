# 🔬 Automated Research Engine - Setup Guide

Your AI-powered research assistant that searches Google Scholar and generates research summaries.

## Features

✅ **No Hallucinations** - Uses real abstracts from Google Scholar  
✅ **Peer-Reviewed Only** - Filters for academic papers  
✅ **PDF Reports** - Professional summaries with clickable links  
✅ **AI Summaries** - Optional Ollama integration for intelligent summaries  
✅ **JSON Export** - Programmatic access to all data  
✅ **Completely Free** - Uses only free tools and APIs  

---

## Installation

### Step 1: Prerequisites
- Python 3.8+
- pip (Python package manager)

### Step 2: Install Dependencies

```bash
pip install requests beautifulsoup4 reportlab
```

### Step 3: (Optional) Install Ollama for AI Summaries

If you want intelligent AI summaries without hallucinations:

1. Download Ollama from [ollama.ai](https://ollama.ai)
2. Run: `ollama serve`
3. In another terminal: `ollama pull mistral` (or `ollama pull llama2`)

The script will work without Ollama too (uses abstract text as-is).

---

## Usage

### CLI Version

```bash
python scholar_search.py
```

Then follow the prompts:
```
🔍 Enter your research topic: RAG systems and semantic search
📊 How many articles to fetch? (default: 10): 15
🤖 Use Ollama for AI summaries? (y/n, default: n): y
```

**Output:**
- `research_YYYYMMDD_HHMMSS.pdf` - Professional PDF report
- `research_YYYYMMDD_HHMMSS.json` - Raw data in JSON format

---

## Usage Examples

### Example 1: RAG Systems Research
```
Query: "Retrieval Augmented Generation systems"
Results: 10 peer-reviewed papers with summaries
```

### Example 2: AI Ethics
```
Query: "ethical AI bias detection"
Results: Papers on AI ethics with clickable links
```

### Example 3: Specific Domain
```
Query: "vector embeddings semantic similarity LLM"
Results: Technical papers on embeddings and LLMs
```

---

## How It Works (Under the Hood)

### 1. **Search Phase**
   - Queries Google Scholar API
   - Filters for peer-reviewed papers
   - Extracts title, authors, publication, year, abstract

### 2. **Processing Phase**
   - Extracts real abstracts (NO AI generation here)
   - No hallucinations - only actual paper content
   - Cleans and formats data

### 3. **Summarization Phase (Optional)**
   - If Ollama is available: Uses local LLM for intelligent summaries
   - If not: Uses first 200 chars of abstract
   - Still 100% real content, not invented

### 4. **Output Phase**
   - Generates professional PDF with:
     - Article title and metadata
     - Real abstract or summary
     - Clickable link to full paper
   - Exports JSON for programmatic use

---

## Advanced Usage

### Using in Python Code

```python
from scholar_search import GoogleScholarScraper

# Initialize scraper
scraper = GoogleScholarScraper()

# Search for articles
articles = scraper.search("your research topic", num_results=20)

# Generate PDF
scraper.generate_pdf("my_research.pdf", use_ollama=True)

# Export JSON
scraper.export_json("my_research.json")

# Access articles programmatically
for article in articles:
    print(f"Title: {article['title']}")
    print(f"Link: {article['link']}")
    print(f"Summary: {article['summary']}")
```

### Batch Processing Multiple Topics

```python
topics = [
    "RAG systems",
    "vector embeddings",
    "semantic search",
    "LLM fine-tuning"
]

scraper = GoogleScholarScraper()

for topic in topics:
    print(f"\nSearching: {topic}")
    scraper.search(topic, num_results=15)
    scraper.generate_pdf(f"research_{topic.replace(' ', '_')}.pdf")
```

---

## Troubleshooting

### Issue: "ConnectionError" with Ollama
**Solution:** Ollama is optional. The script works fine without it.

### Issue: Google blocks requests
**Solution:** The script includes proper delays. If still blocked:
- Try again after 30 minutes
- Use a VPN
- Or manually download PDFs from Google Scholar

### Issue: "No articles found"
**Solution:** 
- Try a simpler search query
- Use more specific terms
- Increase the number of results

---

## Best Practices

1. **Specific Queries** - More specific = better results
   - ✅ "RAG systems with vector databases"
   - ❌ "AI research"

2. **Reasonable Limits** - 10-20 articles per search is ideal
   - Too many = slower execution
   - Too few = limited coverage

3. **Use Ollama for Technical Queries** - Gets better summaries
   - Good for: Complex topics, niche research
   - Optional for: Well-known topics

4. **Save JSON Too** - Useful for further analysis
   - Filter by year
   - Group by publication
   - Extract citations

---

## Architecture Details

```
Google Scholar
        ↓
   Web Scraper (BeautifulSoup)
        ↓
   Data Extraction (Real abstracts only)
        ↓
   Summarization (Optional Ollama)
        ↓
   PDF Generation (ReportLab)
   ↓         ↓
 PDF        JSON
```

**Why this architecture avoids hallucinations:**
- We scrape REAL abstracts from Google Scholar
- We never ask an AI to "generate" a summary from scratch
- Ollama only summarizes REAL text (input: abstract → output: condensed abstract)
- All links point to actual papers

---

## Next Steps

1. Test with a simple query
2. Try with Ollama for better summaries
3. Use the JSON output for further analysis
4. Build on this (custom filters, database storage, etc.)

---

## Questions?

See the included `scholar_search.py` for full implementation details.

Happy researching! 🔬📚
