import torch
import torch.nn as nn
import numpy as np
import pandas as pd
from pathlib import Path
import json

class ContextClassifier(nn.Module):
    def __init__(self, input_size=28, num_classes=3):
        super(ContextClassifier, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(input_size, 32),
            nn.ReLU(),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, num_classes),
            nn.Softmax(dim=1)
        )

    def forward(self, x):
        return self.net(x)

def main():
    # 1. Load Data
    data_path = Path("data/context_features.csv")
    names_path = Path("artifacts/feature_names.json")
    
    if not data_path.exists() or not names_path.exists():
        print("[ERROR] Data or feature names not found.")
        return

    feature_names = json.loads(names_path.read_text())
    df = pd.read_csv(data_path)
    
    # Simple label mapping for demo data
    # Assuming stationary, walking, transit_like -> 0, 1, 2
    label_map = {"stationary": 0, "walking": 1, "transit_like": 2}
    df['label_idx'] = df['context_label'].map(label_map).fillna(0).astype(int)

    X = torch.tensor(df[feature_names].values.astype(np.float32))
    y = torch.tensor(df['label_idx'].values).long()

    # 2. Train
    model = ContextClassifier(input_size=len(feature_names), num_classes=3)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

    print("Training Context Classifier (.pt2)...")
    for epoch in range(100):
        optimizer.zero_grad()
        outputs = model(X)
        loss = criterion(outputs, y)
        loss.backward()
        optimizer.step()
        if (epoch+1) % 25 == 0:
            print(f'Epoch [{epoch+1}/100], Loss: {loss.item():.4f}')

    model.eval()

    # 3. Export
    example_input = torch.randn(1, len(feature_names))
    print("Exporting Context model to .pt2...")
    try:
        exported_program = torch.export.export(model, (example_input,))
        output_path = Path("artifacts/context_classifier.pt2")
        torch.export.save(exported_program, output_path)
        print(f"[OK] Saved to {output_path}")
    except Exception as e:
        print(f"[ERROR] Failed to export .pt2: {e}")
        traced = torch.jit.trace(model, example_input)
        traced.save("artifacts/context_classifier.pt")
        print("[OK] Fallback to .pt saved.")

    np.save("artifacts/context_classifier_sample_input.npy", example_input.numpy())

if __name__ == "__main__":
    main()
