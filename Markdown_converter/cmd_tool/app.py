''' import requests
from bs4 import BeautifulSoup
import re
import os
import markdownify
from pathlib import Path
import urllib.parse
import sys

# Base directory for attachments
ATTACHMENT_DIR = "attachments"

def sanitize_filename(filename):
    """Sanitizes the filename by removing invalid characters."""
    return re.sub(r'[<>:"/\\|?*]', '', filename)

def download_image(url, session):
    """Downloads an image and saves it in the attachments directory."""
    os.makedirs(ATTACHMENT_DIR, exist_ok=True)
    filename = sanitize_filename(url.split("/")[-1])
    filepath = os.path.join(ATTACHMENT_DIR, filename)

    if not os.path.exists(filepath):
        response = session.get(url)
        with open(filepath, "wb") as img_file:
            img_file.write(response.content)

    return filepath

def parse_tables(soup):
    """Converts tables into Markdown format."""
    for table in soup.find_all("table"):
        headers = [th.get_text(strip=True) for th in table.find_all("th")]
        rows = [
            [td.get_text(strip=True) for td in row.find_all("td")]
            for row in table.find_all("tr")
        ]

        md_table = "|" + "|".join(headers) + "|\n"
        md_table += "|" + "|".join("---" for _ in headers) + "|\n"
        for row in rows:
            if len(row) == len(headers):
                md_table += "|" + "|".join(row) + "|\n"

        table.replace_with(md_table)

def clean_wikipedia_content(soup):
    """Removes 'Edit' links from Wikipedia pages."""
    for edit_link in soup.select("span.mw-editsection"):
        edit_link.decompose()

def convert_to_markdown(url):
    """Main function to download page content, convert to markdown, and save with attachments."""
    session = requests.Session()
    response = session.get(url)
    if response.status_code != 200:
        raise Exception("Could not retrieve page")

    soup = BeautifulSoup(response.text, "html.parser")

    # Clean Wikipedia pages
    if "wikipedia.org" in url:
        clean_wikipedia_content(soup)

    # Parse and replace tables
    parse_tables(soup)

    # Convert main content to Markdown
    main_content = soup.find("main") or soup.find(id="bodyContent") or soup.body
    markdown_content = markdownify.markdownify(str(main_content), heading_style="ATX")

    # Replace and download image links
    def replace_img_tag(match):
        img_url = urllib.parse.urljoin(url, match.group(1))
        img_path = download_image(img_url, session)
        return f"![]({img_path})"

    markdown_content = re.sub(r'!\[.*?\]\((.*?)\)', replace_img_tag, markdown_content)

    # Save Markdown file
    filename = f"{sanitize_filename(url.split('/')[-1])}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    print(f"Markdown file saved as {filename}")

# Get URL from command line argument
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python markdown_converter.py <URL>")
    else:
        url = sys.argv[1]
        convert_to_markdown(url)
'''
import requests
from bs4 import BeautifulSoup
import re
import os
import markdownify
from pathlib import Path
import urllib.parse
import sys

# Base directory for attachments
ATTACHMENT_DIR = "attachments"

def sanitize_filename(filename):
    """Sanitizes the filename by removing invalid characters."""
    return re.sub(r'[<>:"/\\|?*]', '', filename)

def download_image(url, session):
    """Downloads an image and saves it in the attachments directory."""
    os.makedirs(ATTACHMENT_DIR, exist_ok=True)
    filename = sanitize_filename(url.split("/")[-1])
    filepath = os.path.join(ATTACHMENT_DIR, filename)

    # Only download if the file doesn't already exist
    if not os.path.exists(filepath):
        response = session.get(url, stream=True)
        if response.status_code == 200:
            with open(filepath, "wb") as img_file:
                for chunk in response.iter_content(1024):
                    img_file.write(chunk)

    # Return the relative path to the downloaded image for Markdown linking
    return os.path.join(ATTACHMENT_DIR, filename)

def parse_tables(soup):
    """Converts tables into Markdown format."""
    for table in soup.find_all("table"):
        headers = [th.get_text(strip=True) for th in table.find_all("th")]
        rows = [
            [td.get_text(strip=True) for td in row.find_all("td")]
            for row in table.find_all("tr")
        ]

        md_table = "|" + "|".join(headers) + "|\n"
        md_table += "|" + "|".join("---" for _ in headers) + "|\n"
        for row in rows:
            if len(row) == len(headers):
                md_table += "|" + "|".join(row) + "|\n"

        table.replace_with(md_table)

def clean_wikipedia_content(soup):
    """Removes 'Edit' links from Wikipedia pages."""
    for edit_link in soup.select("span.mw-editsection"):
        edit_link.decompose()

def convert_to_markdown(url):
    """Main function to download page content, convert to markdown, and save with attachments."""
    session = requests.Session()
    response = session.get(url)
    if response.status_code != 200:
        raise Exception("Could not retrieve page")

    soup = BeautifulSoup(response.text, "html.parser")

    # Clean Wikipedia pages
    if "wikipedia.org" in url:
        clean_wikipedia_content(soup)

    # Parse and replace tables
    parse_tables(soup)

    # Convert main content to Markdown
    main_content = soup.find("main") or soup.find(id="bodyContent") or soup.body
    markdown_content = markdownify.markdownify(str(main_content), heading_style="ATX")

    
    def replace_img_tag(match):
        img_url = urllib.parse.urljoin(url, match.group(1))
        img_path = download_image(img_url, session)
        # Convert the path to use forward slashes for Markdown compatibility
        return f"![]({img_path.replace(os.sep, '/')})"

    markdown_content = re.sub(r'!\[.*?\]\((.*?)\)', replace_img_tag, markdown_content)

    # Save Markdown file
    filename = f"{sanitize_filename(url.split('/')[-1])}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    print(f"Markdown file saved as {filename}")


def clean_markdown_output(markdown_content):
    # Replace multiple newlines with a single newline
    markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content)
    # Additional cleanup steps can be added here if necessary
    return markdown_content

# Get URL from command line argument
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python markdown_converter.py <URL>")
    else:
        url = sys.argv[1]
        convert_to_markdown(url)
