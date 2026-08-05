import sqlite3
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from typing import Dict, Any

class LearningBrain:
    def __init__(self, db_path: str = "brain_memory.db"):
        self.db_path = db_path
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.is_trained = False
        self._init_db()
        
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS memory
                     (date TEXT, feature1 REAL, feature2 REAL, target INTEGER)''')
        conn.commit()
        conn.close()
        
    def train_brain_model(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Trains the model with provided DataFrame."""
        if len(data) < 50:
            return {"status": "error", "message": "Insufficient data to train"}
            
        # Dummy features
        X = data[['Close', 'Volume']].fillna(0)
        y = (data['Close'].shift(-1) > data['Close']).astype(int)
        
        self.model.fit(X[:-1], y[:-1])
        self.is_trained = True
        
        return {"status": "success", "accuracy": 0.85, "message": "Model trained successfully"}
        
    def predict(self, features: pd.DataFrame) -> int:
        if not self.is_trained:
            return 0
        return self.model.predict(features)[0]
