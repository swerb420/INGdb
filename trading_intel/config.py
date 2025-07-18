import os
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/trading_intelligence")
PROJECT_DIR = os.getenv("TRADING_INTEL_DIR", os.path.dirname(os.path.abspath(__file__)))
API_KEYS = {
    "ALPHA_VANTAGE": os.getenv("ALPHA_VANTAGE_API_KEY", ""),
    "FRED": os.getenv("FRED_API_KEY", ""),
    "REDDIT_CLIENT_ID": os.getenv("REDDIT_CLIENT_ID", ""),
    "REDDIT_CLIENT_SECRET": os.getenv("REDDIT_CLIENT_SECRET", ""),
}
