import torch
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from ml.features import build_features

FEATURE_COLS = [
    "log_amount",
    "hour",
    "dow",
    "cust_avg",
    "cust_count",
    "ratio_to_avg",
]
TARGET_COL = "is_fraud"


class FraudDataset(Dataset):
    """Wraps a pandas DataFrame as a PyTorch Dataset."""

    def __init__(self, X, y):
        self.X = torch.tensor(X.values, dtype=torch.float32)
        self.y = torch.tensor(y.values, dtype=torch.float32).unsqueeze(1)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, index):
        return self.X[index], self.y[index]


def get_dataloaders(batch_size: int = 8, test_size: float = 0.3):
    df = build_features()
    if df.empty:
        raise ValueError("No payment data. Add payments before training.")

    # Standardize features — neural nets train much better on scaled input
    X = df[FEATURE_COLS].copy()
    for col in FEATURE_COLS:
        mean = X[col].mean()
        std = X[col].std() or 1.0
        X[col] = (X[col] - mean) / std

    y = df[TARGET_COL]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=y
    )

    train_ds = FraudDataset(X_train, y_train)
    test_ds = FraudDataset(X_test, y_test)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False)

    return train_loader, test_loader