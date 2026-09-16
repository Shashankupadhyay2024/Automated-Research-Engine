# 🔍 Atlas Research Engine

Professional research paper search application with two versions: LOCAL (Selenium + Chrome) and WEB (Semantic Scholar API).

## 📋 Installation

```bash
# Install dependencies
pip install streamlit selenium beautifulsoup4 requests pandas reportlab webdriver-manager

# For LOCAL version, ensure Chrome is installed on your system
# Mac: brew install google-chrome
# Linux: sudo apt-get install google-chrome-stable
# Windows: Download from google.com/chrome
```

## 🚀 Quick Start

### LOCAL Version (Desktop with Real Chrome Browser)
```bash
streamlit run local.py
```
**Features:**
- Opens real Chrome browser for searching
- Direct access to Google Scholar
- Requires Chrome installed locally
- Shows search in progress in browser window

### WEB Version (Cloud-Ready for Render)
```bash
streamlit run web.py
```
**Features:**
- Uses Semantic Scholar API (no rate limiting)
- Works on cloud platforms like Render
- Reliable, consistent results
- No bot detection issues

## ✨ Features (Both Versions)

✅ **Credibility Scoring** - Papers ranked 0-100 based on:
  - Citation count
  - Publication year (recent papers higher)
  - Abstract quality
  - Publication venue

✅ **Search History** - Click previous searches to restore results instantly

✅ **Citation Formats** - Copy-paste ready citations in:
  - APA
  - MLA
  - Chicago
  - BibTeX

✅ **Export Options:**
  - PDF with formatted papers and copyright footer
  - JSON for data analysis
  - CSV for spreadsheets

✅ **Adjustable Search** - Request 5-100 papers per search

✅ **Professional UI** - Dark theme with gradient styling

## 📝 Copyright Footer

Both versions include: `© 2025 Shashank Upadhyay`

## 🔧 Troubleshooting

### LOCAL Version Shows reCAPTCHA
- Google Scholar may ask to verify you're human
- Solution: Complete the CAPTCHA in the Chrome window
- Refresh the Streamlit page after completing

### WEB Version Returns No Results
- Check internet connection
- Verify query is spelled correctly
- Semantic Scholar API may be temporarily down (rare)

### Chrome Driver Issues (LOCAL)
- Ensure Chrome is installed: `google-chrome --version` (Linux/Mac) or check Control Panel (Windows)
- Clear Chrome profile: `rm -rf /tmp/chrome_profile`
- Restart Streamlit: `streamlit run local.py`

## 📊 API Details

**WEB Version:**
- Uses: https://api.semanticscholar.org (free API)
- No authentication required
- No rate limiting for academic queries
- Includes: title, authors, abstract, citations, venue, year

**LOCAL Version:**
- Uses: Google Scholar (google.com/scholar)
- Requires Chrome browser
- May trigger reCAPTCHA on heavy use

## 🎯 Recommended Usage

- **Development/Presentation:** Use LOCAL (real Chrome, interactive)
- **Production/Cloud:** Use WEB (Semantic Scholar API, reliable)
- **Heavy Academic Work:** WEB version (unlimited queries)
- **Desktop Only:** LOCAL version (Chrome must be installed)

---

**Version:** 2.0 | **Status:** Production Ready
