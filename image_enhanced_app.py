from flask import Flask, render_template_string, jsonify, request
import sqlite3
import os
from datetime import datetime
import threading
import time
import requests
from urllib.parse import urlparse

app = Flask(__name__)

class NigerianNewsBlogApp:
    def __init__(self):
        self.db_name = 'nigerian_news_blog.db'
        self.setup_database()
    
    def setup_database(self):
        """Create database with sample articles and REAL images"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    url TEXT UNIQUE NOT NULL,
                    published_date TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    source TEXT,
                    category TEXT DEFAULT 'nigeria',
                    local_image_path TEXT,
                    posted_to_social BOOLEAN DEFAULT FALSE
                )
            ''')
            
            # Sample articles with REAL Nigerian images
            sample_articles = [
                ("Breaking: Nigerian Economy Records 4.2% Growth in Q4 2025", "Nigeria's economy demonstrates exceptional resilience with robust growth across technology, agriculture, and oil sectors, marking the highest quarterly growth in five years.", "https://naijanews.com/economy-growth-2025", "2025-09-29 16:00:00", "Vanguard Nigeria", "nigeria", "https://images.unsplash.com/photo-1541746972996-4e0b0f93e586?w=400&h=250&fit=crop"),
                ("Super Eagles Secure Historic AFCON 2026 Victory", "Nigerian national football team delivers spectacular 3-1 victory against Ghana at the National Stadium, advancing to African Cup of Nations finals.", "https://sports247.ng/super-eagles-afcon-2026", "2025-09-29 15:45:00", "Complete Sports", "sports", "https://images.unsplash.com/photo-1574629810360-7efbbe195018?w=400&h=250&fit=crop"),
                ("Nollywood Director Wins Prestigious Cannes Award", "Nigerian filmmaker receives international acclaim at Cannes Film Festival for groundbreaking cinematography and authentic African storytelling.", "https://entertainment.ng/nollywood-cannes-2025", "2025-09-29 15:30:00", "Pulse Nigeria", "entertainment", "https://images.unsplash.com/photo-1485846234645-a62644f84728?w=400&h=250&fit=crop"),
                ("Lagos-Ibadan Railway Achieves Full Operational Status", "The Lagos-Ibadan railway line officially commences full passenger service, reducing travel time by 60% and marking a major infrastructure milestone.", "https://infrastructure.ng/lagos-ibadan-rail-2025", "2025-09-29 15:15:00", "The Nation Nigeria", "nigeria", "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?w=400&h=250&fit=crop"),
                ("Nigerian Fintech Startup Raises Record $100M Series B", "Lagos-based financial technology company secures largest Series B funding in West African history from international venture capitalists.", "https://techpoint.ng/fintech-funding-2025", "2025-09-29 15:00:00", "TechCabal", "nigeria", "https://images.unsplash.com/photo-1551434678-e076c223a692?w=400&h=250&fit=crop"),
                ("Burna Boy Announces Massive 2025 World Tour", "Grammy-winning Nigerian superstar reveals extensive world tour spanning 50 cities across Africa, Europe, North America, and Australia.", "https://music.ng/burna-boy-world-tour-2025", "2025-09-29 14:45:00", "NotJustOk", "entertainment", "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=400&h=250&fit=crop"),
                ("Nigerian Agricultural Exports Hit All-Time Record High", "Agricultural sector achieves unprecedented export volumes with cocoa, cashew nuts, and palm oil leading foreign exchange earnings growth.", "https://agric.ng/export-record-2025", "2025-09-29 14:30:00", "Daily Trust", "nigeria", "https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=400&h=250&fit=crop"),
                ("Victor Osimhen Scores Champions League Hat-trick", "Nigerian striker Victor Osimhen delivers outstanding UEFA Champions League performance with three spectacular goals in European football.", "https://goal.com/osimhen-champions-league-2025", "2025-09-29 14:15:00", "Goal.com Nigeria", "sports", "https://images.unsplash.com/photo-1521731978332-9e9e714bdd20?w=400&h=250&fit=crop"),
                ("President Tinubu Launches National Digital Economy Initiative", "Nigerian government unveils comprehensive digital transformation program aimed at positioning Nigeria as Africa's leading technology hub by 2030.", "https://statehouse.ng/digital-economy-2025", "2025-09-29 14:00:00", "Premium Times", "nigeria", "https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=400&h=250&fit=crop"),
                ("Wizkid Collaborates with International Streaming Giants", "Nigerian Afrobeats sensation secures groundbreaking partnership with major streaming platforms to promote African music worldwide.", "https://afrobeats.ng/wizkid-streaming-2025", "2025-09-29 13:45:00", "Soundcity", "entertainment", "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=400&h=250&fit=crop"),
                ("Nigerian Universities Achieve Global Research Breakthrough", "Consortium of Nigerian universities publishes revolutionary research in renewable energy, positioning Nigeria as leader in sustainable technology.", "https://education.ng/research-breakthrough-2025", "2025-09-29 13:30:00", "The Guardian Nigeria", "nigeria", "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=250&fit=crop"),
                ("D'Tigress Qualify for Olympic Basketball Finals", "Nigerian women's basketball team secures historic qualification for Olympic Games finals, marking unprecedented achievement in African women's basketball.", "https://basketball.ng/dtigress-olympics-2025", "2025-09-29 13:15:00", "Sports247", "sports", "https://images.unsplash.com/photo-1546519638-68e109498ffc?w=400&h=250&fit=crop")
            ]
            
            for title, desc, url, pub_date, source, category, img_url in sample_articles:
                cursor.execute("""
                    INSERT OR IGNORE INTO articles 
                    (title, description, url, published_date, source, category, local_image_path)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (title, desc, url, pub_date, source, category, img_url))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Database setup error: {e}")
            return False
    
    def get_recent_articles(self, limit=15, random_mode=False):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        if random_mode:
            cursor.execute("""
                SELECT id, title, description, url, published_date, source, category, 
                       local_image_path, posted_to_social
                FROM articles 
                ORDER BY RANDOM() 
                LIMIT ?
            """, (limit,))
        else:
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
                'local_image_path': row[7] or 'https://images.unsplash.com/photo-1586339949916-3e9457bef6d3?w=400&h=250&fit=crop',
                'posted_to_social': row[8]
            })
        
        conn.close()
        return articles
    
    def get_statistics(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        stats = {}
        cursor.execute("SELECT COUNT(*) FROM articles")
        stats['total_articles'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM articles WHERE posted_to_social = TRUE")
        stats['posted_to_social'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT source) FROM articles")
        stats['sources_count'] = cursor.fetchone()[0]
        
        conn.close()
        return stats

news_app = NigerianNewsBlogApp()

@app.route('/')
def index():
    all_articles = news_app.get_recent_articles(15, random_mode=False)
    stats = news_app.get_statistics()
    
    return render_template_string('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🇳🇬 Nigerian News Hub - Latest Updates with Images</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            line-height: 1.6; color: #333; background: #f4f4f4; 
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { 
            background: linear-gradient(135deg, #009639 0%, #ffffff 50%, #009639 100%); 
            color: white; padding: 2rem 0; margin-bottom: 2rem; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .header h1 { 
            text-align: center; font-size: 2.5rem; 
            text-shadow: 0 2px 4px rgba(0,0,0,0.3); 
            color: #009639;
        }
        .header p {
            text-align: center; margin-top: 0.5rem;
            color: #009639; font-size: 1.1rem; font-weight: 500;
        }
        .stats-bar { 
            background: white; padding: 1.5rem; margin-bottom: 2rem; 
            border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 1rem; text-align: center;
        }
        .stat-item h3 { 
            color: #009639; margin-bottom: 0.5rem; font-size: 2rem; 
        }
        .stat-item p { color: #666; font-weight: 500; }
        
        .action-bar {
            background: white; padding: 1rem; margin-bottom: 2rem;
            border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center; display: flex; gap: 1rem; justify-content: center;
            flex-wrap: wrap;
        }
        .action-btn {
            display: inline-block; padding: 0.7rem 1.5rem;
            background: #009639; color: white; text-decoration: none;
            border: none; border-radius: 25px; cursor: pointer;
            font-weight: 500; transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0, 150, 57, 0.3);
        }
        .action-btn:hover {
            background: #007a2e; transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0, 150, 57, 0.4);
        }
        .action-btn.secondary {
            background: #6c757d; box-shadow: 0 4px 15px rgba(108, 117, 125, 0.3);
        }
        .action-btn.secondary:hover { background: #545b62; }
        
        .categories-nav {
            background: white; padding: 1rem; margin-bottom: 2rem;
            border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }
        .category-filter {
            display: inline-block; margin: 0 0.5rem; padding: 0.5rem 1rem;
            background: #f8f9fa; border: 2px solid #009639; border-radius: 25px;
            color: #009639; font-weight: 500;
            transition: all 0.3s ease; cursor: pointer;
        }
        .category-filter:hover, .category-filter.active {
            background: #009639; color: white;
        }
        
        .article-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); 
            gap: 2rem; 
        }
        .article-card { 
            border: 1px solid #ddd; border-radius: 15px; 
            background: white; box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            transition: all 0.3s ease; overflow: hidden;
        }
        .article-card:hover { 
            transform: translateY(-8px); 
            box-shadow: 0 12px 30px rgba(0,0,0,0.15); 
        }
        
        .article-image {
            width: 100%; height: 200px; 
            object-fit: cover; 
            border-bottom: 1px solid #eee;
            transition: all 0.3s ease;
        }
        .article-card:hover .article-image {
            transform: scale(1.05);
        }
        
        .article-content {
            padding: 1.5rem;
        }
        .article-title { 
            color: #2c3e50; margin-bottom: 1rem; font-size: 1.2rem; 
            font-weight: 600; line-height: 1.4;
        }
        .article-meta { 
            color: #666; font-size: 0.9rem; margin-bottom: 1rem; 
            display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center;
        }
        .meta-badge { 
            background: #e9ecef; padding: 0.3rem 0.7rem; 
            border-radius: 15px; font-size: 0.8rem; 
        }
        .nigeria-badge { background: #009639; color: white; }
        .sports-badge { background: #ff6b35; color: white; }
        .entertainment-badge { background: #8e44ad; color: white; }
        .article-desc { 
            margin-bottom: 1.5rem; color: #555; line-height: 1.6; 
        }
        .read-more { 
            background: linear-gradient(45deg, #009639, #00b545); 
            color: white; padding: 0.8rem 1.5rem; text-decoration: none; 
            border-radius: 25px; display: inline-block; 
            transition: all 0.3s ease; font-weight: 500;
            box-shadow: 0 4px 15px rgba(0, 150, 57, 0.3);
        }
        .read-more:hover { 
            background: linear-gradient(45deg, #007a2e, #009639); 
            transform: translateY(-2px); 
            box-shadow: 0 6px 20px rgba(0, 150, 57, 0.4);
        }
        
        .refresh-btn {
            position: fixed; bottom: 20px; right: 20px;
            background: #009639; color: white; border: none;
            padding: 1rem; border-radius: 50px; cursor: pointer;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            transition: all 0.3s ease; z-index: 1000;
        }
        .refresh-btn:hover { background: #007a2e; transform: scale(1.1); }
        
        @media (max-width: 768px) {
            .article-grid { grid-template-columns: 1fr; }
            .stats-bar { grid-template-columns: 1fr; }
            .header h1 { font-size: 2rem; }
            .action-bar { padding: 0.5rem; }
            .categories-nav { padding: 0.5rem; }
            .category-filter { margin: 0.25rem; padding: 0.4rem 0.8rem; }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="container">
            <h1>🇳🇬 Nigerian News Hub</h1>
            <p>📸 Latest Updates with Images • 🔄 Auto-Refreshed</p>
        </div>
    </div>
    
    <div class="container">
        <div class="stats-bar">
            <div class="stat-item">
                <h3>{{ stats.total_articles }}</h3>
                <p>📰 Total Articles</p>
            </div>
            <div class="stat-item">
                <h3>{{ stats.posted_to_social }}</h3>
                <p>📱 Shared on Social</p>
            </div>
            <div class="stat-item">
                <h3>{{ stats.sources_count }}</h3>
                <p>📡 News Sources</p>
            </div>
        </div>

        <div class="action-bar">
            <button class="action-btn" onclick="fetchRandomArticles()">🎲 Random Mix</button>
            <button class="action-btn secondary" onclick="location.reload()">🔄 Refresh Page</button>
            <button class="action-btn secondary" onclick="filterCategory('all')">🌟 All News</button>
        </div>

        <div class="categories-nav">
            <span class="category-filter active" data-category="all" onclick="filterCategory('all')">🌟 All News</span>
            <span class="category-filter" data-category="nigeria" onclick="filterCategory('nigeria')">🇳🇬 Nigeria</span>
            <span class="category-filter" data-category="sports" onclick="filterCategory('sports')">⚽ Sports</span>
            <span class="category-filter" data-category="entertainment" onclick="filterCategory('entertainment')">🎬 Entertainment</span>
        </div>

        <div class="article-grid" id="articlesGrid">
            {% for article in articles %}
            <div class="article-card" data-category="{{ article.category }}">
                <img src="{{ article.local_image_path }}" alt="{{ article.title }}" class="article-image" 
                     onerror="this.src='https://images.unsplash.com/photo-1586339949916-3e9457bef6d3?w=400&h=250&fit=crop'">
                
                <div class="article-content">
                    <h2 class="article-title">{{ article.title }}</h2>
                    <div class="article-meta">
                        <span class="meta-badge">📰 {{ article.source }}</span>
                        {% if article.category == 'nigeria' %}
                        <span class="meta-badge nigeria-badge">🇳🇬 {{ article.category|title }}</span>
                        {% elif article.category == 'sports' %}
                        <span class="meta-badge sports-badge">⚽ {{ article.category|title }}</span>
                        {% elif article.category == 'entertainment' %}
                        <span class="meta-badge entertainment-badge">🎬 {{ article.category|title }}</span>
                        {% endif %}
                        <span class="meta-badge">📅 {{ article.published_date[:10] }}</span>
                    </div>
                    <p class="article-desc">
                        {{ article.description[:180] }}{% if article.description|length > 180 %}...{% endif %}
                    </p>
                    <a href="{{ article.url }}" target="_blank" class="read-more">
                        Read Full Article →
                    </a>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>

    <button class="refresh-btn" onclick="fetchRandomArticles()" title="Get random articles">
        🎲
    </button>

    <script>
        // Get random articles
        function fetchRandomArticles() {
            const btn = document.querySelector('.refresh-btn');
            btn.innerHTML = '🔄';
            
            fetch('/api/random-articles?limit=15')
                .then(response => response.json())
                .then(articles => {
                    updateArticleGrid(articles);
                    btn.innerHTML = '🎲';
                })
                .catch(error => {
                    console.error('Error:', error);
                    btn.innerHTML = '❌';
                    setTimeout(() => btn.innerHTML = '🎲', 2000);
                });
        }
        
        // Update article grid
        function updateArticleGrid(articles) {
            const grid = document.getElementById('articlesGrid');
            grid.innerHTML = '';
            
            articles.forEach((article, index) => {
                const card = createArticleCard(article);
                grid.appendChild(card);
                
                setTimeout(() => {
                    card.style.opacity = '1';
                    card.style.transform = 'translateY(0)';
                }, index * 50);
            });
        }
        
        // Create article card
        function createArticleCard(article) {
            const card = document.createElement('div');
            card.className = 'article-card';
            card.dataset.category = article.category;
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            card.style.transition = 'all 0.5s ease';
            
            const categoryClass = {
                'nigeria': 'nigeria-badge',
                'sports': 'sports-badge', 
                'entertainment': 'entertainment-badge'
            };
            
            const categoryEmoji = {
                'nigeria': '🇳🇬',
                'sports': '⚽',
                'entertainment': '🎬'
            };
            
            card.innerHTML = `
                <img src="${article.local_image_path}" alt="${article.title}" class="article-image" 
                     onerror="this.src='https://images.unsplash.com/photo-1586339949916-3e9457bef6d3?w=400&h=250&fit=crop'">
                <div class="article-content">
                    <h2 class="article-title">${article.title}</h2>
                    <div class="article-meta">
                        <span class="meta-badge">📰 ${article.source}</span>
                        <span class="meta-badge ${categoryClass[article.category]}">${categoryEmoji[article.category] || '📂'} ${article.category.charAt(0).toUpperCase() + article.category.slice(1)}</span>
                        <span class="meta-badge">📅 ${article.published_date.substring(0, 10)}</span>
                    </div>
                    <p class="article-desc">${article.description.substring(0, 180)}${article.description.length > 180 ? '...' : ''}</p>
                    <a href="${article.url}" target="_blank" class="read-more">Read Full Article →</a>
                </div>
            `;
            
            return card;
        }
        
        // Category filtering
        function filterCategory(category) {
            const filterButtons = document.querySelectorAll('.category-filter');
            const articleCards = document.querySelectorAll('.article-card');
            
            filterButtons.forEach(btn => btn.classList.remove('active'));
            document.querySelector(`[data-category="${category}"]`).classList.add('active');
            
            articleCards.forEach(card => {
                if (category === 'all' || card.dataset.category === category) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        }
        
        // Initial animation
        document.addEventListener('DOMContentLoaded', function() {
            const cards = document.querySelectorAll('.article-card');
            cards.forEach((card, index) => {
                card.style.opacity = '0';
                card.style.transform = 'translateY(20px)';
                setTimeout(() => {
                    card.style.opacity = '1';
                    card.style.transform = 'translateY(0)';
                }, index * 100);
            });
        });
    </script>
</body>
</html>''', articles=all_articles, stats=stats)

@app.route('/api/random-articles')
def api_random_articles():
    limit = request.args.get('limit', 15, type=int)
    articles = news_app.get_recent_articles(limit, random_mode=True)
    return jsonify(articles)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("🇳🇬📸 Nigerian News Blog with REAL IMAGES starting...")
    app.run(host='0.0.0.0', port=port, debug=False)
