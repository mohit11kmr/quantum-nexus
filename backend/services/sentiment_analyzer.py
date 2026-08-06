"""
Sentiment Analyzer - real implementation backed by the live RSS NewsScanner.

Keeps the previous SentimentAnalyzer API surface (analyze_news) so existing
callers keep working, but now returns real market sentiment from live news
instead of a random number.
"""

from typing import Dict, Any

from services.news_scanner import news_scanner


class SentimentAnalyzer:
    def __init__(self):
        self._scanner = news_scanner

    def analyze_news(self, symbol: str) -> Dict[str, Any]:
        """Live news sentiment scoring from RSS headlines (bullish/bearish/neutral)."""
        return self._scanner.analyze_sentiment(symbol)
