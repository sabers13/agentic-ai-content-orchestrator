# Loading environment variables needs to respect the project root, not the package directory.
from dotenv import load_dotenv, find_dotenv
import os

dotenv_path = find_dotenv(usecwd=True)
if dotenv_path:
    load_dotenv(dotenv_path=dotenv_path)
else:
    load_dotenv()

class Settings:
    # WordPress.com
    WP_DOTCOM_SITE: str = os.getenv("WP_DOTCOM_SITE", "")
    WP_DOTCOM_API_BASE: str = os.getenv("WP_DOTCOM_API_BASE", "")
    WP_DOTCOM_BEARER: str = os.getenv("WP_DOTCOM_BEARER", "")  # <— Added this line

    # Optional legacy / unused (can stay blank)
    WP_BASE_URL: str = os.getenv("WP_BASE_URL", "")
    WP_USERNAME: str = os.getenv("WP_USERNAME", "")
    WP_APP_PASSWORD_OR_JWT: str = os.getenv("WP_APP_PASSWORD_OR_JWT", "")

    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Model & thresholds
    MODEL_PRIMARY: str = os.getenv("MODEL_PRIMARY", "gpt-5o")
    MODEL_SECONDARY: str = os.getenv("MODEL_SECONDARY", "gpt-5o-mini")
    SEO_THRESHOLD: int = int(os.getenv("SEO_THRESHOLD", "75"))
    QUALITY_THRESHOLD: int = int(os.getenv("QUALITY_THRESHOLD", "70"))

    # Prefect
    PREFECT_API_URL: str = os.getenv("PREFECT_API_URL", "")
    PREFECT_API_KEY: str = os.getenv("PREFECT_API_KEY", "")

settings = Settings()
