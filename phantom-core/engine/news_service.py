import time
import asyncio
import httpx
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional

class MacroNewsService:
    """
    High-Speed Async Macroeconomic & Forex News Aggregator.
    Aggregates multi-tier RSS feeds (Fed, FXStreet, CNBC, Bloomberg mirrors, MarketWatch),
    tags entities ($GOLD, $USD, $EUR, $JPY, $FED), computes sentiment (▲ / ▼), and checks High-Impact calendar.
    """

    DEFAULT_FEEDS = [
        {"id": "fed-press", "source": "FEDERAL RESERVE", "url": "https://www.federalreserve.gov/feeds/press_all.xml", "category": "FED", "tier": 1},
        {"id": "fxstreet-news", "source": "FXSTREET", "url": "https://www.fxstreet.com/rss/news", "category": "FOREX", "tier": 1},
        {"id": "cnbc-markets", "source": "CNBC", "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114", "category": "MARKETS", "tier": 2},
        {"id": "marketwatch", "source": "MARKETWATCH", "url": "https://feeds.marketwatch.com/marketwatch/topstories/", "category": "MARKETS", "tier": 2},
        {"id": "oilprice", "source": "OILPRICE", "url": "https://oilprice.com/rss/main", "category": "COMMODITIES", "tier": 2}
    ]

    def __init__(self):
        self.cached_articles: List[Dict[str, Any]] = []
        self.last_fetch_ts: float = 0
        self.economic_calendar: List[Dict[str, Any]] = self._init_economic_calendar()
        self._init_mock_articles()

    def _init_mock_articles(self):
        """Pre-populates institutional grade wire news for instant display."""
        now = int(time.time())
        self.cached_articles = [
            {
                "id": "art-1",
                "headline": "Fed Signals Data-Dependent Path as Core Inflation Moderates in Latest Reading",
                "source": "FEDERAL RESERVE",
                "category": "FED",
                "time_str": "2m ago",
                "timestamp": now - 120,
                "sentiment": "NEUTRAL",
                "sentiment_icon": "▲",
                "impact": "HIGH",
                "tickers": ["$USD", "$FED", "$CPI"],
                "summary": "Federal Reserve officials noted continued progress on inflation while emphasizing caution ahead of upcoming policy decisions.",
                "url": "https://federalreserve.gov"
            },
            {
                "id": "art-2",
                "headline": "Gold Surges Toward $2,670 Resistance on Strong Institutional Safe-Haven Inflows",
                "source": "FXSTREET",
                "category": "GOLD",
                "time_str": "6m ago",
                "timestamp": now - 360,
                "sentiment": "BULLISH",
                "sentiment_icon": "▲",
                "impact": "HIGH",
                "tickers": ["$GOLD", "$XAUUSD", "$USD"],
                "summary": "Spot Gold (XAUUSD) gathered aggressive bullish momentum following central bank reserve accumulation and treasury yield retreat.",
                "url": "https://fxstreet.com"
            },
            {
                "id": "art-3",
                "headline": "ECB Officials Reiterate Gradual Rate Cuts as Eurozone Growth Shows Resilient Pockets",
                "source": "BLOOMBERG",
                "category": "FOREX",
                "time_str": "14m ago",
                "timestamp": now - 840,
                "sentiment": "NEUTRAL",
                "sentiment_icon": "▼",
                "impact": "MEDIUM",
                "tickers": ["$EUR", "$EURUSD", "$ECB"],
                "summary": "European Central Bank policymakers signaled confidence in bringing inflation back to target with measured rate adjustments.",
                "url": "https://bloomberg.com"
            },
            {
                "id": "art-4",
                "headline": "Bank of Japan Watches Currency Volatility Closely Ahead of Policy Review",
                "source": "NIKKEI",
                "category": "FOREX",
                "time_str": "22m ago",
                "timestamp": now - 1320,
                "sentiment": "BEARISH",
                "sentiment_icon": "▼",
                "impact": "HIGH",
                "tickers": ["$JPY", "$USDJPY", "$BOJ"],
                "summary": "BOJ officials monitored yen exchange rate dynamics and wage growth indices prior to the upcoming quarter meeting.",
                "url": "https://nikkei.com"
            },
            {
                "id": "art-5",
                "headline": "US Dollar Index (DXY) Consolidates Near 103.50 as Yields Ease",
                "source": "MARKETWATCH",
                "category": "MACRO",
                "time_str": "35m ago",
                "timestamp": now - 2100,
                "sentiment": "BEARISH",
                "sentiment_icon": "▼",
                "impact": "MEDIUM",
                "tickers": ["$DXY", "$USD", "$BONDS"],
                "summary": "The greenback held inside tight dealing ranges as bond traders recalibrated rate trajectory expectations.",
                "url": "https://marketwatch.com"
            }
        ]

    def _init_economic_calendar(self) -> List[Dict[str, Any]]:
        """Institutional Red Folder High-Impact Calendar for Forex & Gold."""
        return [
            {"time": "13:30 UTC", "currency": "USD", "event": "Core CPI (YoY)", "forecast": "3.1%", "previous": "3.2%", "impact": "HIGH", "status": "UPCOMING"},
            {"time": "15:00 UTC", "currency": "USD", "event": "Fed Chair Powell Speaks", "forecast": "-", "previous": "-", "impact": "HIGH", "status": "UPCOMING"},
            {"time": "19:00 UTC", "currency": "USD", "event": "FOMC Meeting Minutes", "forecast": "-", "previous": "-", "impact": "HIGH", "status": "UPCOMING"},
            {"time": "08:00 UTC", "currency": "EUR", "event": "German Flash Manufacturing PMI", "forecast": "42.8", "previous": "42.5", "impact": "MEDIUM", "status": "COMPLETED"},
            {"time": "07:00 UTC", "currency": "GBP", "event": "UK Claimant Count Change", "forecast": "+14.5K", "previous": "+20.5K", "impact": "MEDIUM", "status": "COMPLETED"}
        ]

    def tag_article_entities(self, text: str) -> List[str]:
        """Automatically tags asset symbols from article text."""
        tickers = []
        upper_text = text.upper()
        if "GOLD" in upper_text or "XAU" in upper_text: tickers.append("$GOLD")
        if "DOLLAR" in upper_text or "USD" in upper_text: tickers.append("$USD")
        if "EURO" in upper_text or "EUR" in upper_text: tickers.append("$EUR")
        if "YEN" in upper_text or "JPY" in upper_text: tickers.append("$JPY")
        if "FED" in upper_text or "POWELL" in upper_text: tickers.append("$FED")
        if "CPI" in upper_text or "INFLATION" in upper_text: tickers.append("$CPI")
        if "OIL" in upper_text or "CRUDE" in upper_text: tickers.append("$OIL")
        if not tickers: tickers.append("$MACRO")
        return list(set(tickers))

    def compute_sentiment(self, text: str) -> Dict[str, str]:
        """Heuristic financial sentiment scoring."""
        upper = text.upper()
        bull_words = ["SURGES", "GAINS", "RALLIES", "JUMPS", "BULLISH", "EXPANDS", "BEATS", "REBOUNDS", "RISES"]
        bear_words = ["DROPS", "SINKS", "FALLS", "PLUNGES", "BEARISH", "INFLATION RISES", "SLUMPS", "WEAKENS", "DECLINES"]

        bull_count = sum(1 for w in bull_words if w in upper)
        bear_count = sum(1 for w in bear_words if w in upper)

        if bull_count > bear_count:
            return {"sentiment": "BULLISH", "icon": "▲"}
        elif bear_count > bull_count:
            return {"sentiment": "BEARISH", "icon": "▼"}
        return {"sentiment": "NEUTRAL", "icon": "●"}

    async def fetch_live_rss(self) -> List[Dict[str, Any]]:
        """Async RSS parser for live tier 1/2 feeds."""
        new_articles = []
        async with httpx.AsyncClient(timeout=8.0) as client:
            for feed in self.DEFAULT_FEEDS:
                try:
                    resp = await client.get(feed["url"], headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
                    if resp.status_code == 200:
                        root = ET.fromstring(resp.text)
                        # RSS 2.0 item parsing
                        for item in root.findall(".//item")[:4]:
                            title = item.find("title")
                            link = item.find("link")
                            desc = item.find("description")
                            
                            headline = title.text.strip() if title is not None and title.text else ""
                            if not headline: continue

                            sent_info = self.compute_sentiment(headline)
                            tickers = self.tag_article_entities(headline)

                            new_articles.append({
                                "id": f"rss-{abs(hash(headline))}",
                                "headline": headline,
                                "source": feed["source"],
                                "category": feed["category"],
                                "time_str": "Just now",
                                "timestamp": int(time.time()),
                                "sentiment": sent_info["sentiment"],
                                "sentiment_icon": sent_info["icon"],
                                "impact": "HIGH" if "$FED" in tickers or "$CPI" in tickers else "MEDIUM",
                                "tickers": tickers,
                                "summary": desc.text[:180] if desc is not None and desc.text else headline,
                                "url": link.text.strip() if link is not None and link.text else "#"
                            })
                except Exception:
                    pass

        if new_articles:
            # Merge & deduplicate
            existing_ids = {a["id"] for a in self.cached_articles}
            for a in new_articles:
                if a["id"] not in existing_ids:
                    self.cached_articles.insert(0, a)
            self.cached_articles = self.cached_articles[:50]

        self.last_fetch_ts = time.time()
        return self.cached_articles

    def get_articles(self, category: str = "ALL") -> List[Dict[str, Any]]:
        if category == "ALL":
            return self.cached_articles
        return [a for a in self.cached_articles if a["category"] == category or any(category.lower() in t.lower() for t in a["tickers"])]

    def get_macro_context_for_ai(self) -> Dict[str, Any]:
        """Provides concise summary of top news & upcoming red folder calendar for AI reasoning."""
        top_3_news = [a["headline"] for a in self.cached_articles[:3]]
        upcoming_red_folders = [e for e in self.economic_calendar if e["impact"] == "HIGH" and e["status"] == "UPCOMING"]
        return {
            "breaking_macro_headlines": top_3_news,
            "upcoming_red_folder_events": upcoming_red_folders,
            "macro_risk_warning": "HIGH VOLATILITY EXPECTED (Red Folder Event Approaching)" if upcoming_red_folders else "NORMAL RISK ENVIRONMENT"
        }
