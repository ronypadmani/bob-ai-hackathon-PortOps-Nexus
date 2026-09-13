import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Port Operations Copilot"
    APP_ENV: str = "development"
    PORT_NAME: str = "San Pedro Bay Terminal Complex"
    PLANNING_HORIZON_HOURS: int = 72
    
    # Path settings
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    SAMPLE_DATA_DIR: Path = Path(__file__).resolve().parent / "data" / "sample_data"
    
    # watsonx / IBM Bob configuration
    WATSONX_API_KEY: str = os.getenv("WATSONX_API_KEY", "")
    WATSONX_PROJECT_ID: str = os.getenv("WATSONX_PROJECT_ID", "")
    WATSONX_URL: str = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
    WATSONX_MODEL_ID: str = os.getenv("WATSONX_MODEL_ID", "ibm/granite-3-8b-instruct")
    
    # Optimization parameters
    ORTOOLS_SOLVER_TIME_LIMIT_SECONDS: int = 30
    DEFAULT_CRANE_PRODUCTIVITY_MOVES_PER_HOUR: float = 28.0  # standard container moves per crane hour
    MAX_CRANES_PER_VESSEL: int = 5
    MIN_CRANES_PER_VESSEL: int = 2
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
