"""Dataset Profiling Service

Provides functionality for profiling datasets and generating basic statistics
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import time
from sqlalchemy.orm import Session
from sqlalchemy import desc
import pandas as pd
import numpy as np

from app.models.profiling_result import ProfilingResult


class DatasetProfilingService:
    """Service for profiling datasets and storing profiling results"""
    
    def __init__(self, db: Session):
        """
        Initialize the dataset profiling service.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def profile_dataset(
        self,
        df: pd.DataFrame,
        dataset_name: str,
        profiled_by: str = 'system'
    ) -> ProfilingResult:
        """
        Profile a dataset and generate statistics.
        
        Args:
            df: Pandas DataFrame to profile
            dataset_name: Name of the dataset
            profiled_by: User or system initiating profiling
            
        Returns:
            ProfilingResult instance with profiling statistics
        """
        start_time = time.time()
        
        try:
            # Calculate basic metrics
            row_count = len(df)
            column_count = len(df.columns)
            
            # Calculate per-column statistics
            column_statistics = self._calculate_column_statistics(df)
            
            # Calculate column distributions
            column_distributions = self._calculate_column_distributions(df)
            
            # Calculate execution time
            execution_time_ms = (time.time() - start_time) * 1000
            
            # Create profiling result
            profiling_result = ProfilingResult(
                dataset_name=dataset_name,
                status='completed',
                row_count=row_count,
                column_count=column_count,
                execution_time_ms=execution_time_ms,
                column_statistics=column_statistics,
                column_distributions=column_distributions,
                profiled_by=profiled_by
            )
            
            # Save to database
            self.db.add(profiling_result)
            self.db.commit()
            self.db.refresh(profiling_result)
            
            return profiling_result
            
        except Exception as e:
            # Create failed profiling result
            execution_time_ms = (time.time() - start_time) * 1000
            
            profiling_result = ProfilingResult(
                dataset_name=dataset_name,
                status='failed',
                execution_time_ms=execution_time_ms,
                error_message=str(e),
                profiled_by=profiled_by
            )
            
            self.db.add(profiling_result)
            self.db.commit()
            self.db.refresh(profiling_result)
            
            raise
    
    def _calculate_column_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate basic statistics for each column.
        
        Args:
            df: Pandas DataFrame
            
        Returns:
            Dictionary with column statistics
        """
        statistics = {}
        
        for column in df.columns:
            col_stats = {
                'column_name': column,
                'data_type': str(df[column].dtype),
                'null_count': int(df[column].isnull().sum()),
                'null_percentage': float((df[column].isnull().sum() / len(df)) * 100) if len(df) > 0 else 0.0,
            }
            
            # Add numeric statistics for numeric columns
            if pd.api.types.is_numeric_dtype(df[column]):
                # Filter out NaN values for calculations
                non_null_values = df[column].dropna()
                
                if len(non_null_values) > 0:
                    col_stats['min'] = float(non_null_values.min())
                    col_stats['max'] = float(non_null_values.max())
                    col_stats['mean'] = float(non_null_values.mean())
                    col_stats['median'] = float(non_null_values.median())
                    col_stats['std'] = float(non_null_values.std()) if len(non_null_values) > 1 else 0.0
                else:
                    col_stats['min'] = None
                    col_stats['max'] = None
                    col_stats['mean'] = None
                    col_stats['median'] = None
                    col_stats['std'] = None
            
            statistics[column] = col_stats
        
        return statistics
    
    def _calculate_column_distributions(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate value distributions for each column.
        
        Args:
            df: Pandas DataFrame
            
        Returns:
            Dictionary with column value distributions
        """
        distributions = {}
        
        for column in df.columns:
            # Calculate value counts (top 10 most frequent values)
            value_counts = df[column].value_counts().head(10)
            
            # Convert to list of dictionaries
            distribution_list = [
                {
                    'value': str(value),
                    'count': int(count),
                    'percentage': float((count / len(df)) * 100) if len(df) > 0 else 0.0
                }
                for value, count in value_counts.items()
            ]
            
            distributions[column] = {
                'column_name': column,
                'unique_count': int(df[column].nunique()),
                'top_values': distribution_list
            }
        
        return distributions
    
    def get_latest_profiling(self, dataset_name: str) -> Optional[ProfilingResult]:
        """
        Get the latest profiling result for a dataset.
        
        Args:
            dataset_name: Name of the dataset
            
        Returns:
            Latest ProfilingResult or None
        """
        return (
            self.db.query(ProfilingResult)
            .filter(ProfilingResult.dataset_name == dataset_name)
            .order_by(desc(ProfilingResult.created_at))
            .first()
        )
    
    def get_profiling_history(
        self,
        dataset_name: Optional[str] = None,
        limit: int = 100
    ) -> List[ProfilingResult]:
        """
        Get profiling history, optionally filtered by dataset.
        
        Args:
            dataset_name: Optional dataset name filter
            limit: Maximum number of results
            
        Returns:
            List of ProfilingResult instances
        """
        query = self.db.query(ProfilingResult)
        
        if dataset_name:
            query = query.filter(ProfilingResult.dataset_name == dataset_name)
        
        return (
            query
            .order_by(desc(ProfilingResult.created_at))
            .limit(limit)
            .all()
        )
    
    def get_profiling_by_id(self, profiling_id: int) -> Optional[ProfilingResult]:
        """
        Get a specific profiling result by ID.
        
        Args:
            profiling_id: Profiling result ID
            
        Returns:
            ProfilingResult or None
        """
        return self.db.query(ProfilingResult).filter(ProfilingResult.id == profiling_id).first()


def get_profiling_service(db: Session = None) -> DatasetProfilingService:
    """
    Factory function to get profiling service instance.
    
    Args:
        db: Optional database session
        
    Returns:
        DatasetProfilingService instance
    """
    if db is None:
        from app.core.database import SessionLocal
        db = SessionLocal()
    
    return DatasetProfilingService(db)
