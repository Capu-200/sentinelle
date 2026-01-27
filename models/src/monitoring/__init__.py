"""
Monitoring des prédictions pour Vertex AI Model Monitoring.

Logging des inferences vers GCS (JSONL) pour alimenter Vertex.
"""

from .gcs_logger import log_inference_to_gcs

__all__ = ["log_inference_to_gcs"]
