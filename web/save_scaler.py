"""
Run from web/ to save the training-time scaler for the ML service.
"""
import os
import sys
import json
from pathlib import Path

# --- Django bootstrap MUST come first ---
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()



import json
from pathlib import Path
from ml.features import build_features
from ml.dataset import FEATURE_COLS


def main():
    df = build_features()
    if df.empty:
        raise SystemExit("No payment data — add payments first.")

    scaler = {}
    for col in FEATURE_COLS:
        scaler[col] = {
            "mean": float(df[col].mean()),
            "std": float(df[col].std() or 1.0),
        }

    # Write to both locations
    web_out = Path(__file__).parent / "ml" / "models" / "scaler.json"
    web_out.parent.mkdir(parents=True, exist_ok=True)
    web_out.write_text(json.dumps(scaler, indent=2))
    print(f"Saved to {web_out}")

    # Also copy to ml-service
    ml_out = Path(__file__).parent.parent / "ml-service" / "models" / "scaler.json"
    if ml_out.parent.exists():
        ml_out.write_text(json.dumps(scaler, indent=2))
        print(f"Also saved to {ml_out}")


if __name__ == "__main__":
    import os
    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()
    main()