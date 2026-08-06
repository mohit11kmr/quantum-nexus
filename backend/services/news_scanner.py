"""
Real News & Sentiment Scanner.

Fetches live market news from Google News RSS (no API key required) using only
stdlib (urllib + xml.etree) and scores each headline with a transparent
bullish/bearish lexicon. Replaces the previous random/simulated sentiment.
"""

import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, Any, List

NEWS_FEED = "https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
CACHE_TTL_SEC = 300  # 5 minutes
MAX_ARTICLES = 15
TIMEOUT_SEC = 10

BULLISH_TERMS = [
    "rally", "surge", "surges", "soar", "soars", "gain", "gains", "gainers",
    "up", "rises", "rise", "hit record high", "all-time high", "record high",
    "bull", "bullish", "beat", "beats", "positive", "upgrade", "upgraded",
    "buy", "strong", "recover", "rebound", "jump", "jumps", "climb", "climbs",
    "outperform", "growth", "profit", "profits", "expansion",
]
BEARISH_TERMS = [
    "fall", "falls", "drop", "drops", "slump", "slumps", "sell-off", "selloff",
    "crash", "crashes", "bear", "bearish", "decline", "declines", "down",
    "cut", "cuts", "downgrade", "downgraded", "warning", "worst", "weak",
    "plunge", "plunges", "loss", "losses", "underperform", "correction",
    "pressure", "concern", "concerns", "hit", "slides", "slides", "tumble",
]

SYMBOL_QUERIES = {
    "NIFTY": "NIFTY 50 OR Indian stock market OR Sensex",
    "^NSEI": "NIFTY 50 OR Indian stock market OR Sensex",
    "BANKNIFTY": "BANK NIFTY OR Nifty Bank OR banking stocks India",
    "^NSEBANK": "BANK NIFTY OR Nifty Bank OR banking stocks India",
    "FINNIFTY": "Nifty Financial Services index",
    "^CNXFIN": "Nifty Financial Services index",
    "RELIANCE.NS": "Reliance Industries stock",
}


def _build_query(symbol: str) -> str:
    sym = symbol.strip().upper()
    if sym in SYMBOL_QUERIES:
        return SYMBOL_QUERIES[sym]
    if sym.endswith(".NS") or sym.endswith(".BO"):
        return f"{sym[:-3]} stock India"
    if sym.startswith("^"):
        return sym[1:]
    return f"{sym} stock India"


def _fetch_rss(query: str) -> List[Dict[str, Any]]:
    url = NEWS_FEED.format(query=urllib.parse.quote(query))
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as resp:
        data = resp.read().decode("utf-8", "ignore")
    root = ET.fromstring(data)
    items = []
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = item.findtext("link") or ""
        pub = item.findtext("pubDate") or ""
        source_el = item.find("source")
        source = source_el.text.strip() if source_el is not None and source_el.text else "Google News"
        if not title:
            continue
        items.append({"title": title, "source": source, "url": link, "published": pub})
    return items


def _score_text(text: str) -> Dict[str, Any]:
    lower = " " + text.lower() + " "
    bulls = sum(1 for t in BULLISH_TERMS if t in lower)
    bears = sum(1 for t in BEARISH_TERMS if t in lower)
    total = bulls + bears
    if total == 0:
        return {"score": 0.0, "label": "NEUTRAL", "bullish_terms": 0, "bearish_terms": 0}
    score = (bulls - bears) / max(total, 1)
    if score > 0.2:
        label = "BULLISH"
    elif score < -0.2:
        label = "BEARISH"
    else:
        label = "NEUTRAL"
    return {"score": round(score, 3), "label": label, "bullish_terms": bulls, "bearish_terms": bears}


class NewsScanner:
    def __init__(self, cache_ttl: int = CACHE_TTL_SEC):
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, Dict] = {}

    def _cached_or_fetch(self, symbol: str) -> List[Dict[str, Any]]:
        entry = self._cache.get(symbol)
        if entry and (time.time() - entry["ts"] < self.cache_ttl):
            return entry["articles"]
        try:
            articles = _fetch_rss(_build_query(symbol))[:MAX_ARTICLES]
        except Exception:
            articles = []
        self._cache[symbol] = {"ts": time.time(), "articles": articles}
        return articles

    def fetch_news(self, symbol: str, limit: int = MAX_ARTICLES) -> List[Dict[str, Any]]:
        articles = self._cached_or_fetch(symbol)[:limit]
        for a in articles:
            a["sentiment"] = _score_text(a["title"])
        return articles

    def analyze_sentiment(self, symbol: str) -> Dict[str, Any]:
        articles = self.fetch_news(symbol)
        if not articles:
            return {
                "symbol": symbol,
                "sentiment_score": 0.0,
                "classification": "NEUTRAL",
                "sources_analyzed": 0,
                "articles": [],
                "note": "No news articles could be fetched (offline or feed unavailable)",
            }
        scores = [a["sentiment"]["score"] for a in articles]
        avg = sum(scores) / len(scores)
        bulls = sum(1 for s in scores if s > 0)
        bears = sum(1 for s in scores if s < 0)
        if avg > 0.15:
            classification = "BULLISH"
        elif avg < -0.15:
            classification = "BEARISH"
        else:
            classification = "NEUTRAL"
        return {
            "symbol": symbol,
            "sentiment_score": round(avg, 3),
            "classification": classification,
            "bullish_articles": bulls,
            "bearish_articles": bears,
            "sources_analyzed": len(articles),
            "analyzed_at": datetime.now().isoformat(timespec="seconds"),
            "articles": articles,
        }


news_scanner = NewsScanner()
