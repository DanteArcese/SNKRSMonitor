import discord
from datetime import datetime


class DiscordHandler:
    def __init__(self, discord_webhook_url):
        self.discord_webhook_url = discord_webhook_url
        self.webhook = discord.SyncWebhook.from_url(discord_webhook_url)

    def format_bool(self, bool):
        return ":green_circle:" if bool else ":red_circle:"

    def format_stock(self, stock):
        return ":green_circle:" if stock == "HIGH" else (":yellow_circle:" if stock == "MEDIUM" else ":red_circle:")

    def format_status(self, status):
        return ":green_circle:" if status == "ACTIVE" else (":yellow_circle:" if status == "HOLD" else ":red_circle:")

    def format_product(self, product):
        embed = discord.Embed(
            title=product["title"],
            url=product["url"],
            colour=0xFE081F,
            timestamp=datetime.now(),
        )

        embed.set_author(
            name="SNKRS Monitor",
            icon_url="https://play-lh.googleusercontent.com/kWXy8EJ9rL4iH2lDxiDv0LYd6DeTPHLbzGXDHwZLvRy5UBhYHezTDm51onReoWZdzjPX",
        )

        embed.add_field(name="Price", value=product["price"], inline=True)
        embed.add_field(name="Release Date", value=f"<t:{product["launchDate"]}:f>", inline=True)
        embed.add_field(name="SKU", value=product["sku"], inline=True)
        embed.add_field(name="Status", value=f"{product["status"]} {self.format_status(product["status"])}", inline=True)
        embed.add_field(
            name="Release Method", value=product["releaseMethod"], inline=True
        )
        embed.add_field(name="Cart Limit", value=product["cartLimit"], inline=True)
        embed.add_field(
            name="Exclusive Access", value=f"{"Yes" if product["exclusiveAccess"] else "No"} {self.format_bool(product["exclusiveAccess"])}", inline=True
        )
        embed.add_field(
            name="Useful Links",
            value=f"[StockX](https://stockx.com/search?s={product["sku"]}) | [GOAT](https://www.goat.com/search?query={product["sku"]}) | [eBay](https://www.ebay.com/sch/i.html?_nkw={product["sku"]})",
            inline=True,
        )
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(
            name="Stock Levels",
            value="\n".join(
                [f"{sku["size"]} | {sku["stock"]} {self.format_stock(sku["stock"])}" for sku in product["skus"][::2]]
            ),
            inline=True,
        )
        embed.add_field(
            name="Stock Levels",
            value="\n".join(
                [f"{sku["size"]} | {sku["stock"]} {self.format_stock(sku["stock"])}" for sku in product["skus"][1::2]]
            ),
            inline=True,
        )

        embed.set_image(url=product["imageURL"])

        embed.set_footer(text="SNKRS Monitor")

        return embed

    def send_webhook(self, product, discord_message_id=None):
        if discord_message_id:
            self.webhook.edit_message(
                discord_message_id, embeds=[self.format_product(product)]
            )
            return discord_message_id
        else:
            return self.webhook.send(
                embeds=[self.format_product(product)], wait=True
            ).id
