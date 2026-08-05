import math
from typing import Dict, Any, List

def norm_cdf(x: float) -> float:
    """Standard normal cumulative distribution function using math.erf."""
    return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0

def norm_pdf(x: float) -> float:
    """Standard normal probability density function."""
    return math.exp(-x*x / 2.0) / math.sqrt(2.0 * math.pi)

class BlackScholesEngine:
    def __init__(self, r: float = 0.05):
        self.r = r  # Risk-free rate
        
    def calculate_greeks(self, S: float, K: float, T: float, sigma: float, option_type: str = 'c') -> Dict[str, float]:
        """Calculate fair value and Greeks."""
        if T <= 0:
            T = 1e-5
            
        d1 = (math.log(S / K) + (self.r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        
        if option_type == 'c':
            price = S * norm_cdf(d1) - K * math.exp(-self.r * T) * norm_cdf(d2)
            delta = norm_cdf(d1)
            theta = (-S * norm_pdf(d1) * sigma / (2 * math.sqrt(T)) 
                     - self.r * K * math.exp(-self.r * T) * norm_cdf(d2))
        else:
            price = K * math.exp(-self.r * T) * norm_cdf(-d2) - S * norm_cdf(-d1)
            delta = norm_cdf(d1) - 1
            theta = (-S * norm_pdf(d1) * sigma / (2 * math.sqrt(T)) 
                     + self.r * K * math.exp(-self.r * T) * norm_cdf(-d2))
                     
        gamma = norm_pdf(d1) / (S * sigma * math.sqrt(T))
        vega = S * norm_pdf(d1) * math.sqrt(T)
        
        return {
            "fair_value": price,
            "delta": delta,
            "gamma": gamma,
            "theta": theta / 365.0,  # Per day
            "vega": vega / 100.0     # Per 1% volatility change
        }

    def analyze_option_strike_valuation(self, market_price: float, fair_value: float) -> str:
        """Rates strikes as CHEAP/FAIR/EXPENSIVE."""
        ratio = market_price / fair_value if fair_value > 0 else 1.0
        if ratio < 0.90:
            return "CHEAP"
        elif ratio > 1.10:
            return "EXPENSIVE"
        return "FAIR"
