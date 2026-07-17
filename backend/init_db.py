"""Initialize database with all tables"""
import sys
sys.path.append('.')

from app.core.database import engine, Base
from app.models import *  # Import all models including User

# Create all tables
print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("✅ Database tables created successfully!")

# List all created tables
from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()
print(f"\nCreated {len(tables)} tables:")
for table in sorted(tables):
    print(f"  - {table}")
