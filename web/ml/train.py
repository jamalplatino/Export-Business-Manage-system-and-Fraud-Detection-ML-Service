import os
import sys
import django
from pathlib import Path

# Add the web/ directory to the path so "config.settings" is importable
WEB_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WEB_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()


import torch
import torch.nn as nn
import torch.optim as optim
from pathlib import Path
from ml.dataset import get_dataloaders, FEATURE_COLS
from ml.model import FraudNet


def train(epochs: int = 50, lr: float = 0.01):
    train_loader, test_loader = get_dataloaders(batch_size=8)

    model = FraudNet(n_features=len(FEATURE_COLS))
    loss_fn = nn.BCELoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)

    for epoch in range(epochs):
        model.train()
        total_loss = 0.0
        for X_batch, y_batch in train_loader:
            optimizer.zero_grad()
            preds = model(X_batch)
            loss = loss_fn(preds, y_batch)
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * len(X_batch)

        avg_loss = total_loss / len(train_loader.dataset)

        if (epoch + 1) % 10 == 0:
            print(f"Epoch {epoch+1:3d}/{epochs} | train loss: {avg_loss:.4f}")

    out_dir = Path(__file__).parent / "models"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "fraud_v1.pt"
    torch.save(model.state_dict(), out_path)
    print(f"\nModel saved to {out_path}")

    return model, test_loader


def evaluate(model, test_loader):
    model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for X_batch, y_batch in test_loader:
            preds = model(X_batch)
            predicted = (preds > 0.5).float()
            correct += (predicted == y_batch).sum().item()
            total += len(y_batch)
    print(f"Test accuracy: {correct / total:.4f} ({correct}/{total})")


if __name__ == "__main__":
    model, test_loader = train()
    evaluate(model, test_loader)