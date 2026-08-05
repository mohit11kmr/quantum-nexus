import numpy as np
from typing import Dict, Any

class MonteCarloSimulator:
    def __init__(self, num_paths: int = 10000):
        self.num_paths = num_paths
        
    def simulate(self, S0: float, mu: float, sigma: float, T: float, steps: int = 252) -> Dict[str, Any]:
        """MonteCarloSimulator with 10,000 GBM paths."""
        dt = T / steps
        paths = np.zeros((steps + 1, self.num_paths))
        paths[0] = S0
        
        for t in range(1, steps + 1):
            Z = np.random.standard_normal(self.num_paths)
            paths[t] = paths[t - 1] * np.exp((mu - 0.5 * sigma ** 2) * dt + sigma * np.sqrt(dt) * Z)
            
        final_prices = paths[-1]
        returns = (final_prices - S0) / S0
        
        var_95 = np.percentile(returns, 5)
        var_99 = np.percentile(returns, 1)
        cvar_95 = returns[returns <= var_95].mean()
        
        max_drawdown = np.min(paths, axis=0) / S0 - 1
        avg_max_drawdown = max_drawdown.mean()
        
        return {
            "var_95": float(var_95),
            "var_99": float(var_99),
            "cvar_95": float(cvar_95),
            "avg_max_drawdown": float(avg_max_drawdown),
            "quantiles": {
                "25%": float(np.percentile(final_prices, 25)),
                "50%": float(np.percentile(final_prices, 50)),
                "75%": float(np.percentile(final_prices, 75))
            }
        }
