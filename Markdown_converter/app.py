from flask import Flask, render_template, request, send_file
import requests
from bs4 import BeautifulSoup
import markdownify
import os
from datetime import datetime
import urllib.parse

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

''' def download_images_and_update_links(main_content, markdown_content):
    # Find all image tags and download images
    for img_tag in main_content.find_all("img"):
        img_url = img_tag.get("src")
        if img_url.startswith("//"):
            img_url = "https:" + img_url
        elif img_url.startswith("/"):
            img_url = request.form.get("url").split("/")[2] + img_url  # Relative path to absolute

        img_data = requests.get(img_url).content
        img_name = os.path.join(ATTACHMENTS_FOLDER, os.path.basename(img_url))
        
        # Save image to attachments folder
        with open(img_name, "wb") as img_file:
            img_file.write(img_data)

        # Update image links in Markdown to point to the attachments folder
        markdown_content = markdown_content.replace(img_tag["src"], f"{ATTACHMENTS_FOLDER}/{os.path.basename(img_url)}")
    
    return markdown_content
'''
import re

''' def download_images_and_update_links(main_content, markdown_content):
    # Find all image tags and download images
    for img_tag in main_content.find_all("img"):
        img_url = img_tag.get("src")
        if img_url.startswith("//"):
            img_url = "https:" + img_url
        elif img_url.startswith("/"):
            img_url = request.form.get("url").split("/")[2] + img_url  # Relative path to absolute

        # Sanitize the image URL to create a safe filename
        img_name = os.path.basename(img_url)
        img_name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', img_name)  # Replace illegal characters with '_'
        
        img_path = os.path.join(ATTACHMENTS_FOLDER, img_name)
        
        # Download and save the image to the attachments folder
        img_data = requests.get(img_url).content
        with open(img_path, "wb") as img_file:
            img_file.write(img_data)

        # Update image links in Markdown to point to the attachments folder
        markdown_content = markdown_content.replace(img_tag["src"], f"{ATTACHMENTS_FOLDER}/{img_name}")
    
    return markdown_content
'''

# Attachments are not downloading
def download_images_and_update_links(main_content, markdown_content):
    # Find all image tags and download images
    for img_tag in main_content.find_all("img"):
        img_url = img_tag.get("src")
        
        # Normalize the image URL
        if img_url.startswith("//"):
            img_url = "https:" + img_url
        elif img_url.startswith("/"):
            img_url = request.form.get("url").split("/")[2] + img_url  # Convert relative to absolute

        # Sanitize the image URL to create a safe filename
        img_name = os.path.basename(img_url)
        img_name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', img_name)  # Replace illegal characters

        img_path = os.path.join(ATTACHMENTS_FOLDER, img_name)
        
        # Download and save the image to the attachments folder
        try:
            img_data = requests.get(img_url).content
            with open(img_path, "wb") as img_file:
                img_file.write(img_data)
        except Exception as e:
            print(f"Error downloading {img_url}: {e}")
            continue  # Skip this image if there's an error

        # Update image links in Markdown to point to the attachments folder
        markdown_content = markdown_content.replace(img_tag["src"], f"{ATTACHMENTS_FOLDER}/{img_name}")
    
    return markdown_content

if __name__ == "__main__":
    app.run(debug=True)
