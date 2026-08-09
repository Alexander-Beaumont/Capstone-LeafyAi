#!/usr/bin/env python3
from __future__ import annotations

import json
from contextlib import ExitStack
from pathlib import Path

MODEL_VERSION = "LeafyCV1.0"


class CVApiClient:
    def __init__(self, *, url: str = "", api_key: str = "", timeout: float = 5.0):
        self.url = (url or "").strip()
        self.api_key = (api_key or "").strip()
        self.timeout = max(0.5, float(timeout))

    @property
    def enabled(self) -> bool:
        return bool(self.url)

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "User-Agent": MODEL_VERSION,
            "X-Leafy-CV-Version": MODEL_VERSION,
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def send_sample(
        self,
        *,
        payload: dict,
        raw_path: Path,
        annotated_path: Path,
        mask_path: Path,
        image_mode: str = "raw",
    ) -> bool:
        if not self.enabled:
            return False

        try:
            import requests
        except ImportError:
            print(
                "API WARNING: install requests to enable backend sending. "
                "Local files are still safe."
            )
            return False

        try:
            if image_mode == "none":
                response = requests.post(
                    self.url,
                    json=payload,
                    headers=self._headers(),
                    timeout=self.timeout,
                )
            else:
                with ExitStack() as stack:
                    files = {}

                    raw_file = stack.enter_context(raw_path.open("rb"))
                    files["raw_image"] = (
                        raw_path.name,
                        raw_file,
                        "image/jpeg",
                    )

                    if image_mode == "all":
                        annotated_file = stack.enter_context(
                            annotated_path.open("rb")
                        )
                        mask_file = stack.enter_context(mask_path.open("rb"))
                        files["annotated_image"] = (
                            annotated_path.name,
                            annotated_file,
                            "image/jpeg",
                        )
                        files["mask_image"] = (
                            mask_path.name,
                            mask_file,
                            "image/png",
                        )

                    response = requests.post(
                        self.url,
                        data={"metadata": json.dumps(payload)},
                        files=files,
                        headers=self._headers(),
                        timeout=self.timeout,
                    )

            if 200 <= response.status_code < 300:
                print(
                    f"API: {MODEL_VERSION} sample accepted "
                    f"(HTTP {response.status_code})"
                )
                return True

            print(
                f"API WARNING: HTTP {response.status_code}: "
                f"{response.text[:500]}"
            )
            return False

        except Exception as exc:
            print(
                f"API WARNING: send failed: {exc}. "
                "CV continues and local CSV/images remain saved."
            )
            return False
