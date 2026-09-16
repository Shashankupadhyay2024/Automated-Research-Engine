with open('local.py', 'r') as f:
    lines = f.readlines()

# Find and replace the CAPTCHA detection section
new_lines = []
i = 0
while i < len(lines):
    if 'Check for reCAPTCHA' in lines[i]:
        # Replace the entire CAPTCHA handling block
        new_lines.append(lines[i])  # Keep the comment
        i += 1
        # Skip old code until we find the next try/except or main code
        while i < len(lines) and 'items = driver.find_elements' not in lines[i]:
            i += 1
        
        # Insert new CAPTCHA handling
        new_lines.append('        try:\n')
        new_lines.append('            recaptcha = driver.find_elements(By.CSS_SELECTOR, "[data-sitekey]")\n')
        new_lines.append('            if recaptcha:\n')
        new_lines.append('                st.warning("⚠️ reCAPTCHA detected. Solving in browser...")\n')
        new_lines.append('                st.info("⏳ Waiting up to 5 minutes for you to complete CAPTCHA...")\n')
        new_lines.append('                captcha_solved = False\n')
        new_lines.append('                for wait_sec in range(300):\n')
        new_lines.append('                    try:\n')
        new_lines.append('                        recaptcha = driver.find_elements(By.CSS_SELECTOR, "[data-sitekey]")\n')
        new_lines.append('                        if not recaptcha:\n')
        new_lines.append('                            captcha_solved = True\n')
        new_lines.append('                            st.success("✅ CAPTCHA completed!")\n')
        new_lines.append('                            time.sleep(2)\n')
        new_lines.append('                            break\n')
        new_lines.append('                    except:\n')
        new_lines.append('                        pass\n')
        new_lines.append('                    time.sleep(1)\n')
        new_lines.append('                if not captcha_solved:\n')
        new_lines.append('                    st.error("❌ CAPTCHA timeout. Try again.")\n')
        new_lines.append('                    driver.quit()\n')
        new_lines.append('                    return []\n')
        new_lines.append('        except:\n')
        new_lines.append('            pass\n')
        new_lines.append('\n')
    else:
        new_lines.append(lines[i])
        i += 1

with open('local.py', 'w') as f:
    f.writelines(new_lines)

print("✅ CAPTCHA handler updated - now waits 5 minutes for you to solve it!")
