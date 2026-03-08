import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import pickle

def train():
    print("Training Delay Prediction Model (Scikit-learn)...")
    # Synthetic training data
    # Features: weather (encoded), traffic (encoded), congestion (binary)
    np.random.seed(42)
    data = []
    
    for _ in range(2000):
        # 0:Clear, 1:Rain, 2:Snow, 3:Storm
        weather = np.random.choice([0, 1, 2, 3], p=[0.7, 0.15, 0.10, 0.05]) 
        # 0:Low, 1:Moderate, 2:Heavy, 3:Gridlock
        traffic = np.random.choice([0, 1, 2, 3], p=[0.5, 0.3, 0.15, 0.05]) 
        # 0:Normal, 1:Warehouse Congestion
        congestion = np.random.choice([0, 1], p=[0.95, 0.05])
        
        risk = (weather * 15) + (traffic * 20) + (congestion * 50) + np.random.randint(-5, 5)
        
        if risk > 65:
            label = 2 # Major Delay (High Risk)
        elif risk > 35:
            label = 1 # Minor Delay (Medium Risk)
        else:
            label = 0 # On Time (Low Risk)
            
        data.append([weather, traffic, congestion, label])
        
    df = pd.DataFrame(data, columns=['weather', 'traffic', 'congestion', 'label'])
    
    X = df[['weather', 'traffic', 'congestion']]
    y = df['label']
    
    model = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
    model.fit(X, y)
    
    import os
    model_path = os.path.join(os.path.dirname(__file__), "..", "models", "delay_model.pkl")
    
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
        
    print(f"Model trained and saved to {model_path}")

if __name__ == "__main__":
    train()
