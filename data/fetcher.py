import os
import time
import requests
import logging
import re
from typing import Optional, Dict, Any, List

from config.settings import MAX_RETRIES
from data.cache import ModelCache

logger = logging.getLogger(__name__)

class HFAPIError(Exception):
    pass

class RateLimitError(Exception):
    pass

class ModelNotFoundError(Exception):
    pass

class HFDataFetcher:
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.environ.get("HF_TOKEN")
        self.session = requests.Session()
        if self.token:
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        self.cache = ModelCache()
        self.base_url = "https://huggingface.co/api"

    def _make_request(self, url: str, params: Optional[Dict[str, Any]] = None) -> Any:
        retries = 0
        backoff = 1

        while retries <= MAX_RETRIES:
            try:
                response = self.session.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    raise RateLimitError("Rate limit exceeded")
                elif response.status_code == 404:
                    raise ModelNotFoundError(f"Resource not found: {url}")
                else:
                    raise HFAPIError(f"API Error {response.status_code}: {response.text}")
                    
            except RateLimitError:
                if retries == MAX_RETRIES:
                    raise
                logger.warning(f"Rate limited. Retrying in {backoff} seconds...")
                time.sleep(backoff)
                retries += 1
                backoff *= 2
            except (requests.RequestException, Exception) as e:
                if retries == MAX_RETRIES:
                    raise HFAPIError(f"Failed to fetch data: {e}")
                logger.warning(f"Request failed: {e}. Retrying in {backoff} seconds...")
                time.sleep(backoff)
                retries += 1
                backoff *= 2

    def fetch_model_info(self, model_id: str) -> Dict[str, Any]:
        # Handle cases where user pastes a full HuggingFace URL
        if "huggingface.co/" in model_id:
            model_id = model_id.split("huggingface.co/")[-1].strip("/")
            
        cached = self.cache.get_model(model_id)
        if cached:
            return cached

        url = f"{self.base_url}/models/{model_id}"
        params = {
            "expand[]": ["evalResults", "safetensors", "likes", "downloads"]
        }
        
        try:
            data = self._make_request(url, params=params)
            
            normalized = {
                "id": data.get("_id", model_id),
                "model_id": model_id,
                "downloads": data.get("downloads", 0),
                "likes": data.get("likes", 0),
                "tags": data.get("tags", []),
                "last_modified": data.get("lastModified"),
                "created_at": data.get("createdAt"),
                "pipeline_tag": data.get("pipeline_tag"),
                "library_name": data.get("library_name"),
                "param_count": self.extract_param_count(data),
                "is_abliterated": self.detect_abliterated(data),
            }
            
            quant_info = self.detect_quantized(data)
            normalized["is_quantized"] = quant_info["is_quantized"]
            normalized["quantization_formats"] = quant_info["formats"]
            
            self.cache.set_model(model_id, normalized)
            return normalized
        except ModelNotFoundError:
            raise

    def fetch_model_list(self, task: Optional[str] = None, sort: str = 'downloads', limit: int = 100, search: Optional[str] = None) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/models"
        params = {
            "sort": sort,
            "limit": limit
        }
        if task:
            params["pipeline_tag"] = task
        if search:
            params["search"] = search
            
        return self._make_request(url, params=params)

    def fetch_eval_results(self, model_id: str) -> List[Dict[str, Any]]:
        if "huggingface.co/" in model_id:
            model_id = model_id.split("huggingface.co/")[-1].strip("/")

        cached = self.cache.get_eval_results(model_id)
        if cached:
            return cached

        results = []

        # --- Source 1: HF native evalResults field (correct nested structure) ---
        try:
            url = f"{self.base_url}/models/{model_id}"
            data = self._make_request(url, params={"expand[]": "evalResults"})
            raw_evals = data.get("evalResults", [])

            # Map known HF eval dataset IDs → our benchmark IDs
            eval_id_map = {
                "Idavidrein/gpqa": "gpqa",
                "gpqa": "gpqa",
                "cais/mmlu": "mmlu-pro",
                "mmlu": "mmlu-pro",
                "mmlu-pro": "mmlu-pro",
                "gsm8k": "gsm8k",
                "openai_humaneval": "humaneval",
                "humaneval": "humaneval",
                "bbh": "bbh",
                "bigbench": "bbh",
                "math": "math",
                "ifeval": "ifeval",
                "musr": "musr",
                "hellaswag": "hellaswag",
                "truthfulqa": "truthfulqa",
                "winogrande": "winogrande",
                "arc": "arc",
            }

            for ev in raw_evals:
                # Actual structure: ev has 'data' dict with 'dataset.id' and 'value'
                ev_data = ev.get("data", ev)  # fallback to ev itself for old format
                dataset_info = ev_data.get("dataset", {})
                ds_id = (dataset_info.get("id") or dataset_info.get("name") or
                         ev.get("dataset", {}).get("name", "unknown")).lower()

                # Resolve to our canonical benchmark ID
                canonical_id = ds_id
                for pattern, mapped in eval_id_map.items():
                    if pattern in ds_id:
                        canonical_id = mapped
                        break

                val = ev_data.get("value")
                if val is None:
                    # Old format: nested metrics list
                    for metric in ev_data.get("metrics", []):
                        val = metric.get("value")
                        if val is not None:
                            break

                if val is not None:
                    try:
                        fval = float(val)
                        # Normalize: if score is 0-1 range, convert to 0-100
                        if fval <= 1.0 and fval >= 0:
                            fval *= 100
                        results.append({
                            "dataset_id": canonical_id,
                            "task_id": ev_data.get("dataset", {}).get("task_id", canonical_id),
                            "value": fval,
                            "verified": ev.get("verified", False),
                            "source": "hf_native",
                        })
                    except (TypeError, ValueError):
                        pass
        except Exception as e:
            logger.debug(f"HF native evalResults not available for {model_id}: {e}")


        # --- Source 2: Open LLM Leaderboard v2 results dataset ---
        # Pulls from the public parquet dataset hosted on HF Hub
        if not results:
            try:
                leaderboard_url = (
                    "https://datasets-server.huggingface.co/rows"
                    "?dataset=open-llm-leaderboard%2Fresults"
                    "&config=default&split=train&offset=0&length=1"
                    f"&where=model_name_or_path%3D%27{model_id}%27"
                )
                r = self.session.get(leaderboard_url, timeout=10)
                if r.status_code == 200:
                    rows = r.json().get("rows", [])
                    if rows:
                        row = rows[0].get("row", {})
                        # Map leaderboard columns to our benchmark IDs
                        bench_map = {
                            "IFEval": ("ifeval", True),
                            "BBH": ("bbh", True),
                            "MATH Lvl 5": ("math", True),
                            "GPQA": ("gpqa", True),
                            "MuSR": ("musr", True),
                            "MMLU-PRO": ("mmlu-pro", True),
                        }
                        for col, (bench_id, verified) in bench_map.items():
                            val = row.get(col)
                            if val is not None:
                                try:
                                    results.append({
                                        "dataset_id": bench_id,
                                        "task_id": bench_id,
                                        "value": float(val) * 100 if float(val) <= 1.0 else float(val),
                                        "verified": verified,
                                        "source": "open_llm_leaderboard_v2",
                                    })
                                except (TypeError, ValueError):
                                    pass
            except Exception as e:
                logger.debug(f"Open LLM Leaderboard lookup failed for {model_id}: {e}")

        # --- Source 3: Model card metrics (tags like mmlu=75.3) ---
        if not results:
            try:
                url = f"{self.base_url}/models/{model_id}"
                data = self._make_request(url, params={})
                card_data = data.get("cardData", {}) or {}
                model_results = card_data.get("model-results", card_data.get("results", []))
                for res in (model_results if isinstance(model_results, list) else []):
                    dataset = res.get("dataset", {})
                    ds_name = dataset.get("name", dataset.get("type", ""))
                    for task in res.get("task", [res.get("task", {})]):
                        if isinstance(task, dict):
                            for metric in task.get("metrics", []):
                                val = metric.get("value")
                                if val is not None and ds_name:
                                    try:
                                        results.append({
                                            "dataset_id": ds_name.lower().replace(" ", "-"),
                                            "task_id": task.get("type", ""),
                                            "value": float(val) * 100 if float(val) <= 1.0 else float(val),
                                            "verified": False,
                                            "source": "model_card",
                                        })
                                    except (TypeError, ValueError):
                                        pass
            except Exception as e:
                logger.debug(f"Model card metrics not available for {model_id}: {e}")

        self.cache.set_eval_results(model_id, results)
        return results

    def fetch_trending_models(self, limit: int = 20) -> List[str]:
        url = f"{self.base_url}/models"
        params = {"sort": "trending", "limit": limit}
        data = self._make_request(url, params=params)
        return [model.get("id", "") for model in data if "id" in model]

    def detect_abliterated(self, model_data: Dict[str, Any]) -> bool:
        tags = [t.lower() for t in model_data.get("tags", [])]
        card = str(model_data.get("cardData", "")).lower()
        
        keywords = ["abliterated", "uncensored", "ablation"]
        
        for kw in keywords:
            if kw in tags or kw in card:
                return True
        return False

    def detect_quantized(self, model_data: Dict[str, Any]) -> Dict[str, Any]:
        tags = [t.lower() for t in model_data.get("tags", [])]
        formats = []
        
        quant_tags = ["gguf", "awq", "gptq", "bnb", "exl2", "bitsandbytes"]
        for qt in quant_tags:
            if qt in tags:
                formats.append(qt)
                
        return {
            "is_quantized": len(formats) > 0,
            "formats": formats
        }

    def extract_param_count(self, model_data: Dict[str, Any]) -> Optional[int]:
        if "safetensors" in model_data and "total" in model_data["safetensors"]:
            return model_data["safetensors"]["total"]
            
        model_id = model_data.get("id", "").lower()
        tags = [t.lower() for t in model_data.get("tags", [])]
        
        match_str = f"{model_id} {' '.join(tags)}"
        match = re.search(r'(\d+(?:\.\d+)?)[bx]', match_str)
        if match:
            try:
                num = float(match.group(1))
                return int(num * 1e9)
            except ValueError:
                pass
                
        return None
