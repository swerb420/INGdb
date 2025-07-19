import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://localhost/trading_intelligence",
)
PROJECT_DIR = os.getenv(
    "TRADING_INTEL_DIR",
    os.path.dirname(os.path.abspath(__file__)),
)
API_KEYS = {
    "ALPHA_VANTAGE": os.getenv("ALPHA_VANTAGE_API_KEY", ""),
    "FRED": os.getenv("FRED_API_KEY", ""),
    "REDDIT_CLIENT_ID": os.getenv("REDDIT_CLIENT_ID", ""),
    "REDDIT_CLIENT_SECRET": os.getenv("REDDIT_CLIENT_SECRET", ""),
    "DUNE": os.getenv("DUNE_API_KEY", ""),
}


def validate_env() -> None:
    """Ensure all critical environment variables are present.

    Raises
    ------
    RuntimeError
        If any required variable is missing, with instructions on how to
        provide it.
    """

    required = {
        "DATABASE_URL": DATABASE_URL,
        "ALPHA_VANTAGE_API_KEY": API_KEYS["ALPHA_VANTAGE"],
        "FRED_API_KEY": API_KEYS["FRED"],
        "REDDIT_CLIENT_ID": API_KEYS["REDDIT_CLIENT_ID"],
        "REDDIT_CLIENT_SECRET": API_KEYS["REDDIT_CLIENT_SECRET"],
    }

    missing = [k for k, v in required.items() if not v]
    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(
            f"Missing required environment variables: {joined}. "
            "Set them in your environment or in a '.env' file."
        )


# Optional log file path for logging.basicConfig
LOG_FILE = os.getenv("LOG_FILE", "")
