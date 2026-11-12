"""
KLFINAL Prediction Engine
Loads the trained KL1 (joblib) and KLED2 (pkl) models and executes
their original feature engineering and prediction pipelines.

Vercel-optimized: Sequential download → hash verify → load → delete
to stay within 512 MB /tmp disk limit.
"""

import gc
import hashlib
import os
import shutil
import sys
import time
import urllib.request
import itertools
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
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

# Expected SHA256 hashes for model integrity verification
EXPECTED_HASHES = {
    "kerala_lottery_model.joblib": "cee51bf857681aba4d5db5dcf29af2fdb17af46443e4939aec27532606d250db",
    "kerala_lottery_model.pkl": "878dfd55b2f5045aa39a6386cfbb6ade4d87d72c18b505935c9352cb8704ad3c",
}


def _disk_space_info(path: str = "/tmp") -> Dict[str, str]:
    """Returns human-readable disk space for the given path."""
    try:
        usage = shutil.disk_usage(path)
        return {
            "total_mb": f"{usage.total / (1024 * 1024):.1f}",
            "used_mb": f"{usage.used / (1024 * 1024):.1f}",
            "free_mb": f"{usage.free / (1024 * 1024):.1f}",
        }
    except Exception as e:
        return {"error": str(e)}


def _sha256_file(path: Path) -> str:
    """Computes SHA256 hex digest of a file, streaming 1 MB chunks."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


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
        self._load_error: Optional[str] = None
        self._diagnostics: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # File-system helpers
    # ------------------------------------------------------------------

    def _get_writable_dir(self) -> Path:
        """Returns the first writable directory."""
        candidates = [
            self.base_dir / "models",
            Path("/tmp/models"),
            Path("/tmp"),
        ]
        for d in candidates:
            try:
                d.mkdir(parents=True, exist_ok=True)
                test_file = d / f".write_test_{os.getpid()}"
                test_file.touch()
                test_file.unlink()
                return d
            except (OSError, PermissionError):
                continue
        return Path("/tmp")

    # ------------------------------------------------------------------
    # Download with diagnostics
    # ------------------------------------------------------------------

    def _download_binary_file(self, url: str, target: Path, filename: str) -> Path:
        """
        Streams a large model binary from external URL with:
        - Custom User-Agent to bypass GitHub asset CDN browser checks
        - Chunked streaming (1 MB)
        - Redirect following (urllib default)
        - Git LFS pointer detection
        - Size validation
        - SHA256 hash verification
        """
        print(f"[ModelService] Downloading '{filename}' from: {url}")
        print(f"[ModelService] Target: {target}")
        print(f"[ModelService] Disk before download: {_disk_space_info(str(target.parent))}")

        target.parent.mkdir(parents=True, exist_ok=True)
        temp_target = target.with_suffix(".download.tmp")

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "application/octet-stream",
        }
        req = urllib.request.Request(url, headers=headers)

        try:
            t0 = time.time()
            with urllib.request.urlopen(req, timeout=300) as response:
                content_type = response.headers.get("Content-Type", "")
                content_length = response.headers.get("Content-Length", "unknown")
                final_url = response.url  # after redirects
                print(f"[ModelService] Final URL: {final_url}")
                print(f"[ModelService] Content-Type: {content_type}, Content-Length: {content_length}")

                if "text/html" in content_type:
                    preview = response.read(250).decode("utf-8", errors="ignore")
                    raise RuntimeError(
                        f"Download URL returned HTML instead of binary. "
                        f"Use a direct download link (e.g. GitHub Releases asset URL). "
                        f"Preview: {preview[:120]}..."
                    )

                downloaded_bytes = 0
                chunk_size = 1024 * 1024  # 1 MB
                with open(temp_target, "wb") as out_f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        out_f.write(chunk)
                        downloaded_bytes += len(chunk)
                        if downloaded_bytes % (50 * 1024 * 1024) < chunk_size:
                            elapsed = time.time() - t0
                            print(
                                f"[ModelService] ... {downloaded_bytes / (1024 * 1024):.1f} MB "
                                f"({elapsed:.1f}s)"
                            )

            elapsed = time.time() - t0
            print(
                f"[ModelService] Download complete: {downloaded_bytes:,} bytes "
                f"in {elapsed:.1f}s"
            )

            # ---- Validate downloaded file ----
            # 1. LFS pointer check
            if downloaded_bytes < 1024 * 1024:
                with open(temp_target, "rb") as f:
                    sample = f.read(200)
                if b"version https://git-lfs" in sample:
                    temp_target.unlink(missing_ok=True)
                    raise RuntimeError(
                        f"Downloaded file is a Git LFS pointer ({downloaded_bytes} bytes), "
                        f"NOT the binary model. Upload the actual model binary as a "
                        f"GitHub Release asset—do not use raw Git blob URLs."
                    )
                temp_target.unlink(missing_ok=True)
                raise RuntimeError(
                    f"Downloaded file is too small ({downloaded_bytes} bytes). "
                    f"Expected >90 MB binary model."
                )

            # 2. SHA256 hash verification
            actual_hash = _sha256_file(temp_target)
            expected_hash = (
                os.environ.get(
                    "MODEL_KL1_SHA256" if "joblib" in filename else "MODEL_KLED2_SHA256"
                )
                or EXPECTED_HASHES.get(filename)
            )
            if expected_hash and actual_hash != expected_hash:
                temp_target.unlink(missing_ok=True)
                raise RuntimeError(
                    f"SHA256 mismatch for '{filename}'!\n"
                    f"  Expected: {expected_hash}\n"
                    f"  Got:      {actual_hash}\n"
                    f"The download may be corrupted, truncated, or an LFS pointer page."
                )
            print(f"[ModelService] SHA256 verified: {actual_hash}")

            # Move temp → final
            if target.exists():
                target.unlink()
            temp_target.rename(target)
            print(f"[ModelService] Saved '{filename}': {target.stat().st_size:,} bytes")
            print(f"[ModelService] Disk after download: {_disk_space_info(str(target.parent))}")
            return target

        except Exception as e:
            if temp_target.exists():
                try:
                    temp_target.unlink()
                except Exception:
                    pass
            raise RuntimeError(f"Failed to download '{filename}' from {url}: {e}") from e

    # ------------------------------------------------------------------
    # Resolve a single model: local file or remote download
    # ------------------------------------------------------------------

    def _find_local_model(self, filename: str) -> Optional[Path]:
        """Searches local candidate directories for a real binary model file."""
        model_env = os.environ.get("MODEL_DIR")
        candidates = [
            self.base_dir / "models" / filename,
            self.base_dir / filename,
            Path("/tmp/models") / filename,
            Path("/tmp") / filename,
            Path.cwd() / "models" / filename,
            Path.cwd().parent / "models" / filename,
            Path("/app/models") / filename,
        ]
        if model_env:
            candidates.append(Path(model_env).resolve() / filename)
        candidates.append(Path.cwd() / filename)

        for p in candidates:
            if p is not None and p.exists() and p.is_file():
                size = p.stat().st_size
                # Detect Git LFS pointer
                if size < 1024:
                    try:
                        with open(p, "rb") as f:
                            header = f.read(50)
                        if b"version https://git-lfs" in header:
                            print(
                                f"[ModelService WARNING] '{p}' is an LFS pointer "
                                f"({size} bytes) — skipping."
                            )
                            continue
                    except Exception:
                        pass
                return p
        return None

    def _resolve_and_load_single_model(
        self, filename: str, env_url_key: str
    ) -> Any:
        """
        Resolves, downloads (if needed), loads into memory, and deletes the
        temp file for a single model.  Returns the deserialized model package.

        This keeps at most ONE model binary on disk at a time, critical for
        Vercel's 512 MB /tmp limit.
        """
        t0 = time.time()

        # 1. Try local path first (works in dev and container deployments)
        local_path = self._find_local_model(filename)
        if local_path:
            print(f"[ModelService] Found local '{filename}': {local_path} ({local_path.stat().st_size:,} bytes)")
            # Verify hash for local files too
            actual_hash = _sha256_file(local_path)
            expected_hash = EXPECTED_HASHES.get(filename)
            if expected_hash and actual_hash != expected_hash:
                print(
                    f"[ModelService WARNING] Local hash mismatch for '{filename}':\n"
                    f"  Expected: {expected_hash}\n"
                    f"  Got:      {actual_hash}\n"
                    f"  Loading anyway (model may have been retrained)."
                )
            else:
                print(f"[ModelService] Local SHA256 OK: {actual_hash}")
            pkg = joblib.load(local_path)
            elapsed = time.time() - t0
            print(f"[ModelService] Loaded '{filename}' from local in {elapsed:.1f}s")
            return pkg

        # 2. Remote download (Vercel / serverless)
        download_url = os.environ.get(env_url_key)
        if not download_url:
            raise FileNotFoundError(
                f"Model file '{filename}' not found locally and no download URL "
                f"configured.  Set the '{env_url_key}' environment variable to a "
                f"direct binary download URL (e.g. GitHub Releases asset)."
            )

        writable_dir = self._get_writable_dir()
        target = writable_dir / filename
        downloaded_path = self._download_binary_file(download_url, target, filename)

        # Load into memory
        print(f"[ModelService] Loading '{filename}' into memory...")
        pkg = joblib.load(downloaded_path)
        elapsed_load = time.time() - t0
        print(f"[ModelService] Loaded '{filename}' in {elapsed_load:.1f}s total")

        # Delete temp file to free /tmp disk for the next model
        try:
            downloaded_path.unlink()
            print(
                f"[ModelService] Deleted temp file '{downloaded_path}' to free disk. "
                f"Disk now: {_disk_space_info(str(writable_dir))}"
            )
        except Exception as e:
            print(f"[ModelService WARNING] Could not delete temp file: {e}")

        # Force a garbage collection to release any file-backed memory maps
        gc.collect()

        return pkg

    # ------------------------------------------------------------------
    # Public model loading
    # ------------------------------------------------------------------

    def load_models(self) -> None:
        """
        Loads both ML models into memory.

        On serverless (Vercel) the strategy is:
          1. Download KL1 → verify hash → load → delete temp file
          2. Download KLED2 → verify hash → load → delete temp file
        This avoids having both 241 MB + 100 MB on /tmp simultaneously.
        """
        if self._is_loaded:
            return

        self._load_error = None
        self._diagnostics = {"load_start": time.time()}

        print(f"[ModelService] base_dir = {self.base_dir}")
        print(f"[ModelService] Disk at start: {_disk_space_info('/tmp')}")

        try:
            # ---- KL1 (241 MB) — load first, delete temp, THEN load KLED2 ----
            self.kl1_pkg = self._resolve_and_load_single_model(
                "kerala_lottery_model.joblib", "MODEL_KL1_URL"
            )
            if not isinstance(self.kl1_pkg, dict) or "models" not in self.kl1_pkg:
                raise RuntimeError(
                    "KL1 model loaded but has unexpected structure "
                    f"(type={type(self.kl1_pkg).__name__}, "
                    f"keys={list(self.kl1_pkg.keys()) if isinstance(self.kl1_pkg, dict) else 'N/A'}). "
                    "Expected dict with 'models' key."
                )

            # ---- KLED2 (100 MB) ----
            self.kled2_pkg = self._resolve_and_load_single_model(
                "kerala_lottery_model.pkl", "MODEL_KLED2_URL"
            )
            if not isinstance(self.kled2_pkg, dict) or "models" not in self.kled2_pkg:
                raise RuntimeError(
                    "KLED2 model loaded but has unexpected structure "
                    f"(type={type(self.kled2_pkg).__name__}, "
                    f"keys={list(self.kled2_pkg.keys()) if isinstance(self.kled2_pkg, dict) else 'N/A'}). "
                    "Expected dict with 'models' key."
                )

        except Exception as e:
            self._load_error = str(e)
            self._is_loaded = False
            self.kl1_pkg = None
            self.kled2_pkg = None
            print(f"[ModelService ERROR] Model loading failed: {e}")
            raise

        # Extract lottery names from both models
        kl1_lotteries = set(self.kl1_pkg.get("lottery_names", []))
        kled2_lotteries = set(self.kled2_pkg.get("lottery_names", []))
        all_lotteries = sorted(list(kl1_lotteries | kled2_lotteries))
        if not all_lotteries:
            all_lotteries = [
                'Akshaya', 'Bhagyanidhi', 'Bhagyathara', 'Dhanalekshmi',
                'Fifty-Fifty', 'Karunya', 'Karunya Plus', 'Nirmal',
                'Pournami', 'Samrudhi', 'Sthree Sakthi', 'Suvarna Keralam', 'Win Win'
            ]
        self.lottery_names = all_lotteries
        self._is_loaded = True

        elapsed = time.time() - self._diagnostics["load_start"]
        self._diagnostics["load_time_s"] = round(elapsed, 1)
        self._diagnostics["kl1_models_count"] = len(self.kl1_pkg["models"])
        self._diagnostics["kled2_models_count"] = len(self.kled2_pkg["models"])
        self._diagnostics["lotteries_count"] = len(self.lottery_names)

        print(
            f"[ModelService] Models loaded successfully in {elapsed:.1f}s. "
            f"KL1 pipelines: {len(self.kl1_pkg['models'])}, "
            f"KLED2 pipelines: {len(self.kled2_pkg['models'])}, "
            f"Lotteries ({len(self.lottery_names)}): {self.lottery_names}"
        )
        print(f"[ModelService] Disk at end: {_disk_space_info('/tmp')}")

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
