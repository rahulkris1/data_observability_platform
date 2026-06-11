"""Latency Service

Service for tracking and calculating ingestion and validation latency
"""
from datetime import datetime
from typing import Optional, Dict
from contextlib import contextmanager


class LatencyTracker:
    """Context manager for tracking operation latency
    
    Usage:
        with LatencyTracker() as tracker:
            # perform operation
            pass
        latency_seconds = tracker.get_latency_seconds()
    """
    
    def __init__(self):
        """Initialize latency tracker"""
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
    
    def __enter__(self):
        """Start tracking latency"""
        self.start_time = datetime.utcnow()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop tracking latency"""
        self.end_time = datetime.utcnow()
        return False
    
    def get_latency_seconds(self) -> Optional[float]:
        """Get latency in seconds
        
        Returns:
            Latency in seconds, or None if tracking incomplete
        """
        if self.start_time is None or self.end_time is None:
            return None
        
        delta = self.end_time - self.start_time
        return delta.total_seconds()
    
    def get_latency_milliseconds(self) -> Optional[float]:
        """Get latency in milliseconds
        
        Returns:
            Latency in milliseconds, or None if tracking incomplete
        """
        latency_seconds = self.get_latency_seconds()
        if latency_seconds is None:
            return None
        return latency_seconds * 1000.0


class LatencyService:
    """Service for tracking ingestion and validation latency
    
    Tracks start and end times for operations and calculates
    latency metrics.
    """
    
    def __init__(self):
        """Initialize latency service"""
        self._active_operations: Dict[str, Dict[str, datetime]] = {}
    
    def start_ingestion(self, operation_id: str) -> datetime:
        """Mark the start of an ingestion operation
        
        Args:
            operation_id: Unique identifier for the operation
            
        Returns:
            Start timestamp
        """
        start_time = datetime.utcnow()
        
        if operation_id not in self._active_operations:
            self._active_operations[operation_id] = {}
        
        self._active_operations[operation_id]["ingestion_start"] = start_time
        return start_time
    
    def complete_ingestion(self, operation_id: str) -> datetime:
        """Mark the completion of an ingestion operation
        
        Args:
            operation_id: Unique identifier for the operation
            
        Returns:
            End timestamp
        """
        end_time = datetime.utcnow()
        
        if operation_id not in self._active_operations:
            self._active_operations[operation_id] = {}
        
        self._active_operations[operation_id]["ingestion_end"] = end_time
        return end_time
    
    def start_validation(self, operation_id: str) -> datetime:
        """Mark the start of a validation operation
        
        Args:
            operation_id: Unique identifier for the operation
            
        Returns:
            Start timestamp
        """
        start_time = datetime.utcnow()
        
        if operation_id not in self._active_operations:
            self._active_operations[operation_id] = {}
        
        self._active_operations[operation_id]["validation_start"] = start_time
        return start_time
    
    def complete_validation(self, operation_id: str) -> datetime:
        """Mark the completion of a validation operation
        
        Args:
            operation_id: Unique identifier for the operation
            
        Returns:
            End timestamp
        """
        end_time = datetime.utcnow()
        
        if operation_id not in self._active_operations:
            self._active_operations[operation_id] = {}
        
        self._active_operations[operation_id]["validation_end"] = end_time
        return end_time
    
    def calculate_ingestion_latency(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> float:
        """Calculate ingestion latency in seconds
        
        Args:
            start_time: Ingestion start time
            end_time: Ingestion completion time
            
        Returns:
            Latency in seconds
        """
        delta = end_time - start_time
        return delta.total_seconds()
    
    def calculate_validation_latency(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> float:
        """Calculate validation latency in seconds
        
        Args:
            start_time: Validation start time
            end_time: Validation completion time
            
        Returns:
            Latency in seconds
        """
        delta = end_time - start_time
        return delta.total_seconds()
    
    def get_operation_latencies(
        self,
        operation_id: str
    ) -> Dict[str, Optional[float]]:
        """Get all latencies for an operation
        
        Args:
            operation_id: Unique identifier for the operation
            
        Returns:
            Dictionary with ingestion_latency, validation_latency, and total_latency
        """
        if operation_id not in self._active_operations:
            return {
                "ingestion_latency_seconds": None,
                "validation_latency_seconds": None,
                "total_latency_seconds": None,
            }
        
        op_data = self._active_operations[operation_id]
        
        # Calculate ingestion latency
        ingestion_latency = None
        if "ingestion_start" in op_data and "ingestion_end" in op_data:
            ingestion_latency = self.calculate_ingestion_latency(
                op_data["ingestion_start"],
                op_data["ingestion_end"]
            )
        
        # Calculate validation latency
        validation_latency = None
        if "validation_start" in op_data and "validation_end" in op_data:
            validation_latency = self.calculate_validation_latency(
                op_data["validation_start"],
                op_data["validation_end"]
            )
        
        # Calculate total latency
        total_latency = None
        if "ingestion_start" in op_data:
            # Find the latest end time
            end_time = None
            if "validation_end" in op_data:
                end_time = op_data["validation_end"]
            elif "ingestion_end" in op_data:
                end_time = op_data["ingestion_end"]
            
            if end_time:
                delta = end_time - op_data["ingestion_start"]
                total_latency = delta.total_seconds()
        
        return {
            "ingestion_latency_seconds": ingestion_latency,
            "validation_latency_seconds": validation_latency,
            "total_latency_seconds": total_latency,
        }
    
    def get_operation_timestamps(
        self,
        operation_id: str
    ) -> Dict[str, Optional[datetime]]:
        """Get all timestamps for an operation
        
        Args:
            operation_id: Unique identifier for the operation
            
        Returns:
            Dictionary with start and end timestamps
        """
        if operation_id not in self._active_operations:
            return {
                "ingestion_start_time": None,
                "ingestion_end_time": None,
                "validation_start_time": None,
                "validation_end_time": None,
            }
        
        op_data = self._active_operations[operation_id]
        
        return {
            "ingestion_start_time": op_data.get("ingestion_start"),
            "ingestion_end_time": op_data.get("ingestion_end"),
            "validation_start_time": op_data.get("validation_start"),
            "validation_end_time": op_data.get("validation_end"),
        }
    
    def cleanup_operation(self, operation_id: str) -> None:
        """Clean up tracking data for a completed operation
        
        Args:
            operation_id: Unique identifier for the operation
        """
        if operation_id in self._active_operations:
            del self._active_operations[operation_id]
    
    @contextmanager
    def track_ingestion(self, operation_id: str):
        """Context manager for tracking ingestion latency
        
        Args:
            operation_id: Unique identifier for the operation
            
        Yields:
            Start timestamp
            
        Example:
            with latency_service.track_ingestion("dataset_123") as start_time:
                # perform ingestion
                pass
        """
        start_time = self.start_ingestion(operation_id)
        try:
            yield start_time
        finally:
            self.complete_ingestion(operation_id)
    
    @contextmanager
    def track_validation(self, operation_id: str):
        """Context manager for tracking validation latency
        
        Args:
            operation_id: Unique identifier for the operation
            
        Yields:
            Start timestamp
            
        Example:
            with latency_service.track_validation("dataset_123") as start_time:
                # perform validation
                pass
        """
        start_time = self.start_validation(operation_id)
        try:
            yield start_time
        finally:
            self.complete_validation(operation_id)
