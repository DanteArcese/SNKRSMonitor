import os
import logging
import sys
from datetime import datetime, timezone
from time import sleep
from dotenv import load_dotenv
from snkrs import SNKRSMonitor
from db import DBHandler
from discord_handler import DiscordHandler

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter(
    "{asctime} - [{levelname}] - {name} - {message}", style="{"
)

console = logging.StreamHandler(sys.stdout)
console.setLevel(logging.INFO)
console.setFormatter(formatter)

file_handler = logging.FileHandler("app.log", encoding="utf-8")
file_handler.setLevel(logging.WARNING)
file_handler.setFormatter(formatter)

logger.addHandler(console)
logger.addHandler(file_handler)


def main():
    logger.debug("Gathering SNKRS monitor configuration...")
    country_code = os.getenv("COUNTRY_CODE")
    language = os.getenv("LANGUAGE")
    channel_id = os.getenv("CHANNEL_ID")
    upcoming = os.getenv("UPCOMING")
    exclusive_access = os.getenv("EXCLUSIVE_ACCESS")
    discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    polling_interval_seconds = int(os.getenv("POLLING_INTERVAL_SECONDS"))
    db_path = os.getenv("DB_PATH")

    db = DBHandler(db_path)
    db.init()

    dc = DiscordHandler(discord_webhook_url)

    logger.info(f"""Starting SNKRS Monitor with the following configuration:
                
                Country Code: {country_code}
                Language: {language}
                Channel ID: {channel_id}
                Upcoming: {upcoming}
                Exclusive Access: {exclusive_access}
                Discord webhook set: {"Yes" if discord_webhook_url else "No"}

                Press Ctrl+C to exit.""")
    monitor = SNKRSMonitor(
        country_code,
        language,
        channel_id,
        upcoming,
        exclusive_access,
    )
    try:
        while True:
            loop_start = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            products = monitor.get_products()
            logger.info(f"Fetched {len(products)} product{"s" if len(products) != 1 else ""}.")
            products_updated = db.upsert_products(products)
            if products_updated:
                logger.info(f"{products_updated} product{"s" if products_updated != 1 else ""} upserted.")
            total_skus_updated = 0 
            for product in products:
                skus_updated = db.upsert_skus(product["skus"])
                if skus_updated:
                    logger.info(f"{product["title"]} - {skus_updated} SKU{"s" if skus_updated != 1 else ""} upserted.")
                    total_skus_updated += skus_updated
            updated_product_ids = []
            if products_updated:
                updated_product_ids.extend([product['productId'] for product in db.get_updated_records('products', loop_start)])
            if skus_updated:
                updated_product_ids.extend(list(set([sku['productId'] for sku in db.get_updated_records('skus', loop_start) if sku['productId'] not in updated_product_ids])))
            for product in products:
                if product['productId'] in updated_product_ids:
                    discord_message_id = db.get_discord_message_id(product['productId'])["discordMessageId"]
                    new_discord_message_id = dc.send_webhook(product, discord_message_id)
                    if new_discord_message_id:
                        logger.info(f"Sent message for {product['title']}.")
                    else:
                        logger.error(f"Unable to {"edit" if discord_message_id else "send"} message for {product['title']}.")
                    if not discord_message_id:
                        update_count = db.update_discord_message_id(product['productId'], new_discord_message_id)
                        if update_count:
                            logger.info(f"Discord message ID stored in DB for {product["title"]}.")
                        else:
                            logger.error(f"Unable to store Discord message ID in DB for {product["title"]}.")
            logger.debug(
                f"Sleeping for {polling_interval_seconds} seconds before next run."
            )
            sleep(polling_interval_seconds)
            logger.debug(
                f"Finished sleeping for {polling_interval_seconds} seconds. Kicking off next run."
            )

    except KeyboardInterrupt:
        logger.info("Shutdown signal received. Cleaning up...")
    except Exception as e:
        logger.exception("", exc_info=e)
    finally:
        logger.info("Service safely stopped.")
        sys.exit(0)


if __name__ == "__main__":
    main()
