"""
Local metrics aggregation service.
Tracks application metrics in memory for monitoring and observability.
"""
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict
from dataclasses import dataclass, field, asdict
import threading


@dataclass
class MetricPoint:
    """A single metric data point."""
    timestamp: datetime
    value: float
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class Counter:
    """Counter metric that only increases."""
    name: str
    count: int = 0
    tags: Dict[str, str] = field(default_factory=dict)
    last_updated: Optional[datetime] = None
    
    def increment(self, value: int = 1):
        """Increment counter by value."""
        self.count += value
        self.last_updated = datetime.utcnow()


@dataclass
class Histogram:
    """Histogram metric for tracking distributions."""
    name: str
    values: List[float] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)
    max_size: int = 1000  # Keep last 1000 values
    
    def record(self, value: float):
        """Record a value in the histogram."""
        self.values.append(value)
        # Keep only recent values to prevent memory issues
        if len(self.values) > self.max_size:
            self.values = self.values[-self.max_size:]
    
    def get_stats(self) -> Dict[str, float]:
        """Calculate histogram statistics."""
        if not self.values:
            return {
                "count": 0,
                "sum": 0,
                "min": 0,
                "max": 0,
                "avg": 0,
                "p50": 0,
                "p95": 0,
                "p99": 0,
            }
        
        sorted_values = sorted(self.values)
        count = len(sorted_values)
        
        return {
            "count": count,
            "sum": sum(sorted_values),
            "min": sorted_values[0],
            "max": sorted_values[-1],
            "avg": sum(sorted_values) / count,
            "p50": sorted_values[int(count * 0.5)],
            "p95": sorted_values[int(count * 0.95)],
            "p99": sorted_values[int(count * 0.99)],
        }


