from src.publisher.wp_dotcom_client import WordPressDotComClient
from src.common.config import settings


def main():
    print("DEBUG: WP_DOTCOM_SITE =", settings.WP_DOTCOM_SITE)
    print("DEBUG: WP_DOTCOM_API_BASE =", settings.WP_DOTCOM_API_BASE)

    client = WordPressDotComClient()
    try:
        data = client.ping()
        print("Connected to WP.com site:", data.get("name"), "-", data.get("URL"))
    except Exception as e:
        print("ERROR while calling WordPress.com API:", e)


if __name__ == "__main__":
    main()
