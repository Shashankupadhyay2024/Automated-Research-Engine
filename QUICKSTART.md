# 🚀 Quick Start Guide

Get your research engine running in 5 minutes!

---

## Option 1: CLI (Command Line)

### 1. Install Dependencies
```bash
pip install requests beautifulsoup4 reportlab
```

### 2. Run the Script
```bash
python scholar_search.py
```

### 3. Follow Prompts
```
🔍 Enter your research topic: RAG systems and semantic search
📊 How many articles to fetch? (default: 10): 15
🤖 Use Ollama for AI summaries? (y/n, default: n): n
```

### 4. Get Your PDF
✅ A professional PDF with all research summaries and links!

---

## Option 2: Streamlit Web App (Easier!)

### 1. Install Streamlit
```bash
pip install streamlit requests beautifulsoup4 reportlab
```

### 2. Run the App
```bash
streamlit run streamlit_app.py
```

### 3. Open in Browser
- Automatically opens http://localhost:8501
- Beautiful web interface
- Click "Search" button
- Download PDF or JSON

### 4. That's It!
✅ Web interface handles everything!

---

## Option 3: Add Ollama for Better Summaries (Optional)

### 1. Install Ollama
- Download from [ollama.ai](https://ollama.ai)
- Run: `ollama serve` (in one terminal)

### 2. Download a Model
```bash
ollama pull mistral
```
(or `ollama pull llama2`)

### 3. Use with Your Script
```bash
python scholar_search.py
# When asked "Use Ollama for AI summaries?" → Answer 'y'
```

---

## Example Searches

### 1. RAG Systems
```
Query: "Retrieval Augmented Generation with vector databases"
Results: 10-15 papers on RAG architecture
```

### 2. Semantic Search
```
Query: "semantic similarity embeddings natural language"
Results: Papers on embeddings and similarity search
```

### 3. AI Ethics
```
Query: "bias detection fairness machine learning"
Results: Papers on AI ethics and bias
```

---

## Output Files

After running a search:

### PDF Report (`research_YYYYMMDD_HHMMSS.pdf`)
```
📚 Automated Research Summary
═══════════════════════════════

1. [Article Title]
   Authors: ...
   Publication: ...
   Year: ...
   Summary: [2-3 sentence summary]
   📎 Read Full Paper [CLICKABLE LINK]

2. [Next Article]
   ...
```

### JSON Data (`research_YYYYMMDD_HHMMSS.json`)
```json
[
  {
    "title": "Article Title",
    "authors": "Author names",
    "publication": "Journal name",
    "year": "2024",
    "abstract": "Full abstract text...",
    "link": "https://scholar.google.com/...",
    "summary": "Summary text..."
  }
]
```

---

## Troubleshooting

### Issue: "No module named 'requests'"
```bash
pip install requests
```

### Issue: Google Scholar blocks requests
- Wait 30 minutes and try again
- Use a VPN
- It's a rate limiting issue - totally normal

### Issue: PDF not generating
```bash
pip install --upgrade reportlab
```

### Issue: Ollama not connecting
- Make sure you ran `ollama serve` in another terminal
- Script works fine without Ollama (just uses abstracts)

---

## Next Steps

1. **Try the Streamlit app** - More user-friendly
2. **Save your searches** - PDFs are permanent records
3. **Export JSON** - Analyze data further
4. **Batch search** - Search multiple topics
5. **Share reports** - Send PDFs to colleagues

---

## Key Features Recap

✅ **Real Data Only** - No AI hallucinations, real abstracts from papers  
✅ **Peer-Reviewed** - Filters for academic papers only  
✅ **Clickable Links** - Every article links to the full paper  
✅ **Free** - No API keys, no paid services  
✅ **Professional Output** - Beautiful PDFs ready to share  
✅ **Flexible** - Use CLI or web app  
✅ **Extensible** - JSON output for further analysis  

---

## Commands Reference

```bash
# Install dependencies
pip install requests beautifulsoup4 reportlab streamlit

# Run CLI tool
python scholar_search.py

# Run web app
streamlit run streamlit_app.py

# Install Ollama (optional)
ollama serve  # in one terminal
ollama pull mistral  # in another terminal
```

---

That's it! You're ready to automate your research! 🚀📚

**Questions?** Check `SETUP_GUIDE.md` for detailed documentation.
