from flask import Flask, render_template, request, jsonify, send_file
import requests
from bs4 import BeautifulSoup
import markdownify
import os
import time

app = Flask(__name__)
ATTACHMENTS_FOLDER = "attachments"

# Create attachments folder if not exists
if not os.path.exists(ATTACHMENTS_FOLDER):
    os.makedirs(ATTACHMENTS_FOLDER)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("url")
        if url:
            return start_conversion(url)
    
    return render_template("index.html")

@app.route("/start_conversion", methods=["POST"])
def start_conversion(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Extract main content
        main_content = extract_main_content(soup)
        if not main_content:
            return jsonify({"error": "Could not find main content on this page"}), 400

        # Convert HTML to Markdown
        markdown_content = html_to_markdown(str(main_content))

        # Download images and update links in Markdown
        markdown_content = download_assets_and_update_links(main_content, markdown_content)

        # Save Markdown content to a file
        output_folder = create_output_folder(url)
        output_path = os.path.join(output_folder, "converted_page.md")
        with open(output_path, "w") as file:
            file.write(markdown_content)

        return send_file(output_path, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def extract_main_content(soup):
    # Improved extraction of the main content
    main_content = soup.find('main') or soup.find('article')
    if not main_content:
        potential_divs = soup.find_all('div', class_='content')
        return potential_divs[0] if potential_divs else None
    return main_content

def html_to_markdown(html_content):
    return markdownify.markdownify(html_content, heading_style="ATX")

def normalize_url(base_url, src):
    if src.startswith("//"):
        return "https:" + src
    elif src.startswith("/"):
        return f"https://{base_url}{src}"
    return src

def download_assets_and_update_links(main_content, markdown_content):
    for asset_tag in main_content.find_all(['img', 'video', 'audio']):
        asset_url = asset_tag.get('src') or asset_tag.get('href')
        if asset_url:
            asset_url = normalize_url(request.host_url, asset_url)
            asset_path = download_asset(asset_url)
            if asset_path:
                markdown_content = markdown_content.replace(asset_url, asset_path)

    return markdown_content

def download_asset(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        filename = os.path.join(ATTACHMENTS_FOLDER, os.path.basename(url))
        with open(filename, "wb") as f:
            f.write(response.content)
        return f"{ATTACHMENTS_FOLDER}/{os.path.basename(url)}"
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return None

def create_output_folder(url):
    folder_name = url.split("//")[1].split("/")[0]  # Extract domain from URL
    timestamp = int(time.time())
    output_folder = os.path.join("converted", f"{folder_name}_{timestamp}")
    os.makedirs(output_folder, exist_ok=True)
    return output_folder

if __name__ == "__main__":
    app.run(debug=True)
