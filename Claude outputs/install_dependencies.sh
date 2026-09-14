#!/bin/bash
set -e

echo "======================================"
echo "Research Engine Setup Script"
echo "======================================"

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python version: $python_version"

# Install core dependencies
echo ""
echo "📦 Installing core dependencies..."
pip install --upgrade pip streamlit reportlab selenium

# Check for ChromeDriver
echo ""
echo "🔍 Checking for ChromeDriver..."

if ! command -v chromedriver &> /dev/null; then
    echo "⚠️  ChromeDriver not found"
    echo ""
    echo "Install ChromeDriver:"
    echo "  macOS:  brew install chromedriver"
    echo "  Linux:  apt-get install chromium-chromedriver"
    echo "  Windows: Download from https://chromedriver.chromium.org/"
    echo ""
    echo "Or install via pip:"
    echo "  pip install chromedriver-binary"
else
    echo "✅ ChromeDriver found at: $(which chromedriver)"
fi

# Check for Chrome/Chromium
echo ""
echo "🔍 Checking for Chrome/Chromium..."

if command -v google-chrome &> /dev/null; then
    echo "✅ Chrome found"
elif command -v chromium &> /dev/null; then
    echo "✅ Chromium found"
elif command -v chromium-browser &> /dev/null; then
    echo "✅ Chromium found"
else
    echo "⚠️  Chrome/Chromium not found. Install:"
    echo "  macOS:  brew install google-chrome"
    echo "  Linux:  apt-get install chromium-browser"
fi

echo ""
echo "======================================"
echo "✅ Setup Complete!"
echo "======================================"
echo ""
echo "Run the app with:"
echo "  streamlit run streamlit_app_selenium.py"
echo ""
echo "Or if you want the arXiv version (more stable, different source):"
echo "  streamlit run streamlit_app_fixed_socket.py"
echo ""
