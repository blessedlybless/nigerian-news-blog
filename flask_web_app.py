from flask import Flask, render_template, jsonify, request, send_from_directory
import sqlite3
from datetime import datetime, timedelta
import os
import threading
import subprocess
import sys

app = Flask(__name__)


class NigerianNewsBlogApp:
    def __init__(self):
        self.db_name = 'nigerian_news_blog.db'
        self.last_fetch = None
        self.fetch_interval = 30  # minutes
        self.is_fetching = False

    def should_fetch_news(self):
        """Check if we should fetch new news"""
        if self.last_fetch is None:
            return True

        time_diff = datetime.now() - self.last_fetch
        return time_diff.total_seconds() > (self.fetch_interval * 60)

    def fetch_news_background(self):
        """Fetch news in background"""
        if self.is_fetching:
            return

        self.is_fetching = True
        try:
            print("🔄 Auto-fetching fresh news...")

            # Run the news fetcher script
            result = subprocess.run([sys.executable, 'nigerian_news_with_images.py'],
                                    capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                self.last_fetch = datetime.now()
                print("✅ Fresh news fetched successfully!")
            else:
                print(f"❌ News fetch failed")

        except Exception as e:
            print(f"❌ Error fetching news: {e}")
        finally:
            self.is_fetching = False

    def get_recent_articles(self, limit=15, random_mode=False):
        # Check if we should fetch new news
        if self.should_fetch_news() and not self.is_fetching:
            # Fetch news in background thread (non-blocking)
            thread = threading.Thread(target=self.fetch_news_background)
            thread.daemon = True
            thread.start()

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        if random_mode:
            # Show random articles from recent days
            cursor.execute("""
                SELECT id, title, description, url, published_date, source, category, 
                       local_image_path, posted_to_social
                FROM articles 
                WHERE datetime(created_at) >= datetime('now', '-7 days')
                ORDER BY RANDOM() 
                LIMIT ?
            """, (limit,))
        else:
            # Show latest articles (normal mode)
            cursor.execute("""
                SELECT id, title, description, url, published_date, source, category, 
                       local_image_path, posted_to_social
                FROM articles 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))

        articles = []
        for row in cursor.fetchall():
            articles.append({
                'id': row[0], 'title': row[1], 'description': row[2], 'url': row[3],
                'published_date': row[4], 'source': row[5], 'category': row[6],
                'local_image_path': row[7] or 'images/fallbacks/news_default.jpg',
                'posted_to_social': row[8]
            })

        conn.close()
        return articles

    def get_statistics(self):
        """Get blog statistics"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        stats = {}

        # Total articles
        cursor.execute("SELECT COUNT(*) FROM articles")
        stats['total_articles'] = cursor.fetchone()[0]

        # Posted to social
        cursor.execute("SELECT COUNT(*) FROM articles WHERE posted_to_social = TRUE")
        stats['posted_to_social'] = cursor.fetchone()[0]

        # Sources count
        cursor.execute("SELECT COUNT(DISTINCT source) FROM articles")
        stats['sources_count'] = cursor.fetchone()[0]

        # Fetch status
        stats['is_fetching'] = self.is_fetching

        conn.close()
        return stats


news_app = NigerianNewsBlogApp()


@app.route('/')
def index():
    # Get latest articles (normal mode)
    all_articles = news_app.get_recent_articles(15, random_mode=False)
    stats = news_app.get_statistics()

    return render_template('index.html',
                           articles=all_articles,
                           stats=stats)


@app.route('/random')
def random_articles():
    """Show random recent articles"""
    all_articles = news_app.get_recent_articles(15, random_mode=True)
    stats = news_app.get_statistics()

    return render_template('index.html',
                           articles=all_articles,
                           stats=stats)


@app.route('/api/articles')
def api_articles():
    limit = request.args.get('limit', 15, type=int)
    articles = news_app.get_recent_articles(limit)
    return jsonify(articles)


@app.route('/api/random-articles')
def api_random_articles():
    """Get random recent articles"""
    limit = request.args.get('limit', 15, type=int)
    articles = news_app.get_recent_articles(limit, random_mode=True)
    return jsonify(articles)


@app.route('/api/fetch-news')
def api_fetch_news():
    """Manual trigger to fetch fresh news"""
    if news_app.is_fetching:
        return jsonify({"status": "already_fetching", "message": "News fetch already in progress"})

    thread = threading.Thread(target=news_app.fetch_news_background)
    thread.daemon = True
    thread.start()
    return jsonify({"status": "fetching", "message": "Fresh news being fetched in background"})


@app.route('/api/status')
def api_status():
    """Get fetch status"""
    return jsonify({
        "is_fetching": news_app.is_fetching,
        "last_fetch": news_app.last_fetch.isoformat() if news_app.last_fetch else None
    })


@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files (images)"""
    return send_from_directory('static', filename)


if __name__ == '__main__':
    print("🇳🇬📸 Nigerian News Flask server with Random Articles!")
    print("🌐 Visit: http://localhost:5000")
    print("🎲 Random articles: http://localhost:5000/random")
    print("🔄 Auto-fetches fresh news every 30 minutes")
    print("📱 Manual refresh shows random articles")
    app.run(debug=True, host='0.0.0.0', port=5000)

# Add this at the end of your flask_web_app.py file
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    print("🇳🇬📸 Nigerian News Flask server starting...")
    print(f"🌐 Running on port: {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

