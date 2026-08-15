/**
 * 🦅 PHANTOM TERMINAL - BLOOMBERG-STYLE NEWS WIRE & CALENDAR CONTROLLER
 */

class NewsWireView {
  constructor(app) {
    this.app = app;
    this.activeCategory = 'ALL';
    this.searchQuery = '';
    this.articles = [];
    this.calendar = [];

    this.initElements();
    this.fetchNews();
    this.fetchCalendar();
  }

  initElements() {
    this.wireContainer = document.getElementById('news-wire-list');
    this.calendarContainer = document.getElementById('economic-calendar-list');
    this.flashTickerText = document.getElementById('flash-ticker-headline');
    this.searchInput = document.getElementById('news-search-input');
    this.btnRefresh = document.getElementById('btn-refresh-news');

    // Category pills
    const pills = document.querySelectorAll('.pill-btn');
    pills.forEach((p) => {
      p.addEventListener('click', () => {
        this.app.playSound('click');
        pills.forEach((b) => b.classList.remove('active'));
        p.classList.add('active');
        this.activeCategory = p.getAttribute('data-cat') || 'ALL';
        this.renderArticles();
      });
    });

    if (this.searchInput) {
      this.searchInput.addEventListener('input', (e) => {
        this.searchQuery = e.target.value.toLowerCase();
        this.renderArticles();
      });
    }

    const baseUrl = (window.location.origin && window.location.origin.startsWith('http')) ? window.location.origin : 'http://127.0.0.1:8000';

    if (this.btnRefresh) {
      this.btnRefresh.addEventListener('click', async () => {
        this.app.playSound('click');
        this.app.showToast('Fetching latest live RSS feeds...', 'warning');
        await fetch(`${baseUrl}/api/refresh-news`, { method: 'POST' });
        await this.fetchNews();
        this.app.playSound('success');
        this.app.showToast('News wire refreshed!', 'success');
      });
    }
  }

  async fetchNews() {
    try {
      const baseUrl = (window.location.origin && window.location.origin.startsWith('http')) ? window.location.origin : 'http://127.0.0.1:8000';
      const resp = await fetch(`${baseUrl}/api/news?category=ALL`);
      if (resp.ok) {
        const data = await resp.json();
        this.articles = data.articles || [];
        this.renderArticles();
        if (this.articles.length > 0) {
          this.updateFlashTicker(this.articles[0]);
        }
      }
    } catch (e) {
      console.warn('Failed to fetch news:', e);
    }
  }

  async fetchCalendar() {
    try {
      const baseUrl = (window.location.origin && window.location.origin.startsWith('http')) ? window.location.origin : 'http://127.0.0.1:8000';
      const resp = await fetch(`${baseUrl}/api/economic-calendar`);
      if (resp.ok) {
        const data = await resp.json();
        this.calendar = data.calendar || [];
        this.renderCalendar();
      }
    } catch (e) {
      console.warn('Failed to fetch calendar:', e);
    }
  }

  updateFlashTicker(article) {
    if (!this.flashTickerText || !article) return;
    this.flashTickerText.innerHTML = `
      <strong style="color: var(--cyan-neon);">[${article.source}]</strong> ${article.headline} 
      <span style="color: var(--gold-neon); font-size: 10px; margin-left: 8px;">(${article.time_str})</span>
    `;
  }

  renderArticles() {
    if (!this.wireContainer) return;
    this.wireContainer.innerHTML = '';

    let filtered = this.articles;
    if (this.activeCategory !== 'ALL') {
      filtered = filtered.filter((a) => a.category === this.activeCategory || a.tickers.some((t) => t.includes(this.activeCategory)));
    }

    if (this.searchQuery) {
      filtered = filtered.filter((a) => a.headline.toLowerCase().includes(this.searchQuery) || a.source.toLowerCase().includes(this.searchQuery));
    }

    if (filtered.length === 0) {
      this.wireContainer.innerHTML = '<div style="padding: 20px; color: var(--text-muted); font-family: var(--font-mono);">No news matching current filter.</div>';
      return;
    }

    filtered.forEach((art) => {
      const row = document.createElement('div');
      row.className = 'wire-item';
      
      const tickerTags = (art.tickers || []).map((t) => `<span class="ticker-tag">${t}</span>`).join('');
      const sourceClass = art.source.replace(' ', '');

      row.innerHTML = `
        <span class="wire-time">${art.time_str}</span>
        <span class="wire-source ${sourceClass}">${art.source}</span>
        <span class="wire-headline" title="${art.headline}">${art.headline}</span>
        <span class="wire-sentiment ${art.sentiment}">${art.sentiment_icon}</span>
        <div class="wire-tickers">${tickerTags}</div>
      `;

      row.addEventListener('click', () => {
        this.app.playSound('click');
        this.app.showToast(`[${art.source}] ${art.summary}`, 'info');
      });

      this.wireContainer.appendChild(row);
    });
  }

  renderCalendar() {
    if (!this.calendarContainer) return;
    this.calendarContainer.innerHTML = '';

    this.calendar.forEach((cal) => {
      const item = document.createElement('div');
      item.className = 'calendar-item';
      item.innerHTML = `
        <div>
          <div style="font-weight: 700; color: #f1f5f9;">${cal.currency} - ${cal.event}</div>
          <div style="font-size: 10px; color: var(--text-muted);">${cal.time} | F: ${cal.forecast} | P: ${cal.previous}</div>
        </div>
        <span class="${cal.impact === 'HIGH' ? 'impact-high' : 'badge badge-gold'}">${cal.impact}</span>
      `;
      this.calendarContainer.appendChild(item);
    });
  }
}
