# KLFINAL - Dual Machine Learning Prediction System

> **Production-Ready Kerala Lottery Prediction Dashboard**  
> Educational and experimental ML prediction engine powered by **KL1** and **KLED2** trained models.

---

## 📌 Overview

**KLFINAL** is a production-grade full-stack web application designed to evaluate Kerala Lottery draw dates and lottery categories using two pre-trained machine learning architectures in parallel:

1. **KL1 Model (`kerala_lottery_model.joblib`)**:
   - **Architecture**: 6 discrete Scikit-Learn classification pipelines (one per digit position).
   - **Feature Inputs**: `YEAR`, `MONTH`, `DAY`, `WEEKDAY`, `DAY_OF_YEAR`, `LOTTERY NAME` (One-Hot Encoded).
   - **Inference Strategy**: `predict_proba()` produces the top 3 candidate classes for each digit. Combinatorial Cartesian expansion ($3^6 = 729$ candidates) evaluates joint probability products $\prod_{i=0}^5 P(D_i)$. The top 5 candidates are ranked and returned.

2. **KLED2 Model (`kerala_lottery_model.pkl`)**:
   - **Architecture**: Multi-algorithm ensemble (`RandomForestClassifier`, `ExtraTreesClassifier`) across 6 digit estimators.
   - **Feature Inputs**: 12 cyclical & temporal dimensions (`YEAR`, `MONTH`, `DAY`, `WEEKDAY`, `DAY_OF_YEAR`, `MONTH_SIN`, `MONTH_COS`, `WEEKDAY_SIN`, `WEEKDAY_COS`, `YEAR_DAY_SIN`, `YEAR_DAY_COS`, `LOTTERY NAME`).
   - **Inference Strategy**: Deterministic `predict()` on each digit model synthesized into an optimal 6-digit consensus result, strictly preserving leading zeros.

---

## 📁 Project Structure

```
klfinal/
├── backend/
│   ├── Dockerfile             # Production container definition
│   ├── main.py                # FastAPI endpoints, CORS, lifespan startup
│   ├── prediction.py          # Dual ML inference service & feature transforms
│   ├── requirements.txt       # Python dependencies
│   └── test_backend.py        # Automated test suite
├── frontend/
│   ├── index.html             # HTML entry point with dark mode
│   ├── netlify.toml           # Netlify build & rewrite configuration
│   ├── package.json           # Frontend dependencies & scripts
│   ├── postcss.config.js      # PostCSS configuration
│   ├── tailwind.config.js     # Tailwind CSS theme & custom colors
│   ├── tsconfig.json          # TypeScript config
│   ├── tsconfig.app.json      # App TypeScript config
│   ├── tsconfig.node.json     # Node TypeScript config
│   ├── vite.config.ts         # Vite bundler & dev proxy
│   ├── .env.example           # Example environment variables
│   └── src/
│       ├── App.tsx            # Main application coordinator & state
│       ├── main.tsx           # React DOM root
│       ├── index.css          # Glassmorphism & dark theme styles
│       └── components/
│           ├── Header.tsx         # Brand header & live API status indicator
│           ├── PredictionForm.tsx # Common date & lottery selector
│           ├── KL1Results.tsx     # Top 5 candidates card with rankings & scores
│           ├── KLED2Result.tsx    # Single prediction card with digit tiles
│           └── Footer.tsx         # Legal & educational disclaimer
├── models/
│   ├── kerala_lottery_model.joblib   # Pre-trained KL1 model package (241 MB)
│   └── kerala_lottery_model.pkl      # Pre-trained KLED2 model package (100 MB)
├── .gitattributes             # Git LFS tracking for model binaries
├── .gitignore                 # Ignore node_modules, pycache, dist
├── final.csv                  # Reference training dataset
├── render.yaml                # Render Blueprint infrastructure definition
└── README.md                  # Comprehensive documentation
```

---

## 🚀 Local Development

### Prerequisites
- **Python 3.10+** (Tested on Python 3.11 & 3.12)
- **Node.js v18+** and **npm v9+**

### 1. Backend Setup & Run

Open a terminal in the root directory:

```bash
# Navigate to backend
cd backend

# Install dependencies
pip install -r requirements.txt

# Run backend test suite to verify model loading & endpoints
python test_backend.py

# Start FastAPI development server
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

The backend API will be available at:
- API Root: `http://127.0.0.1:8000/`
- Interactive Swagger Docs: `http://127.0.0.1:8000/docs`
- Health Endpoint: `http://127.0.0.1:8000/api/health`

