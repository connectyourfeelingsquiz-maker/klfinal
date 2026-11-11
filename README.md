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

### 1. Deploying Backend to Vercel (FastAPI Serverless)

Vercel hosts the backend as an ASGI Python Serverless Function via [`vercel.json`](vercel.json) and [`api/index.py`](api/index.py).

#### ⚠️ Critical Vercel Serverless Limitations & Workarounds
1. **250 MB Package Limit**:
   - Vercel enforces a strict **250 MB uncompressed size limit** on each Serverless Function.
   - Bundling both trained models (KL1 is 241 MB, KLED2 is 100 MB) alongside Python dependencies (~150 MB) totals **~491 MB**, which will fail Vercel deployment if uploaded directly.
   - **Solution**: [`models/`](models/) is excluded from Vercel function packaging via [`.vercelignore`](.vercelignore). During cold-start initialization, the backend automatically streams the models into `/tmp/models` if `MODEL_KL1_URL` and `MODEL_KLED2_URL` are provided in Vercel's Environment Variables.
2. **Execution Timeout**:
   - Vercel Hobby plan has a 10s–15s maximum execution timeout. Host your model files on a high-speed CDN (such as AWS S3, Cloudflare R2, Google Cloud Storage, or GitHub Release assets) so initial streaming stays within the threshold.
3. **Memory Limits**:
   - Vercel provides 1024 MB (1 GB) memory on Hobby plans, which comfortably accommodates both unpickled Scikit-Learn tree ensembles (~500 MB RAM).

#### Steps to Deploy Backend on Vercel:
1. Upload your model files (`kerala_lottery_model.joblib` and `kerala_lottery_model.pkl`) to an S3 bucket, Cloudflare R2, Google Cloud Storage, or a GitHub Release asset download link.
2. Log in to [Vercel.com](https://vercel.com) and click **Add New...** -> **Project**.
3. Import your GitHub repository.
4. Set the **Framework Preset** to **Other** (Root directory: `.`).
5. In **Environment Variables**, add:
   - `MODEL_KL1_URL`: Direct download URL for `kerala_lottery_model.joblib`
   - `MODEL_KLED2_URL`: Direct download URL for `kerala_lottery_model.pkl`
6. Click **Deploy**.
7. Copy your assigned Vercel URL (e.g., `https://klfinal-backend.vercel.app`).

---

### 2. Deploying Backend to Render (Alternative: Long-Running Container)

Render is recommended if you prefer persistent server instances without serverless cold-start timeouts or package size limits.
- Root Directory: `.`
- Build Command: `git lfs pull || true; pip install -r backend/requirements.txt`
- Start Command: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
- Environment Variables:
  - `MODEL_DIR`: `../models`
  - `PYTHON_VERSION`: `3.11.9`

---

### 3. Deploying Frontend to Netlify (React + Vite)

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
   - **Value**: `https://klfinal-backend.vercel.app` (Your Vercel backend URL)
6. Click **Deploy Site**.

`netlify.toml` automatically handles SPA routing and redirects.

---

## ⚠️ Disclaimer

> **Educational and experimental ML predictions only. Lottery results are random. Predictions are not guaranteed to win.**  
> This project is designed strictly for academic exploration of multi-estimator Scikit-Learn pipelines, probability product rankings, and cyclical trigonometric date transformations.
