"""
Unit and integration tests for KLFINAL prediction service and API routes.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from prediction import service
from main import app
from fastapi.testclient import TestClient

def test_prediction_service():
    print("\n--- 1. Testing Model Service Loading ---")
    service.load_models()
    assert service._is_loaded, "Models should be loaded"
    assert len(service.lottery_names) == 13, f"Expected 13 lotteries, got {len(service.lottery_names)}"
    print(f"PASS: Loaded {len(service.lottery_names)} lotteries: {service.lottery_names}")

    print("\n--- 2. Testing KL1 & KLED2 Prediction ---")
    res = service.predict("2026-11-15", "Karunya")
    assert res["success"] is True
    assert res["date"] == "2026-11-15"
    assert res["lottery"] == "Karunya"

    # KL1 check
    kl1_candidates = res["kl1"]["candidates"]
    assert len(kl1_candidates) == 5, f"Expected 5 candidates, got {len(kl1_candidates)}"
    for c in kl1_candidates:
        assert len(c["candidate"]) == 6, f"Candidate {c['candidate']} must be 6 digits"
        assert c["score"] > 0, "Candidate score should be positive"
    print(f"PASS: KL1 generated 5 candidates: {kl1_candidates}")

    # KLED2 check
    kled2_pred = res["kled2"]["prediction"]
    assert len(kled2_pred) == 6, f"KLED2 prediction {kled2_pred} must be 6 digits"
    assert kled2_pred.isdigit(), "KLED2 prediction must be digits"
    print(f"PASS: KLED2 generated 1 prediction: {kled2_pred}")

def test_api_endpoints():
    print("\n--- 3. Testing FastAPI Endpoints ---")
    client = TestClient(app)

    # Root
    r_root = client.get("/")
    assert r_root.status_code == 200
    print("PASS: GET / returned 200")

    # Health
    r_health = client.get("/api/health")
    assert r_health.status_code == 200
    data_health = r_health.json()
    assert data_health["status"] == "healthy"
    assert data_health["models_loaded"] is True
    print(f"PASS: GET /api/health returned {data_health}")

    # Lotteries
    r_lotteries = client.get("/api/lotteries")
    assert r_lotteries.status_code == 200
    data_lotteries = r_lotteries.json()
    assert data_lotteries["success"] is True
    assert len(data_lotteries["lotteries"]) == 13
    print(f"PASS: GET /api/lotteries returned {len(data_lotteries['lotteries'])} lotteries")

    # Predict valid
    r_predict = client.post("/api/predict", json={"date": "2026-11-15", "lottery": "Win Win"})
    assert r_predict.status_code == 200
    data_predict = r_predict.json()
    assert data_predict["success"] is True
    assert len(data_predict["kl1"]["candidates"]) == 5
    assert len(data_predict["kled2"]["prediction"]) == 6
    print(f"PASS: POST /api/predict succeeded for 'Win Win'")
    print(f"      KL1 top candidate: {data_predict['kl1']['candidates'][0]}")
    print(f"      KLED2 prediction: {data_predict['kled2']['prediction']}")

    # Predict invalid lottery
    r_bad_lottery = client.post("/api/predict", json={"date": "2026-11-15", "lottery": "NonExistentLottery"})
    assert r_bad_lottery.status_code == 400
    print(f"PASS: POST /api/predict correctly rejected invalid lottery (400 Bad Request)")

    # Predict invalid date
    r_bad_date = client.post("/api/predict", json={"date": "invalid-date", "lottery": "Karunya"})
    assert r_bad_date.status_code == 422  # Pydantic validation error
    print(f"PASS: POST /api/predict correctly rejected invalid date format (422 Unprocessable Entity)")

if __name__ == "__main__":
    test_prediction_service()
    test_api_endpoints()
    print("\nALL BACKEND TESTS PASSED SUCCESSFULLY!")