### 2. Frontend Setup & Run

Open a second terminal in the root directory:

```bash
# Navigate to frontend
cd frontend

# Install npm dependencies
npm install

# Start Vite dev server
npm run dev
```

The frontend dashboard will be available at:
- `http://localhost:5173/`

Vite is pre-configured with a reverse proxy forwarding `/api` requests to `http://127.0.0.1:8000`.

---

## 📡 API Reference

### 1. Health Check
`GET /api/health`

**Response:**
```json
{
  "status": "healthy",
  "models_loaded": true,
  "lotteries_count": 13
}
```

### 2. Supported Lotteries
`GET /api/lotteries`

**Response:**
```json
{
  "success": true,
  "count": 13,
  "lotteries": [
    "Akshaya",
    "Bhagyanidhi",
    "Bhagyathara",
    "Dhanalekshmi",
    "Fifty-Fifty",
    "Karunya",
    "Karunya Plus",
    "Nirmal",
    "Pournami",
    "Samrudhi",
    "Sthree Sakthi",
    "Suvarna Keralam",
    "Win Win"
  ]
}
```

### 3. Generate Predictions
`POST /api/predict`

**Request Body:**
```json
{
  "date": "2026-11-15",
  "lottery": "Karunya"
}
```

**Response Body:**
```json
{
  "success": true,
  "date": "2026-11-15",
  "lottery": "Karunya",
  "kl1": {
    "candidates": [
      { "rank": 1, "candidate": "709860", "score": 0.00006482 },
      { "rank": 2, "candidate": "759860", "score": 0.00006205 },
      { "rank": 3, "candidate": "709260", "score": 0.00006115 },
      { "rank": 4, "candidate": "706860", "score": 0.00006037 },
      { "rank": 5, "candidate": "759260", "score": 0.00005854 }
    ]
  },
  "kled2": {
    "prediction": "756500"
  }
}
```

---

## 🌐 Production Deployment

### 1. Deploying Backend to Render

Render hosts the Python FastAPI inference service.

#### Model Storage Consideration (GitHub 100MB File Limit)
`kerala_lottery_model.joblib` is ~241 MB. Standard GitHub rejects individual files larger than 100 MB. To push your repository to GitHub:

1. **Option A: Use Git LFS (Recommended)**
   ```bash
   git lfs install
   git lfs track "*.joblib" "*.pkl"
   git add .gitattributes models/
   git commit -m "Add model binaries with Git LFS"
   git push origin main
   ```
2. **Option B: Cloud Object Storage (S3 / Cloud Storage / Render Disk)**
   Upload `kerala_lottery_model.joblib` and `kerala_lottery_model.pkl` to an S3 or Google Cloud Storage bucket. On container startup, download them into `/app/models`.

#### Steps on Render:
1. Log in to [Render.com](https://render.com).
2. Click **New +** -> **Web Service**.
3. Connect your GitHub repository.
4. Select **Docker** (using `backend/Dockerfile`) or **Python**:
   - **Root Directory**: `.`
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Set Environment Variables:
   - `MODEL_DIR`: `../models`
   - `PYTHON_VERSION`: `3.11.9`
6. Click **Deploy Web Service**.
7. Copy your assigned Render URL (e.g. `https://klfinal-backend.onrender.com`).

---

### 2. Deploying Frontend to Netlify

Netlify hosts the high-performance React + Vite static bundle.

#### Steps on Netlify:
1. Log in to [Netlify.com](https://netlify.com).
2. Click **Add new site** -> **Import an existing project**.
3. Select your GitHub repository.
4. Set Build Settings:
   - **Base directory**: `frontend`
   - **Build command**: `npm run build`
   - **Publish directory**: `dist` (or `frontend/dist`)
5. In **Environment variables**, add:
   - **Key**: `VITE_API_URL`
   - **Value**: `https://klfinal-backend.onrender.com` (Your Render backend URL)
6. Click **Deploy Site**.

`frontend/netlify.toml` automatically handles SPA routing and redirects.

---

## ⚠️ Disclaimer

> **Educational and experimental ML predictions only. Lottery results are random. Predictions are not guaranteed to win.**  
> This project is designed strictly for academic exploration of multi-estimator Scikit-Learn pipelines, probability product rankings, and cyclical trigonometric date transformations.
