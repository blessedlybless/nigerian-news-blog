import requests
import json
from datetime import datetime
import sqlite3
import feedparser
from typing import List, Dict
import time
import os
import urllib.request
from urllib.parse import urlparse
import hashlib
from PIL import Image
import io


class NigerianNewsBlogWithImages:
    def __init__(self):
        self.db_name = 'nigerian_news_blog.db'
        self.images_folder = 'static/images'
        self.setup_database()
        self.setup_images_folder()

    def setup_database(self):
        """Setup SQLite database with image support"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                url TEXT UNIQUE,
                published_date DATETIME,
                source TEXT,
                category TEXT,
                image_url TEXT,
                local_image_path TEXT,
                posted_to_social BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS social_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER,
                platform TEXT,
                post_content TEXT,
                image_path TEXT,
                posted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'scheduled',
                FOREIGN KEY (article_id) REFERENCES articles (id)
            )
        """)

        conn.commit()
        conn.close()
        print("✅ Database with image support initialized!")

    def setup_images_folder(self):
        """Create folders for storing images"""
        folders = [self.images_folder, 'static/images/thumbnails', 'static/images/fallbacks']
        for folder in folders:
            os.makedirs(folder, exist_ok=True)
        print("✅ Image folders created!")

    def extract_image_from_entry(self, entry) -> str:
        """Extract image URL from RSS entry"""
        image_url = None

        # Method 1: Check for media:content or media:thumbnail
        if hasattr(entry, 'media_content') and entry.media_content:
            image_url = entry.media_content[0].get('url')
        elif hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
            image_url = entry.media_thumbnail[0].get('url')

        # Method 2: Check enclosure for images
        elif hasattr(entry, 'enclosures') and entry.enclosures:
            for enclosure in entry.enclosures:
                if enclosure.get('type', '').startswith('image/'):
                    image_url = enclosure.get('href')
                    break

        # Method 3: Extract from content/summary
        elif hasattr(entry, 'content') and entry.content:
            import re
            content = entry.content[0].value if isinstance(entry.content, list) else str(entry.content)
            img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', content)
            if img_match:
                image_url = img_match.group(1)

        # Method 4: Check summary for images
        elif hasattr(entry, 'summary'):
            import re
            img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', entry.summary)
            if img_match:
                image_url = img_match.group(1)

        return image_url

    def download_and_process_image(self, image_url: str, article_title: str) -> str:
        """Download image and create thumbnail"""
        if not image_url:
            return None

        try:
            # Create filename from article title and image URL
            title_hash = hashlib.md5(article_title.encode()).hexdigest()[:8]
            url_hash = hashlib.md5(image_url.encode()).hexdigest()[:8]
            filename = f"{title_hash}_{url_hash}.jpg"

            full_path = os.path.join(self.images_folder, filename)

            # Skip if already downloaded
            if os.path.exists(full_path):
                return f"images/{filename}"

            # Download image with headers to avoid blocking
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            req = urllib.request.Request(image_url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                image_data = response.read()

            # Process image with PIL
            image = Image.open(io.BytesIO(image_data))

            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background

            # Save optimized image (max 800px width)
            if image.width > 800:
                ratio = 800 / image.width
                new_size = (800, int(image.height * ratio))
                image = image.resize(new_size, Image.Resampling.LANCZOS)

            image.save(full_path, 'JPEG', quality=85, optimize=True)

            print(f"✅ Downloaded image: {filename}")
            return f"images/{filename}"

        except Exception as e:
            print(f"❌ Error downloading image {image_url}: {str(e)}")
            return None

    def create_fallback_images(self):
        """Create simple fallback images if they don't exist"""
        fallbacks_dir = os.path.join(self.images_folder, 'fallbacks')

        fallback_configs = [
            ('nigeria_flag.jpg', (255, 255, 255), '🇳🇬 NIGERIAN\nNEWS', '#009639'),
            ('football.jpg', (255, 255, 255), '⚽ NIGERIAN\nSPORTS', '#FF6B35'),
            ('nollywood.jpg', (255, 255, 255), '🎬 NOLLYWOOD\nENTERTAINMENT', '#8E44AD'),
            ('news_default.jpg', (255, 255, 255), '📰 BREAKING\nNEWS', '#2C3E50')
        ]

        try:
            from PIL import Image, ImageDraw, ImageFont

            for filename, bg_color, text, text_color in fallback_configs:
                filepath = os.path.join(fallbacks_dir, filename)
                if not os.path.exists(filepath):
                    # Create 400x300 image
                    img = Image.new('RGB', (400, 300), bg_color)
                    draw = ImageDraw.Draw(img)

                    # Try to use a font, fallback to default
                    try:
                        font = ImageFont.truetype("arial.ttf", 32)
                    except:
                        font = ImageFont.load_default()

                    # Calculate text position (center)
                    text_bbox = draw.textbbox((0, 0), text, font=font)
                    text_width = text_bbox[2] - text_bbox[0]
                    text_height = text_bbox[3] - text_bbox[1]

                    x = (400 - text_width) // 2
                    y = (300 - text_height) // 2

                    draw.text((x, y), text, fill=text_color, font=font, align='center')
                    img.save(filepath, 'JPEG', quality=90)
                    print(f"✅ Created fallback image: {filename}")

        except ImportError:
            print("⚠️  PIL not available for creating fallback images")

    def fetch_news_from_rss(self, rss_url: str, category: str = "nigeria") -> List[Dict]:
        """Fetch news from RSS feed with image extraction"""
        try:
            feed = feedparser.parse(rss_url)
            articles = []

            for entry in feed.entries:
                # Extract image URL
                image_url = self.extract_image_from_entry(entry)

                article = {
                    'title': entry.get('title', 'No Title'),
                    'description': entry.get('summary', 'No Description'),
                    'url': entry.get('link', ''),
                    'published_date': entry.get('published', str(datetime.now())),
                    'source': feed.feed.get('title', 'Unknown Source'),
                    'category': category,
                    'image_url': image_url
                }
                articles.append(article)

            source_name = rss_url.split('/')[2].replace('www.', '').replace('.com', '').replace('.ng', '').upper()
            print(f"✅ Fetched {len(articles)} articles from {source_name} ({category.upper()})")
            return articles

        except Exception as e:
            print(f"❌ Error fetching from {rss_url}: {str(e)}")
            return []

    def save_articles(self, articles: List[Dict]) -> List[int]:
        """Save articles to database with image processing"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        saved_ids = []

        for article in articles:
            try:
                # Download and process image
                local_image_path = None
                if article.get('image_url'):
                    local_image_path = self.download_and_process_image(
                        article['image_url'],
                        article['title']
                    )

                # If no image downloaded, use fallback
                if not local_image_path:
                    fallback_images = {
                        'nigeria': 'images/fallbacks/nigeria_flag.jpg',
                        'sports': 'images/fallbacks/football.jpg',
                        'entertainment': 'images/fallbacks/nollywood.jpg'
                    }
                    local_image_path = fallback_images.get(article['category'].lower(),
                                                           'images/fallbacks/news_default.jpg')

                cursor.execute("""
                    INSERT OR IGNORE INTO articles 
                    (title, description, url, published_date, source, category, image_url, local_image_path)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    article['title'], article['description'], article['url'],
                    article['published_date'], article['source'], article['category'],
                    article.get('image_url'), local_image_path
                ))

                if cursor.rowcount > 0:
                    saved_ids.append(cursor.lastrowid)

            except Exception as e:
                print(f"Error saving article: {e}")

        conn.commit()
        conn.close()
        print(f"✅ Saved {len(saved_ids)} new articles with images")
        return saved_ids

    def run_nigerian_news_cycle(self):
        """Focused news cycle with image processing"""
        print("🇳🇬 Starting Nigerian News Cycle with Images...")
        print("=" * 60)

        # Create fallback images if needed
        self.create_fallback_images()

        # Nigerian RSS feeds
        rss_feeds = [
            # Nigerian News Sources
            ("https://vanguardngr.com/feed/", "nigeria"),
            ("https://guardian.ng/feed/", "nigeria"),
            ("https://punchng.com/feed/", "nigeria"),
            ("https://dailypost.ng/feed/", "nigeria"),
            ("https://premiumtimesng.com/feed/", "nigeria"),
            ("https://saharareporters.com/rss", "nigeria"),

            # Nigerian Sports News
            ("https://www.completesports.com/feed/", "sports"),
            ("https://soccernet.ng/feed/", "sports"),
            ("https://brila.net/feed/", "sports"),

            # Nigerian Entertainment News
            ("https://lindaikejisblog.com/feed/", "entertainment"),
            ("https://bellanaija.com/feed/", "entertainment"),
            ("https://pulse.ng/entertainment/feed", "entertainment"),
            ("https://www.naijaloaded.com.ng/feed/", "entertainment"),
            ("https://tooexclusive.com/feed/", "entertainment"),
        ]

        all_articles = []

        print("📡 Fetching news with images from Nigerian sources...")
        for rss_url, category in rss_feeds:
            articles = self.fetch_news_from_rss(rss_url, category)
            all_articles.extend(articles)
            time.sleep(0.5)  # Be nice to servers

        if all_articles:
            saved_ids = self.save_articles(all_articles)
            print(f"\n✅ Nigerian News Cycle with Images Completed! 🇳🇬📸")

    def get_recent_articles(self, limit: int = 10) -> List[Dict]:
        """Get recent articles with image paths"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, title, description, url, published_date, source, category, 
                   local_image_path, posted_to_social
            FROM articles ORDER BY created_at DESC LIMIT ?
        """, (limit,))

        articles = []
        for row in cursor.fetchall():
            articles.append({
                'id': row[0], 'title': row[1], 'description': row[2], 'url': row[3],
                'published_date': row[4], 'source': row[5], 'category': row[6],
                'local_image_path': row[7], 'posted_to_social': row[8]
            })

        conn.close()
        return articles


# Run the enhanced application
if __name__ == "__main__":
    print("🇳🇬📸 NIGERIAN NEWS BLOG WITH IMAGES")
    print("=" * 60)

    app = NigerianNewsBlogWithImages()
    app.run_nigerian_news_cycle()
