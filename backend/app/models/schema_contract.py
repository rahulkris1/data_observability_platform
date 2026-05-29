"""Schema Contract ORM Model

Defines expected dataset structure for validation
"""
from sqlalchemy import Column, String, Text, Boolean, JSON
from app.models.base import BaseModel


class SchemaContract(BaseModel):
    """Schema Contract model for defining expected dataset structure
    
    Attributes:
        name: Unique contract name (e.g., 'customer_schema', 'orders_schema')
        description: Human-readable description of the contract
        dataset_name: Name of the dataset this contract applies to
        version: Contract version (e.g., '1.0.0')
        is_active: Whether this contract is currently active
        schema_definition: JSON structure defining expected schema
            Format: {
                "columns": [
                    {
                        "name": "column_name",
                        "data_type": "string|integer|float|boolean|date|timestamp",
                        "required": true|false,
                        "nullable": true|false
                    },
                    ...
                ]
            }
    """
    __tablename__ = "schema_contracts"
    
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    dataset_name = Column(String(255), nullable=False, index=True)
    version = Column(String(50), nullable=False, default="1.0.0")
    is_active = Column(Boolean, nullable=False, default=True)
    schema_definition = Column(JSON, nullable=False)
    
    def __repr__(self) -> str:
        """String representation of the schema contract"""
        return f"<SchemaContract(name={self.name}, dataset={self.dataset_name}, version={self.version})>"
