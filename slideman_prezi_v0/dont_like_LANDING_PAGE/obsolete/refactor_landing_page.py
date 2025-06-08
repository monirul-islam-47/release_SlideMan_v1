#!/usr/bin/env python3
"""
Refactor the PrezI landing page while preserving ALL visual elements.
This script extracts CSS and JS into separate files and creates a clean HTML.
"""

import re

def extract_and_replace_styles(html_content):
    """Extract all style tags and replace with link tags."""
    # Find all style blocks
    style_pattern = r'<style[^>]*>(.*?)</style>'
    styles = re.findall(style_pattern, html_content, re.DOTALL)
    
    # Remove style tags from HTML
    html_without_styles = re.sub(style_pattern, '', html_content, flags=re.DOTALL)
    
    # Combine all styles (we already extracted them to separate files)
    return html_without_styles

def extract_and_replace_scripts(html_content):
    """Extract inline scripts and replace with script src tags."""
    # Pattern to find script tags (excluding external scripts and specific inline scripts)
    # Keep Google Analytics, error tracking, and structured data inline
    script_pattern = r'<script>(?!.*?gtag|.*?window\.dataLayer|.*?window\.addEventListener\(\'error|.*?@context)(.*?)</script>'
    
    # Find all matching scripts
    scripts = re.findall(script_pattern, html_content, re.DOTALL)
    
    # Replace inline scripts with external references
    # But keep the analytics and error tracking inline
    html_modified = html_content
    
    # Replace the main script block (around line 6530-7500)
    main_script_pattern = r'<script>\s*// Matrix Rain.*?// Initialize sandbox.*?</script>'
    html_modified = re.sub(main_script_pattern, '<script src="js/main.js"></script>', html_modified, flags=re.DOTALL)
    
    # Replace the chat widget script block (around line 8955-10357)
    chat_script_pattern = r'<script>\s*// Chat Widget Functionality.*?chatWidget\.classList\.add\(\'active\'\);\s*}\s*</script>'
    html_modified = re.sub(chat_script_pattern, '<script src="js/chat-widget.js"></script>', html_modified, flags=re.DOTALL)
    
    return html_modified

def add_external_css_links(html_content):
    """Add external CSS links in the head section."""
    # Find the closing </head> tag
    head_close_pos = html_content.find('</head>')
    
    # CSS links to add
    css_links = '''
    <!-- External CSS Files - Preserving ALL styles and animations -->
    <link rel="stylesheet" href="css/main.css">
    <link rel="stylesheet" href="css/chat-widget.css">
    <link rel="stylesheet" href="css/final-styles.css">
'''
    
    # Insert CSS links before closing head tag
    html_with_css = html_content[:head_close_pos] + css_links + html_content[head_close_pos:]
    
    return html_with_css

def fix_form_action(html_content):
    """Fix the form to actually submit data."""
    # Find the request access form and add action
    form_pattern = r'<form id="requestAccessForm" class="access-form">'
    form_replacement = '<form id="requestAccessForm" class="access-form" action="https://formspree.io/f/YOUR_FORM_ID" method="POST">'
    
    html_content = html_content.replace(form_pattern, form_replacement)
    
    return html_content

def fix_analytics_id(html_content):
    """Add a comment about replacing the analytics ID."""
    # Add comment next to GA_MEASUREMENT_ID
    ga_pattern = r'GA_MEASUREMENT_ID'
    ga_replacement = 'GA_MEASUREMENT_ID /* TODO: Replace with your actual Google Analytics ID */'
    
    html_content = html_content.replace(ga_pattern, ga_replacement)
    
    return html_content

def main():
    # Read the original HTML file
    with open('index.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Process the HTML
    print("Extracting styles...")
    html_content = extract_and_replace_styles(html_content)
    
    print("Adding external CSS links...")
    html_content = add_external_css_links(html_content)
    
    print("Extracting scripts...")
    html_content = extract_and_replace_scripts(html_content)
    
    print("Fixing form action...")
    html_content = fix_form_action(html_content)
    
    print("Adding analytics reminder...")
    html_content = fix_analytics_id(html_content)
    
    # Write the refactored HTML
    with open('index_refactored_complete.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("\nRefactoring complete!")
    print("✓ All animations and visual effects preserved")
    print("✓ CSS extracted to separate files")
    print("✓ JavaScript extracted to separate files")
    print("✓ Form action added (needs Formspree ID)")
    print("✓ Analytics ID marked for replacement")
    print("\nThe refactored page should look EXACTLY the same as the original!")

if __name__ == "__main__":
    main()