import requests
from datetime import datetime
from zoneinfo import ZoneInfo


class SNKRSMonitor:
    def __init__(
        self,
        country_code,
        language,
        channel_id,
        upcoming,
        exclusive_access,
    ):
        self.feed_url = "https://api.nike.com/product_feed/threads/v3"
        self.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
        }
        self.feed_params = {
            "filter": [
                f"marketplace({country_code})",
                f"language({language})",
                f"channelId({channel_id})",
                f"upcoming({upcoming})",
                f"exclusiveAccess({exclusive_access})",
            ]
        }

    def get_sku_info(self, sku, available_gtins):
        result = {}

        result["size"] = sku["nikeSize"]

        result["stock"] = "OOS"
        sku_gtin = sku["gtin"]
        for gtin in available_gtins:
            if gtin["gtin"] == sku_gtin:
                result["stock"] = gtin["level"]
                break
        return result

    def parse_product(self, product):
        result = {}

        result["productId"] = product["id"]

        result["titleName"] = product["publishedContent"]["nodes"][0]["properties"][
            "subtitle"
        ]
        result["titleVariant"] = product["publishedContent"]["nodes"][0]["properties"][
            "title"
        ]
        result["title"] = (
            f"{result['titleName']} - {result['titleVariant']}"
            if result["titleVariant"]
            else result["titleName"]
        )

        result["slug"] = product["publishedContent"]["properties"]["seo"]["slug"]
        result["url"] = f"https://www.nike.com/launch/t/{result['slug']}"

        result["priceValue"] = product["productInfo"][0]["merchPrice"]["currentPrice"]
        result["priceCurrency"] = product["productInfo"][0]["merchPrice"]["currency"]
        result["price"] = (
            f"${result['priceValue']} {result['priceCurrency']}"
            if result["priceCurrency"]
            else result["priceValue"]
        )

        result["launchDate"] = int(
            datetime.fromisoformat(
                product["productInfo"][0]["launchView"]["startEntryDate"].replace(
                    "Z", "+00:00"
                )
            ).timestamp()
        )

        result["sku"] = product["productInfo"][0]["merchProduct"]["styleColor"]

        result["status"] = product["productInfo"][0]["merchProduct"]["status"]

        result["releaseMethod"] = product["productInfo"][0]["launchView"]["method"]

        result["cartLimit"] = product["productInfo"][0]["merchProduct"]["quantityLimit"]

        result["exclusiveAccess"] = product["productInfo"][0]["merchProduct"][
            "exclusiveAccess"
        ]

        result["imageURL"] = product["publishedContent"]["nodes"][0]["nodes"][0][
            "properties"
        ]["squarishURL"]

        stock_levels = {
            gtin["gtin"]: gtin["level"]
            for gtin in product["productInfo"][0].get("availableGtins", [])
        }

        result["skus"] = [
            {
                "skuId": sku["gtin"],
                "size": sku["nikeSize"],
                "stock": stock_levels.get(sku["gtin"], "OOS"),
                "productId": product["id"],
            }
            for sku in product["productInfo"][0]["skus"]
        ]

        return result

    def get_products(self):
        response = requests.get(
            self.feed_url, headers=self.headers, params=self.feed_params
        )
        return [self.parse_product(product) for product in response.json()["objects"]]
