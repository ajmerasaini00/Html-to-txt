import os
import re
from pyrogram import Client, filters
from pyrogram.types import Message

# Telegram bot setup
API_ID = 12475131
API_HASH = "719171e38be5a1f500613837b79c536f"
BOT_TOKEN = "7564571951:AAE6xX7b2wPr6jh2SNV4ZH6EoVJXREuyAU8"
CHANNEL_USERNAME = "https://t.me/+_BpSWJk8uCthMDZl"

app = Client("url_extractor_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Function to extract names and URLs
def extract_names_and_urls(file_content):
    pattern = r"(.*?)\s*:\s*(https?://\S+)"
    return re.findall(pattern, file_content)

# Function to categorize URLs
def categorize_urls(urls):
    videos, pdfs, others = [], [], []
    for name, url in urls:
        # Replace Utkarsh S3 → CloudFront
        if "https://apps-s3-jw-prod.utkarshapp.com" in url:
            url = url.replace(
                "https://apps-s3-jw-prod.utkarshapp.com",
                "https://d1q5ugnejk3zoi.cloudfront.net/ut-production-jw/"
            )

        if any(ext in url for ext in [".mp4", ".mkv", ".m3u8", ".mpd"]):
            videos.append((name, url))
        elif url.endswith(".pdf"):
            pdfs.append((name, url))
        else:
            others.append((name, url))
    return videos, pdfs, others

# Function to generate HTML with play + download
def generate_html(title, videos, pdfs, others):
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <link href="https://vjs.zencdn.net/7.21.1/video-js.css" rel="stylesheet" />
    <script src="https://vjs.zencdn.net/7.21.1/video.min.js"></script>
</head>
<body>
    <h1>{title}</h1>

    <h2>🎬 Videos</h2>
    <ul>
"""
    for name, url in videos:
        html_content += f"""
        <li>
            <p><b>{name}</b></p>
            <video id="video_{name}" class="video-js vjs-big-play-centered" controls preload="auto" width="640" height="360">
                <source src="{url}" type="application/x-mpegURL">
                <source src="{url}" type="video/mp4">
            </video>
            <br/>
            <a href="{url}" download>
                <button>⬇ Download</button>
            </a>
        </li>
        <hr/>
"""
    html_content += "<h2>📕 PDFs</h2><ul>"
    for name, url in pdfs:
        html_content += f"""
        <li>
            <a href="{url}" target="_blank">{name}</a>
            <a href="{url}" download><button>⬇ Download</button></a>
        </li>
"""
    html_content += "</ul><h2>🌐 Others</h2><ul>"
    for name, url in others:
        html_content += f"""
        <li>
            <a href="{url}" target="_blank">{name}</a>
            <a href="{url}" download><button>⬇ Download</button></a>
        </li>
"""
    html_content += "</ul></body></html>"
    return html_content

# Handle uploaded .txt files
@app.on_message(filters.document)
async def handle_file(client: Client, message: Message):
    # Check if the file is a .txt file
    if not message.document.file_name.endswith(".txt"):
        await message.reply_text("Please upload a .txt file.")
        return

    # Download the file
    file_path = await message.download()
    file_name = message.document.file_name

    # Read the file content
    with open(file_path, "r", encoding="utf-8") as f:
        file_content = f.read()

    # Extract names and URLs
    urls = extract_names_and_urls(file_content)

    # Categorize URLs
    videos, pdfs, others = categorize_urls(urls)

    # Generate HTML
    html_content = generate_html(file_name, videos, pdfs, others)
    html_file_path = file_path.replace(".txt", ".html")
    with open(html_file_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # Generate categorized TXT file
    txt_output_path = file_path.replace(".txt", "_output.txt")
    with open(txt_output_path, "w", encoding="utf-8") as f:
        f.write("=== VIDEOS ===\n")
        for name, url in videos:
            f.write(f"{name}: {url}\n")
        f.write("\n=== PDFs ===\n")
        for name, url in pdfs:
            f.write(f"{name}: {url}\n")
        f.write("\n=== OTHERS ===\n")
        for name, url in others:
            f.write(f"{name}: {url}\n")

    # Send the HTML and TXT file to the user
    await message.reply_document(document=html_file_path, caption="✅ HTML File with Play + Download Ready!")
    await message.reply_document(document=txt_output_path, caption="✅ TXT File Extracted!")

    # Forward the original .txt file to the channel
    await client.send_document(chat_id=CHANNEL_USERNAME, document=file_path)

    # Clean up files
    os.remove(file_path)
    os.remove(html_file_path)
    os.remove(txt_output_path)


print("🤖 Bot is running...")
app.run()
