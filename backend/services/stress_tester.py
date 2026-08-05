from typing import Dict, Any

class StressTester:
    def __init__(self):
        self.scenarios = [
            "MARKET_CRASH", 
            "VOLATILITY_SPIKE", 
            "SUSTAINED_DECLINE", 
            "GAP_DOWN_OPEN", 
            "LIQUIDITY_CRUNCH"
        ]
        
    def run_stress_test(self, portfolio: Dict[str, Any]) -> Dict[str, Any]:
        results = {}
        for scenario in self.scenarios:
            if scenario == "MARKET_CRASH":
                impact = -0.20
            elif scenario == "VOLATILITY_SPIKE":
                impact = -0.05
            elif scenario == "SUSTAINED_DECLINE":
                impact = -0.15
            elif scenario == "GAP_DOWN_OPEN":
                impact = -0.10
            elif scenario == "LIQUIDITY_CRUNCH":
                impact = -0.08
            else:
                impact = 0.0
                
            results[scenario] = {
                "impact_pct": impact * 100,
                "estimated_loss": portfolio.get('capital', 100000) * abs(impact)
            }
            
        return {
            "status": "COMPLETED",
            "scenarios_tested": len(self.scenarios),
            "results": results
        }
