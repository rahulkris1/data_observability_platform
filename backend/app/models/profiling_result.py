"""Profiling Result ORM Model

Stores dataset profiling execution results and statistics
"""
from sqlalchemy import Column, String, Integer, Text, JSON, Float
from app.models.base import BaseModel


class ProfilingResult(BaseModel):
    """Profiling Result model for storing dataset profiling statistics
    
    Attributes:
        dataset_name: Name of the profiled dataset
        status: Profiling execution status ('completed', 'failed', 'running')
        row_count: Total number of rows in the dataset
        column_count: Total number of columns in the dataset
        execution_time_ms: Execution time in milliseconds
        column_statistics: JSON structure with per-column statistics (min, max, mean, null_count)
        column_distributions: JSON structure with column value distributions
        error_message: Error message if profiling failed
        profiled_by: User or system that initiated profiling
    """
    __tablename__ = "profiling_results"
    
    dataset_name = Column(String(255), nullable=False, index=True)
    status = Column(String(50), nullable=False, index=True)
    
    row_count = Column(Integer, nullable=True)
    column_count = Column(Integer, nullable=True)
    execution_time_ms = Column(Float, nullable=True)
    
    column_statistics = Column(JSON, nullable=True)
    column_distributions = Column(JSON, nullable=True)
    
    error_message = Column(Text, nullable=True)
    profiled_by = Column(String(255), nullable=False, default='system')
    
    def __repr__(self) -> str:
        """String representation of the profiling result"""
        return (
            f"<ProfilingResult(dataset={self.dataset_name}, "
            f"status={self.status}, rows={self.row_count}, "
            f"columns={self.column_count}, "
            f"profiled_at={self.created_at})>"
        )
