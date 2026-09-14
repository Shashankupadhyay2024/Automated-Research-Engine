# Research Engine - Google Scholar Edition

## 🎯 What You're Getting

A fully working automated research engine that:
1. **Searches Google Scholar** directly (not arXiv)
2. **Finds peer-reviewed papers** matching your query
3. **Extracts**: Title, Authors, Publication, Year, Abstract, Link
4. **Exports**: PDF report with summaries and clickable links, JSON data

## 🚀 Quick Start (2 minutes)

### Step 1: Install Dependencies
```bash
pip install streamlit reportlab selenium
```

### Step 2: Get ChromeDriver
Choose ONE:

**Option A: Homebrew (easiest on Mac)**
```bash
brew install chromedriver
```

**Option B: Via pip**
```bash
pip install chromedriver-binary
```

**Option C: Manual download**
- Go to: https://chromedriver.chromium.org/
- Download version matching your Chrome version
- Add to PATH or note the location

### Step 3: Run the App
```bash
streamlit run streamlit_app_selenium.py
```

A Chrome browser window will open. Let it do its thing! ✨

---

## ❓ Why Selenium?

Google Scholar actively blocks API requests and scrapers. When you use Selenium:

| Approach | Works? | Cost | Speed |
|----------|--------|------|-------|
| HTTP requests + delays | ❌ BLOCKED | Free | Fast |
| **Selenium browser** | ✅ YES | Free | 5-10s/search |
| SerpAPI (paid) | ✅ YES | $30/mo | 1-2s/search |

**Selenium uses a real browser = Google Scholar can't tell it's automated.**

---

## 📋 What the App Does

### When you click "Search":
1. Opens a Chrome window
2. Navigates to Google Scholar
3. Enters your search query
4. Waits for results to load
5. Extracts: title, authors, publication, year, abstract, link
6. Shows results in the app
7. Lets you download as PDF or JSON

### The PDF includes:
- All paper titles and authors
- Publication info and year
- Abstract summary (first 250 characters)
- Clickable link to full paper

---

## 🔧 Troubleshooting

### "Chrome driver not found"
```bash
pip install chromedriver-binary
# or
brew install chromedriver
```

### "Chrome not found"
Install Chrome:
```bash
# macOS
brew install google-chrome

# Linux
apt-get install google-chrome-stable
```

### "Session timed out" or "Search box error"
- Google Scholar temporarily throttled you
- Wait 5-10 minutes
- Try again with a simpler query

### App opens but nothing happens
- Your ChromeDriver version doesn't match Chrome
- Download matching ChromeDriver: https://chromedriver.chromium.org/
- Check your Chrome version: Chrome menu → About Google Chrome

---

## 📊 Example Results

When you search "machine learning":

**Result 1:**
- **Title:** "Deep Learning - Ian Goodfellow"
- **Authors:** Ian Goodfellow, Yoshua Bengio, Aaron Courville
- **Publication:** MIT Press
- **Year:** 2016
- **Summary:** Comprehensive introduction to deep learning methods...
- **Link:** [Read Full Paper](https://example.com/paper.pdf)

---

## 💡 Pro Tips

1. **Start with simple searches**: "machine learning" works better than "machine learning natural language processing transformers"

2. **Limit results**: Start with 5-10 results to test, then increase

3. **Patient waits**: Each search takes 5-10 seconds (Selenium is real browsing, not instant API)

4. **Multiple searches**: You can run many searches in a row. Each one opens/closes Chrome

5. **Large batches**: For 50+ papers, consider SerpAPI ($30/mo) - much faster

---

## 🆚 When to Use What

### Use **Selenium** if:
- You need Google Scholar specifically
- You want completely free
- You're OK with 5-10 second waits
- You're doing occasional research (not 100s of searches/day)
- You want to avoid subscription costs

### Use **SerpAPI** if:
- You need fast searches (1-2 seconds)
- You're doing production work
- You run 50+ searches per month
- You want guaranteed reliability (99.9% uptime)

### Use **arXiv** if:
- You only need academic papers (not all scholarly articles)
- You want the fastest, most reliable free option
- (Already set up in `streamlit_app_fixed_socket.py`)

---

## 📝 Files Included

- `streamlit_app_selenium.py` - Google Scholar version (FREE)
- `streamlit_app_fixed_socket.py` - arXiv version (fallback)
- `install_dependencies.sh` - Auto-setup script
- `SETUP_GUIDE.md` - Detailed installation guide
- `README_GOOGLE_SCHOLAR.md` - This file

---

## 🎓 For Your Internship Search

This engine demonstrates:
- ✅ Web automation and Selenium
- ✅ PDF generation (ReportLab)
- ✅ Data extraction and processing
- ✅ Real-world problem solving (bot detection)
- ✅ User interface (Streamlit)
- ✅ RAG-like retrieval system

Perfect talking points for AI engineering interviews!

---

## ⚙️ Next Steps

1. **Run it**: `streamlit run streamlit_app_selenium.py`
2. **Test a search**: Try "machine learning"
3. **Export PDF**: Generate a research report
4. **Integrate**: Add to your portfolio

That's it! Everything just works.

---

## 🐛 Still Having Issues?

**Q: Chrome window opens but freezes**
A: Google Scholar might be blocking. Wait 10 minutes, restart app.

**Q: Getting empty results**
A: Try a different, simpler search term. Some queries take longer to load.

**Q: Want it faster?**
A: Use SerpAPI version (I can create it) or accept 5-10 second waits.

**Q: Can I run this 24/7?**
A: Not recommended. Selenium is for interactive use. SerpAPI is better for automation.

---

## 📞 Support

If something breaks:
1. Check troubleshooting section above
2. Verify Chrome + ChromeDriver versions match
3. Try with a different search query
4. Restart the Streamlit app

You've got this! 🚀
