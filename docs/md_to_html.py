"""
Simple script to convert Markdown to HTML.
After running this script, open the HTML file in your browser and use print to save as PDF.
"""
import markdown
import os

# File paths
script_dir = os.path.dirname(os.path.abspath(__file__))
md_file = os.path.join(script_dir, "slideman_pitch.md")
html_file = os.path.join(script_dir, "slideman_pitch.html")

# Read markdown content
with open(md_file, 'r', encoding='utf-8') as f:
    md_content = f.read()

# Convert markdown to HTML
html_content = markdown.markdown(
    md_content,
    extensions=['markdown.extensions.extra', 'markdown.extensions.tables']
)

# Create a complete HTML document with some basic styling
complete_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Slideman Pitch</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 2em;
            max-width: 800px;
            margin-left: auto;
            margin-right: auto;
        }}
        h1, h2, h3, h4 {{
            color: #333;
            margin-top: 1.5em;
        }}
        h1 {{
            border-bottom: 1px solid #ccc;
            padding-bottom: 0.3em;
            font-size: 2.2em;
        }}
        h2 {{
            font-size: 1.8em;
            border-bottom: 1px solid #eee;
        }}
        h3 {{
            font-size: 1.5em;
        }}
        ul {{
            margin-bottom: 1.5em;
        }}
        li {{
            margin-bottom: 0.5em;
        }}
        strong {{
            color: #333;
        }}
        @media print {{
            body {{
                margin: 1cm;
                font-size: 12pt;
            }}
            h1 {{
                font-size: 20pt;
            }}
            h2 {{
                font-size: 16pt;
            }}
            h3 {{
                font-size: 14pt;
            }}
        }}
    </style>
</head>
<body>
    {html_content}
</body>
</html>
"""

# Save HTML
with open(html_file, 'w', encoding='utf-8') as f:
    f.write(complete_html)

print(f"Successfully created {html_file}")
print("To create a PDF:")
print("1. Open this HTML file in your browser")
print("2. Use the browser's print function (Ctrl+P)")
print("3. Select 'Save as PDF' as the destination")
print("4. Click Save")
