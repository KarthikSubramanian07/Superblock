import torch
import torch.nn as nn
import numpy as np
import pandas as pd
from pathlib import Path
import joblib

# Architecture matching the MLPRegressor we used in sklearn
class ALSModel(nn.Module):
    def __init__(self, input_size=8):
        super(ALSModel, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(input_size, 16),
            nn.ReLU(),
            nn.Linear(16, 8),
            nn.ReLU(),
            nn.Linear(8, 1)
        )

    def forward(self, x):
        return self.net(x)

def main():
    # 1. Load Data for a quick "Warm-up" Training
    data_path = Path("data/als_features_demo.csv")
    if not data_path.exists():
        print(f"[ERROR] Data not found at {data_path}")
        return

    df = pd.read_csv(data_path)
    # Match the ALS_FEATURE_NAMES order
    features = ['hrv_rmssd', 'hrv_sdnn', 'hrv_pnn50', 'hr_mean', 'hr_variance', 
                'skin_temp_delta', 'ambient_noise_db', 'accel_intensity_mean']
    
    X = torch.tensor(df[features].values.astype(np.float32))
    # Map labels to 0-1 range
    y = torch.tensor(df['als_target'].values.astype(np.float32)).view(-1, 1)

    # 2. Initialize and Train Model
    model = ALSModel(input_size=len(features))
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

    print("Training NPU-optimized PyTorch model...")
    for epoch in range(200):
        optimizer.zero_grad()
        outputs = model(X)
        loss = criterion(outputs, y)
        loss.backward()
        optimizer.step()
        if (epoch+1) % 50 == 0:
            print(f'Epoch [{epoch+1}/200], Loss: {loss.item():.4f}')

    model.eval()

    # 3. Export to .pt2 (Zetic Recommended Format)
    # Using torch.export which is the modern standard for static graphs
    print("Exporting to .pt2...")
    example_input = torch.randn(1, 8)
    
    # Modern torch.export (replaces torch.jit.trace for static graphs)
    try:
        exported_program = torch.export.export(model, (example_input,))
        output_path = Path("artifacts/als/als_model.pt2")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        torch.export.save(exported_program, output_path)
        print(f"[OK] Saved PyTorch Exported Program to {output_path}")
    except Exception as e:
        print(f"[ERROR] Failed to export using torch.export: {e}")
        print("Falling back to TorchScript (.pt)...")
        traced_model = torch.jit.trace(model, example_input)
        traced_model.save("artifacts/als/als_model.pt")
        print("[OK] Saved TorchScript model to artifacts/als/als_model.pt")

    # 4. Save sample input as .npy for Zetic
    np.save("artifacts/als/als_sample_input.npy", example_input.numpy())
    print("[OK] Saved sample input to artifacts/als/als_sample_input.npy")

if __name__ == "__main__":
    main()
