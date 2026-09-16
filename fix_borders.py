with open('local.py', 'r') as f:
    content = f.read()

# Add visual separator instead of border
old = '''            with st.container():
                col1, col2 = st.columns([5, 1])'''

new = '''            st.markdown("---")
            col1, col2 = st.columns([5, 1])'''

content = content.replace(old, new)

with open('local.py', 'w') as f:
    f.write(content)

print("✅ Fixed!")
