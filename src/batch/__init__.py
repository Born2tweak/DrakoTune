"""Batch processing: run the pipeline over a directory of vocals."""

from src.batch.runner import BatchItem, BatchSummary, run_batch

__all__ = ["run_batch", "BatchSummary", "BatchItem"]
