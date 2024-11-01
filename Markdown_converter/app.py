from flask import Flask, render_template, request, send_file
import requests
from bs4 import BeautifulSoup
import markdownify
import os
from datetime import datetime
import urllib.parse
import re

app = Flask(__name__)
ATTACHMENTS_FOLDER = "attachments"
OUTPUT_FOLDER = "output_files"

# Create folders if they don't exist
os.makedirs(ATTACHMENTS_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("url")
        if url:
            # Fetch webpage content
            response = requests.get(url)
            soup = BeautifulSoup(response.content, "html.parser")

            # Extract main content (for Wikipedia, typically <div id="content">)
            main_content = soup.find(id="content") or soup.find("main") or soup.find("article")
            if not main_content:
                return "Could not find main content on this page", 400
            
            # Convert HTML to Markdown
            markdown_content = markdownify.markdownify(str(main_content))
            
            # Download images and update Markdown links
            markdown_content = download_images_and_update_links(main_content, markdown_content)

            # Generate a unique filename based on the URL and timestamp
            page_name = urllib.parse.urlparse(url).netloc.replace(".", "_")  # Replace dots to avoid filesystem issues
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{page_name}_{timestamp}.md"
            output_path = os.path.join(OUTPUT_FOLDER, output_filename)

            # Save Markdown content to a file
            with open(output_path, "w", encoding="utf-8") as file:
                file.write(markdown_content)
            
            return send_file(output_path, as_attachment=True)

    return render_template("index.html")

# This code is modified according to obsidian flavoured markdown
# Now also supports the gif as well as the video files
def download_media_and_update_links(main_content, markdown_content):
    # Download images and update Markdown links
    for media_tag in main_content.find_all(['img', 'video']):
        if media_tag.name == 'img':
            media_url = media_tag.get("src")
            media_type = 'image'
        elif media_tag.name == 'video':
            media_url = media_tag.find("source").get("src") if media_tag.find("source") else media_tag.get("src")
            media_type = 'video'

        # Normalize the media URL
        if media_url.startswith("//"):
            media_url = "https:" + media_url
        elif media_url.startswith("/"):
            media_url = request.form.get("url").split("/")[2] + media_url  # Convert relative to absolute

        # Sanitize the media URL to create a safe filename
        media_name = os.path.basename(media_url)
        media_name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', media_name)  # Replace illegal characters

        media_path = os.path.join(ATTACHMENTS_FOLDER, media_name)

        # Download and save the media to the attachments folder
        try:
            media_data = requests.get(media_url).content
            with open(media_path, "wb") as media_file:
                media_file.write(media_data)
        except Exception as e:
            print(f"Error downloading {media_url}: {e}")
            continue  # Skip this media if there's an error

        # Update media links in Markdown for Obsidian
        if media_type == 'image':
            # Use the ![[filename]] syntax for embedding images in Obsidian
            markdown_content = markdown_content.replace(media_tag["src"], f"![{media_name}]({ATTACHMENTS_FOLDER}/{media_name})")
        elif media_type == 'video':
            # Use the normal link syntax for videos
            markdown_content = markdown_content.replace(media_tag["src"], f"[{media_name}]({ATTACHMENTS_FOLDER}/{media_name})")

    return markdown_content


if __name__ == "__main__":
    app.run(debug=True)
