"""
Simple script to convert Markdown to PDF using WeasyPrint.
Usage: python md_to_pdf.py input.md output.pdf
"""
import sys
import markdown
from weasyprint import HTML, CSS
import os

def convert_md_to_pdf(md_file, pdf_file):
    # Read markdown content
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Convert markdown to HTML
    html_content = markdown.markdown(
        md_content,
        extensions=[
            'markdown.extensions.extra',
            'markdown.extensions.smarty',
            'markdown.extensions.tables',
        ]
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
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    # Convert HTML to PDF
    HTML(string=complete_html).write_pdf(pdf_file)
    
    print(f"Successfully converted {md_file} to {pdf_file}")

if __name__ == "__main__":
    if len(sys.argv) > 2:
        md_file = sys.argv[1]
        pdf_file = sys.argv[2]
    else:
        # Use default paths
        script_dir = os.path.dirname(os.path.abspath(__file__))
        md_file = os.path.join(script_dir, "slideman_pitch.md")
        pdf_file = os.path.join(script_dir, "slideman_pitch.pdf")
    
    convert_md_to_pdf(md_file, pdf_file)
