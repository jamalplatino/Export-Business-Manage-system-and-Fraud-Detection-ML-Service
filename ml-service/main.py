from pathlib import Path
import json
import torch
import torch.nn as nn
from fastapi import FastAPI
from pydantic import BaseModel

MODEL_DIR = Path(__file__).parent / "models"
POINTER_FILE = MODEL_DIR / "current.txt"
SCALER_FILE = MODEL_DIR / "scaler.json"

FEATURE_COLS = [
    "log_amount", "hour", "dow",
    "cust_avg", "cust_count", "ratio_to_avg",
]


class FraudNet(nn.Module):
    """Same architecture as training — must match exactly."""
    def __init__(self, n_features):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(n_features, 16),
            nn.ReLU(),
            nn.Linear(16, 8),
            nn.ReLU(),
            nn.Linear(8, 1),
            nn.Sigmoid(),
        )

    def forward(self, x):
        return self.net(x)


class ScoreRequest(BaseModel):
    log_amount: float
    hour: int
    dow: int
    cust_avg: float
    cust_count: int
    ratio_to_avg: float


class ScoreResponse(BaseModel):
    is_fraud: bool
    probability: float
    model_version: str


def load_model():
    version = POINTER_FILE.read_text().strip()
    model_path = MODEL_DIR / version
    model = FraudNet(n_features=len(FEATURE_COLS))
    model.load_state_dict(torch.load(model_path, map_location="cpu"))
    model.eval()
    return model, version


def load_scaler():
    return json.loads(SCALER_FILE.read_text())


model, model_version = load_model()
scaler = load_scaler()

app = FastAPI(title="Fraud Detection ML Service", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok", "model_version": model_version}


@app.post("/score", response_model=ScoreResponse)
def score(req: ScoreRequest):
    features = []
    for col in FEATURE_COLS:
        val = getattr(req, col)
        mean = scaler[col]["mean"]
        std = scaler[col]["std"]
        features.append((val - mean) / std)

    x = torch.tensor([features], dtype=torch.float32)

    with torch.no_grad():
        prob = model(x).item()

    return ScoreResponse(
        is_fraud=prob > 0.5,
        probability=round(prob, 4),
        model_version=model_version,
    )


@app.post("/reload")
def reload_model():
    """Reload the model named in current.txt — no restart needed."""
    global model, model_version
    model, model_version = load_model()
    return {"status": "reloaded", "model_version": model_version}