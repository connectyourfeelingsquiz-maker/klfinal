"""
KLFINAL Prediction Engine
Loads the trained KL1 (joblib) and KLED2 (pkl) models and executes
their original feature engineering and prediction pipelines.
"""

import os
import sys
import urllib.request
import itertools
from pathlib import Path
from typing import Dict, List, Any, Tuple
import numpy as np
import pandas as pd
import joblib

# Compatibility shim for scikit-learn cross-version unpickling
try:
    import sklearn.compose._column_transformer as _ct
    if not hasattr(_ct, '_RemainderColsList'):
        class _RemainderColsList(list):
            pass
        _ct._RemainderColsList = _RemainderColsList
except Exception:
    pass


class ModelService:
    def __init__(self, base_dir: Path | None = None):
        if base_dir is None:
            # Backend is at E:/klfinal/backend, project root is E:/klfinal
            base_dir = Path(__file__).resolve().parent.parent
        self.base_dir = Path(base_dir)
        
        self.kl1_pkg: Dict[str, Any] | None = None
        self.kled2_pkg: Dict[str, Any] | None = None
        self.lottery_names: List[str] = []
        self._is_loaded = False

    def _get_writable_target(self, filename: str) -> Path:
        """Returns a writable destination path (handles read-only serverless filesystems)."""
        candidate_dirs = [
            self.base_dir / "models",
            Path("/tmp/models"),
            Path("/tmp")
        ]
        for d in candidate_dirs:
            try:
                d.mkdir(parents=True, exist_ok=True)
                test_file = d / f".write_test_{os.getpid()}"
                test_file.touch()
                test_file.unlink()
                return d / filename
            except (OSError, PermissionError):
                continue
        return Path("/tmp") / filename

    def _download_binary_file(self, url: str, target: Path, filename: str) -> Path:
        """
        Streams a large model binary from external URL (GitHub Releases, S3, GCS, R2)
        with custom User-Agent, chunked streaming, redirect handling, and validation.
        """
        print(f"[ModelService] Downloading binary model from: {url}")
        print(f"[ModelService] Destination path: {target}")
        
        target.parent.mkdir(parents=True, exist_ok=True)
        temp_target = target.with_suffix(".download.tmp")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        req = urllib.request.Request(url, headers=headers)
        
        try:
            with urllib.request.urlopen(req, timeout=180) as response:
                content_type = response.headers.get("Content-Type", "")
                if "text/html" in content_type:
                    preview = response.read(250).decode("utf-8", errors="ignore")
                    raise RuntimeError(
                        f"Download URL returned an HTML page instead of a binary file. "
                        f"Ensure you provided a direct download link (e.g. GitHub Releases direct asset link). "
                        f"Response preview: {preview[:120]}..."
                    )
                
                downloaded_bytes = 0
                chunk_size = 1024 * 1024  # 1MB buffer
                with open(temp_target, "wb") as out_f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        out_f.write(chunk)
                        downloaded_bytes += len(chunk)
                        if downloaded_bytes % (25 * 1024 * 1024) == 0:
                            print(f"[ModelService] Downloaded {downloaded_bytes // (1024 * 1024)} MB...")
                
                # Check for Git LFS pointer or invalid small file (< 1MB)
                if downloaded_bytes < 1024 * 1024:
                    with open(temp_target, "rb") as check_f:
                        content_sample = check_f.read(200)
                    if b"version https://git-lfs" in content_sample:
                        raise RuntimeError(
                            f"Downloaded file from {url} is a Git LFS pointer text file ({downloaded_bytes} bytes), "
                            f"not the actual binary model. Download direct release assets instead of raw Git blob links."
                        )
                    raise RuntimeError(
                        f"Downloaded file is suspiciously small ({downloaded_bytes} bytes). Expected binary model > 90 MB."
                    )
                
                if target.exists():
                    target.unlink()
                temp_target.rename(target)
                print(f"[ModelService] Successfully saved '{filename}' ({target.stat().st_size} bytes) to {target}")
                return target
        except Exception as e:
            if temp_target.exists():
                try:
                    temp_target.unlink()
                except Exception:
                    pass
            raise RuntimeError(f"Failed to download model binary from {url}: {e}") from e

    def _verify_not_lfs_pointer(self, path: Path, filename: str) -> Path:
        """
        Detects if a model file is only a Git LFS pointer instead of actual binary.
        If a remote download URL is provided in environment variables, downloads it.
        Returns the resolved binary model path.
        """
        if not path.exists():
            return path

        file_size = path.stat().st_size
        if file_size < 1024:
            try:
                with open(path, "rb") as f:
                    header = f.read(50)
                if b"version https://git-lfs" in header:
                    print(f"[ModelService WARNING] '{filename}' is a Git LFS pointer text file ({file_size} bytes), not the binary model!")
                    env_var_key = "MODEL_KL1_URL" if "joblib" in filename else "MODEL_KLED2_URL"
                    download_url = os.environ.get(env_var_key) or os.environ.get("MODEL_STORAGE_URL")
                    if download_url:
                        target = self._get_writable_target(filename)
                        return self._download_binary_file(download_url, target, filename)

                    raise RuntimeError(
                        f"Model file '{filename}' at {path} is an unpulled Git LFS pointer ({file_size} bytes). "
                        f"On serverless hosts like Vercel, configure '{env_var_key}' environment variable pointing to "
                        f"your GitHub Release direct download URL or Cloud Storage bucket."
                    )
            except Exception as e:
                if isinstance(e, RuntimeError):
                    raise
                print(f"[ModelService] Could not check LFS header: {e}")
        return path

    def _resolve_model_path(self, filename: str) -> Path:
        """Find model file across candidate paths including root, models/, /tmp, and cwd."""
        model_env = os.environ.get("MODEL_DIR")
        candidates = [
            self.base_dir / "models" / filename,
            self.base_dir / filename,
            Path("/tmp/models") / filename,
            Path("/tmp") / filename,
            Path.cwd() / "models" / filename,
            Path.cwd().parent / "models" / filename,
            Path("/app/models") / filename,  # Container standard
            Path(model_env).resolve() / filename if model_env else None,
            Path.cwd() / filename,
        ]
        
        valid_candidates = [p for p in candidates if p is not None]
        for p in valid_candidates:
            if p.exists() and p.is_file():
                actual_path = self._verify_not_lfs_pointer(p, filename)
                return actual_path

        # If not found locally, check if remote URL is provided in environment
        env_var_key = "MODEL_KL1_URL" if "joblib" in filename else "MODEL_KLED2_URL"
        download_url = os.environ.get(env_var_key)
        if download_url:
            target_file = self._get_writable_target(filename)
            return self._download_binary_file(download_url, target_file, filename)

        raise FileNotFoundError(
            f"Model file '{filename}' not found in candidates: {[str(c) for c in valid_candidates]}. "
            f"Set MODEL_DIR or {env_var_key} environment variable."
        )

    def load_models(self) -> None:
        """Loads both ML models once into memory."""
        if self._is_loaded:
            return

        kl1_path = self._resolve_model_path("kerala_lottery_model.joblib")
        kled2_path = self._resolve_model_path("kerala_lottery_model.pkl")

        print(f"[ModelService] Loading KL1 model from: {kl1_path} ({kl1_path.stat().st_size} bytes)")
        self.kl1_pkg = joblib.load(kl1_path)

        print(f"[ModelService] Loading KLED2 model from: {kled2_path} ({kled2_path.stat().st_size} bytes)")
        self.kled2_pkg = joblib.load(kled2_path)

        # Extract lottery names from both models
        kl1_lotteries = set(self.kl1_pkg.get("lottery_names", []))
        kled2_lotteries = set(self.kled2_pkg.get("lottery_names", []))
        
        # Combine or fallback to common set
        all_lotteries = sorted(list(kl1_lotteries | kled2_lotteries))
        if not all_lotteries:
            # Default known Kerala Lottery list from training dataset
            all_lotteries = [
                'Akshaya', 'Bhagyanidhi', 'Bhagyathara', 'Dhanalekshmi',
                'Fifty-Fifty', 'Karunya', 'Karunya Plus', 'Nirmal',
                'Pournami', 'Samrudhi', 'Sthree Sakthi', 'Suvarna Keralam', 'Win Win'
            ]
        self.lottery_names = all_lotteries
        self._is_loaded = True
        print(f"[ModelService] Models successfully loaded. Valid lotteries ({len(self.lottery_names)}): {self.lottery_names}")

    def validate_lottery(self, lottery: str) -> str:
        """Validates and canonicalizes lottery name against model training classes."""
        if not self._is_loaded:
            self.load_models()
        
        for name in self.lottery_names:
            if name.lower() == lottery.strip().lower():
                return name
        raise ValueError(
            f"Invalid lottery name '{lottery}'. Supported lotteries are: {', '.join(self.lottery_names)}"
        )

    @staticmethod
    def extract_date_components(date_str: str) -> Tuple[int, int, int, int, int]:
        """Parses date string YYYY-MM-DD into year, month, day, weekday, day_of_year."""
        dt = pd.to_datetime(date_str)
        year = int(dt.year)
        month = int(dt.month)
        day = int(dt.day)
        weekday = int(dt.weekday())  # 0=Monday, 6=Sunday
        day_of_year = int(dt.dayofyear)
        return year, month, day, weekday, day_of_year

    def build_kl1_features(self, date_str: str, lottery: str) -> pd.DataFrame:
        """Exact original KL1 feature engineering."""
        year, month, day, weekday, day_of_year = self.extract_date_components(date_str)
        return pd.DataFrame([{
            'YEAR': year,
            'MONTH': month,
            'DAY': day,
            'WEEKDAY': weekday,
            'DAY_OF_YEAR': day_of_year,
            'LOTTERY NAME': lottery
        }])

    def build_kled2_features(self, date_str: str, lottery: str) -> pd.DataFrame:
        """Exact original KLED2 cyclical date feature engineering."""
        year, month, day, weekday, day_of_year = self.extract_date_components(date_str)
        
        month_sin = float(np.sin(2.0 * np.pi * month / 12.0))
        month_cos = float(np.cos(2.0 * np.pi * month / 12.0))
        weekday_sin = float(np.sin(2.0 * np.pi * weekday / 7.0))
        weekday_cos = float(np.cos(2.0 * np.pi * weekday / 7.0))
        year_day_sin = float(np.sin(2.0 * np.pi * day_of_year / 365.25))
        year_day_cos = float(np.cos(2.0 * np.pi * day_of_year / 365.25))

        return pd.DataFrame([{
            'YEAR': year,
            'MONTH': month,
            'DAY': day,
            'WEEKDAY': weekday,
            'DAY_OF_YEAR': day_of_year,
            'MONTH_SIN': month_sin,
            'MONTH_COS': month_cos,
            'WEEKDAY_SIN': weekday_sin,
            'WEEKDAY_COS': weekday_cos,
            'YEAR_DAY_SIN': year_day_sin,
            'YEAR_DAY_COS': year_day_cos,
            'LOTTERY NAME': lottery
        }])

    def predict_kl1(self, kl1_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Generate top five candidates using the six digit models:
        - predict_proba()
        - Top three digit classes per model
        - itertools.product() (3^6 = 729 combinations)
        - Multiply digit probabilities for ranking
        - Sort and return top five candidates
        """
        if not self._is_loaded or self.kl1_pkg is None:
            self.load_models()

        models = self.kl1_pkg["models"]
        digit_probs = []

        for i, m in enumerate(models):
            probs = m.predict_proba(kl1_df)[0]
            classes = m.classes_
            # Sort probabilities descending and take top 3
            top3_indices = np.argsort(probs)[::-1][:3]
            top3 = [(int(classes[idx]), float(probs[idx])) for idx in top3_indices]
            digit_probs.append(top3)

        # Generate all 3^6 = 729 candidate products
        all_combos = itertools.product(*digit_probs)
        candidates = []
        for combo in all_combos:
            number_str = "".join(str(d[0]) for d in combo)
            score = float(np.prod([d[1] for d in combo]))
            candidates.append((number_str, score))

        # Sort descending by score
        candidates.sort(key=lambda x: x[1], reverse=True)
        top5 = candidates[:5]

        return [
            {
                "rank": rank + 1,
                "candidate": num,
                "score": round(score, 8)
            }
            for rank, (num, score) in enumerate(top5)
        ]

    def predict_kled2(self, kled2_df: pd.DataFrame) -> Dict[str, str]:
        """
        Use the six models' predict() methods and combine the six digits
        into one six-digit result, preserving leading zeros.
        """
        if not self._is_loaded or self.kled2_pkg is None:
            self.load_models()

        models = self.kled2_pkg["models"]
        digits = []
        for m in models:
            pred = m.predict(kled2_df)[0]
            # Convert prediction to single integer digit string
            digits.append(str(int(pred)))

        six_digit_result = "".join(digits)
        # Ensure length is 6 preserving leading zeros
        if len(six_digit_result) < 6:
            six_digit_result = six_digit_result.zfill(6)

        return {
            "prediction": six_digit_result
        }

    def predict(self, date_str: str, lottery: str) -> Dict[str, Any]:
        """Runs predictions for both KL1 and KLED2 on the common input."""
        valid_lottery = self.validate_lottery(lottery)
        kl1_df = self.build_kl1_features(date_str, valid_lottery)
        kled2_df = self.build_kled2_features(date_str, valid_lottery)

        kl1_result = self.predict_kl1(kl1_df)
        kled2_result = self.predict_kled2(kled2_df)

        return {
            "success": True,
            "date": date_str,
            "lottery": valid_lottery,
            "kl1": {
                "candidates": kl1_result
            },
            "kled2": kled2_result
        }


# Singleton service instance
service = ModelService()