class MetricsService:
    """
    Local metrics aggregation service.
    Tracks application metrics in memory.
    """
    
    def __init__(self, retention_hours: int = 24):
        """
        Initialize metrics service.
        
        Args:
            retention_hours: How long to keep metric data in hours
        """
        self.retention_hours = retention_hours
        self.counters: Dict[str, Counter] = {}
        self.histograms: Dict[str, Histogram] = {}
        self.time_series: Dict[str, List[MetricPoint]] = defaultdict(list)
        self._lock = threading.Lock()
    
    def _make_key(self, name: str, tags: Optional[Dict[str, str]] = None) -> str:
        """Create a unique key for a metric with tags."""
        if not tags:
            return name
        
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}{{{tag_str}}}"
    
    def increment_counter(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None) -> None:
        """
        Increment a counter metric.
        
        Args:
            name: Counter name
            value: Value to increment by
            tags: Optional tags for the metric
        """
        with self._lock:
            key = self._make_key(name, tags)
            
            if key not in self.counters:
                self.counters[key] = Counter(name=name, tags=tags or {})
            
            self.counters[key].increment(value)
    
    def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """
        Record a value in a histogram.
        
        Args:
            name: Histogram name
            value: Value to record
            tags: Optional tags for the metric
        """
        with self._lock:
            key = self._make_key(name, tags)
            
            if key not in self.histograms:
                self.histograms[key] = Histogram(name=name, tags=tags or {})
            
            self.histograms[key].record(value)
    
    def record_time_series(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """
        Record a time series data point.
        
        Args:
            name: Metric name
            value: Metric value
            tags: Optional tags for the metric
        """
        with self._lock:
            key = self._make_key(name, tags)
            
            self.time_series[key].append(
                MetricPoint(
                    timestamp=datetime.utcnow(),
                    value=value,
                    tags=tags or {},
                )
            )
            
            # Clean old data
            self._cleanup_time_series(key)
    
    def _cleanup_time_series(self, key: str) -> None:
        """Remove old time series data points."""
        cutoff = datetime.utcnow() - timedelta(hours=self.retention_hours)
        self.time_series[key] = [
            point for point in self.time_series[key]
            if point.timestamp > cutoff
        ]
    
    def get_counter(self, name: str, tags: Optional[Dict[str, str]] = None) -> Optional[Counter]:
        """Get a counter by name and tags."""
        key = self._make_key(name, tags)
        return self.counters.get(key)
    
    def get_histogram(self, name: str, tags: Optional[Dict[str, str]] = None) -> Optional[Histogram]:
        """Get a histogram by name and tags."""
        key = self._make_key(name, tags)
        return self.histograms.get(key)
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """
        Get all metrics as a dictionary.
        
        Returns:
            Dictionary containing all metrics
        """
        with self._lock:
            metrics = {
                "counters": {},
                "histograms": {},
                "timestamp": datetime.utcnow().isoformat(),
            }
            
            # Export counters
            for key, counter in self.counters.items():
                metrics["counters"][key] = {
                    "name": counter.name,
                    "count": counter.count,
                    "tags": counter.tags,
                    "last_updated": counter.last_updated.isoformat() if counter.last_updated else None,
                }
            
            # Export histograms
            for key, histogram in self.histograms.items():
                metrics["histograms"][key] = {
                    "name": histogram.name,
                    "tags": histogram.tags,
                    "stats": histogram.get_stats(),
                }
            
            return metrics
    
    def reset_metrics(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self.counters.clear()
            self.histograms.clear()
            self.time_series.clear()
    
    # Convenience methods for common application metrics
    
    def increment_api_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        error: bool = False,
    ) -> None:
        """
        Track an API request.
        
        Args:
            method: HTTP method
            path: Request path
            status_code: Response status code
            duration_ms: Request duration in milliseconds
            error: Whether the request resulted in an error
        """
        # Normalize path to avoid high cardinality
        normalized_path = self._normalize_path(path)
        
        tags = {
            "method": method,
            "path": normalized_path,
            "status": str(status_code),
        }
        
        # Increment request counter
        self.increment_counter("api_requests_total", tags=tags)
        
        # Record duration
        self.record_histogram("api_request_duration_ms", duration_ms, tags=tags)
        
        # Track errors
        if error or status_code >= 400:
            error_tags = {
                "method": method,
                "path": normalized_path,
                "status": str(status_code),
            }
            self.increment_counter("api_requests_errors_total", tags=error_tags)
    
    def increment_validation_execution(
        self,
        validator_type: str,
        success: bool,
        duration_ms: float,
    ) -> None:
        """
        Track a validation execution.
        
        Args:
            validator_type: Type of validator
            success: Whether validation succeeded
            duration_ms: Validation duration in milliseconds
        """
        tags = {
            "validator_type": validator_type,
            "status": "success" if success else "failure",
        }
        
        # Increment execution counter
        self.increment_counter("validation_executions_total", tags=tags)
        
        # Record duration
        self.record_histogram("validation_duration_ms", duration_ms, tags=tags)
        
        # Track success/failure
        if success:
            self.increment_counter("validation_success_total", tags={"validator_type": validator_type})
        else:
            self.increment_counter("validation_failure_total", tags={"validator_type": validator_type})
    
    def increment_ingestion_execution(
        self,
        dataset: str,
        success: bool,
        records_processed: int,
        duration_ms: float,
    ) -> None:
        """
        Track an ingestion execution.
        
        Args:
            dataset: Dataset name
            success: Whether ingestion succeeded
            records_processed: Number of records processed
            duration_ms: Ingestion duration in milliseconds
        """
        tags = {
            "dataset": dataset,
            "status": "success" if success else "failure",
        }
        
        # Increment execution counter
        self.increment_counter("ingestion_executions_total", tags=tags)
        
        # Record duration
        self.record_histogram("ingestion_duration_ms", duration_ms, tags=tags)
        
        # Record records processed
        self.increment_counter("ingestion_records_processed_total", records_processed, tags={"dataset": dataset})
        
        # Track success/failure
        if success:
            self.increment_counter("ingestion_success_total", tags={"dataset": dataset})
        else:
            self.increment_counter("ingestion_failure_total", tags={"dataset": dataset})
    
    def _normalize_path(self, path: str) -> str:
        """
        Normalize API path to reduce cardinality.
        Replaces IDs and UUIDs with placeholders.
        """
        import re
        
        # Replace UUIDs
        path = re.sub(
            r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            ':id',
            path,
            flags=re.IGNORECASE
        )
        
        # Replace numeric IDs
        path = re.sub(r'/\d+', '/:id', path)
        
        return path


# Global metrics service instance
_metrics_service: Optional[MetricsService] = None


def get_metrics_service() -> MetricsService:
    """Get the global metrics service instance."""
    global _metrics_service
    if _metrics_service is None:
        _metrics_service = MetricsService()
    return _metrics_service
