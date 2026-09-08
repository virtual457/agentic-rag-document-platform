from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Any

from src.config import get_settings
from src.observability.logger import get_logger

log = get_logger("metrics")


class MetricsEmitter:
    def __init__(self) -> None:
        settings = get_settings()
        self._namespace = settings.cloudwatch_namespace
        self._enabled = settings.enable_metrics
        self._region = settings.aws_region
        self._cw: Any | None = None
        if self._enabled and settings.aws_access_key_id:
            try:
                import boto3

                self._cw = boto3.client("cloudwatch", region_name=self._region)
            except Exception as e:
                log.warning("metrics.cloudwatch_init_failed", error=str(e))

    def emit(self, name: str, value: float, unit: str = "Count", dims: dict[str, str] | None = None) -> None:
        if not self._enabled:
            return
        log.info("metric", name=name, value=value, unit=unit, dims=dims or {})
        if self._cw is None:
            return
        try:
            self._cw.put_metric_data(
                Namespace=self._namespace,
                MetricData=[
                    {
                        "MetricName": name,
                        "Value": float(value),
                        "Unit": unit,
                        "Dimensions": [{"Name": k, "Value": v} for k, v in (dims or {}).items()],
                    }
                ],
            )
        except Exception as e:
            log.warning("metrics.emit_failed", error=str(e))


emitter = MetricsEmitter()


@contextmanager
def timed(name: str, dims: dict[str, str] | None = None):
    start = time.time()
    try:
        yield
    finally:
        elapsed_ms = (time.time() - start) * 1000
        emitter.emit(name, elapsed_ms, unit="Milliseconds", dims=dims)
