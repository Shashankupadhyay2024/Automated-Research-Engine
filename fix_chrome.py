with open('local.py', 'r') as f:
    content = f.read()

# Replace Chrome options with macOS-compatible version
old_options = '''        options = webdriver.ChromeOptions()
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--user-data-dir=/tmp/chrome_profile")
        
        driver = webdriver.Chrome(options=options)'''

new_options = '''        options = webdriver.ChromeOptions()
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--user-data-dir=/tmp/chrome_profile")
        options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        
        driver = webdriver.Chrome(options=options)'''

content = content.replace(old_options, new_options)

with open('local.py', 'w') as f:
    f.write(content)

print("✅ Chrome path fixed for macOS!")
