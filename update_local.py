import re

with open('local.py', 'r') as f:
    content = f.read()

# Replace the scrape function with proper page detection and stop button
old_scrape = '''def scrape_google_scholar(query, num_papers):
    results = []
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-tools")
        options.add_argument("--user-data-dir=/tmp/chrome_profile")

        driver = webdriver.Chrome(options=options)
        url = f"https://scholar.google.com/scholar?q={quote(query)}&num={num_papers}"
        st.info(f"📍 Searching Google Scholar for: {query}")
        driver.get(url)

        time.sleep(15)'''

new_scrape = '''def scrape_google_scholar(query, num_papers):
    results = []
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-tools")
        options.add_argument("--user-data-dir=/tmp/chrome_profile")

        driver = webdriver.Chrome(options=options)
        url = f"https://scholar.google.com/scholar?q={quote(query)}&num={num_papers}"
        st.info(f"📍 Searching Google Scholar for: {query}")
        driver.get(url)

        # Wait for page to load (check for results or CAPTCHA)
        st.info("⏳ Waiting for Google Scholar to load...")
        page_loaded = False
        for i in range(30):
            try:
                results_container = driver.find_elements(By.CSS_SELECTOR, "div.gs_ri")
                if results_container:
                    page_loaded = True
                    st.success("✅ Page loaded!")
                    break
            except:
                pass
            time.sleep(1)
        
        if not page_loaded:
            st.warning("⚠️ Page took too long to load")</parameter>
            driver.quit()
            return []'''

content = content.replace(old_scrape, new_scrape)

with open('local.py', 'w') as f:
    f.write(content)

print("✅ local.py updated with page load detection!")
