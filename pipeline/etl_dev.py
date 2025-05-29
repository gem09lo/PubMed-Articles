"""Development script for running the ETL pipeline without AWS (local filesystem only)."""
from transform import main_transform

if __name__ == "__main__":
    main_transform()
