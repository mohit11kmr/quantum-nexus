import math
from typing import Dict, Any, List

def norm_cdf(x: float) -> float:
    """Standard normal cumulative distribution function using math.erf."""
    return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0

def norm_pdf(x: float) -> float:
    """Standard normal probability density function."""
    return math.exp(-x * x / 2.0) / math.sqrt(2.0 * math.pi)

class BlackScholesEngine:
    def __init__(self, r: float = 0.05):
        self.r = r  # Default Risk-free rate

    def calculate_greeks(self, S: float, K: float, T: float, sigma: float, option_type: str = 'CE', r: float = None) -> Dict[str, float]:
        """Calculate fair value and Greeks (Delta, Gamma, Theta, Vega)."""
        rate = r if r is not None else self.r

        if T <= 0:
            T = 1e-5
        if sigma <= 0:
            sigma = 0.01

        d1 = (math.log(S / K) + (rate + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)

        opt_type = str(option_type).upper().strip()
        is_call = opt_type in ['C', 'CE', 'CALL']

        if is_call:
            price = S * norm_cdf(d1) - K * math.exp(-rate * T) * norm_cdf(d2)
            delta = norm_cdf(d1)
            theta = (-S * norm_pdf(d1) * sigma / (2 * math.sqrt(T)) 
                     - rate * K * math.exp(-rate * T) * norm_cdf(d2))
        else:
            price = K * math.exp(-rate * T) * norm_cdf(-d2) - S * norm_cdf(-d1)
            delta = norm_cdf(d1) - 1.0
            theta = (-S * norm_pdf(d1) * sigma / (2 * math.sqrt(T)) 
                     + rate * K * math.exp(-rate * T) * norm_cdf(-d2))

        gamma = norm_pdf(d1) / (S * sigma * math.sqrt(T))
        vega = S * norm_pdf(d1) * math.sqrt(T)

        return {
            "fair_value": round(max(0.05, price), 2),
            "delta": round(delta, 4),
            "gamma": round(gamma, 6),
            "theta": round(theta / 365.0, 4),  # Per day decay
            "vega": round(vega / 100.0, 4)     # Per 1% volatility change
        }

    def analyze_option_strike_valuation(self, market_price: float, fair_value: float) -> str:
        """Rates strikes as CHEAP/FAIR/EXPENSIVE."""
        ratio = market_price / fair_value if fair_value > 0 else 1.0
        if ratio < 0.90:
            return "CHEAP"
        elif ratio > 1.10:
            return "EXPENSIVE"
        return "FAIR"
