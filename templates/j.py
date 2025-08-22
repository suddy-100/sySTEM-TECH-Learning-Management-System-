import os
import re

# Folder where your templates are stored
TEMPLATE_DIR = "templates"  # change if your templates folder has a different name

pattern = re.compile(r"url_for\(\s*['\"]invoicing['\"]\s*\)")

for root, dirs, files in os.walk(TEMPLATE_DIR):
    for file in files:
        if file.endswith(".html") or file.endswith(".htm"):
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                if pattern.search(content):
                    print(f"Found 'invoicing' in: {path}")
