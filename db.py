import sqlite3


class DBHandler:
    def __init__(self, db_path):
        self.db_path = db_path

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def create_tables(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    productId TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    price TEXT NOT NULL,
                    launchDate INTEGER NOT NULL,
                    sku TEXT NOT NULL,
                    status TEXT NOT NULL,
                    releaseMethod TEXT NOT NULL,
                    cartLimit TEXT NOT NULL,
                    exclusiveAccess BOOLEAN NOT NULL,
                    imageURL TEXT NOT NULL,
                    discordMessageId TEXT NULL,
                    recordInsertStamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    recordUpdateStamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP 
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS skus (
                    skuId TEXT PRIMARY KEY,
                    productId TEXT NOT NULL,
                    size TEXT NOT NULL,
                    stock TEXT NOT NULL,
                    recordInsertStamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    recordUpdateStamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (productId) REFERENCES products(productId) ON DELETE CASCADE
                );
            """)

    def init(self):
        self.create_tables()

    def upsert_products(self, products):
        sql_query = """
            INSERT INTO products (productId, title, url, price, launchDate, sku, status, releaseMethod, cartLimit, exclusiveAccess, imageURL)
            VALUES (:productId, :title, :url, :price, :launchDate, :sku, :status, :releaseMethod, :cartLimit, :exclusiveAccess, :imageURL)
            ON CONFLICT(productId) DO UPDATE SET
                title = excluded.title,
                url = excluded.url,
                price = excluded.price,
                launchDate = excluded.launchDate,
                sku = excluded.sku,
                status = excluded.status,
                releaseMethod = excluded.releaseMethod,
                cartLimit = excluded.cartLimit,
                exclusiveAccess = excluded.exclusiveAccess,
                imageURL = excluded.imageURL,
                recordUpdateStamp = CURRENT_TIMESTAMP
            WHERE products.title IS NOT excluded.title
                OR products.url IS NOT excluded.url
                OR products.price IS NOT excluded.price
                OR products.launchDate IS NOT excluded.launchDate
                OR products.sku IS NOT excluded.sku
                OR products.status IS NOT excluded.status
                OR products.releaseMethod IS NOT excluded.releaseMethod
                OR products.cartLimit IS NOT excluded.cartLimit
                OR products.exclusiveAccess IS NOT excluded.exclusiveAccess
                OR products.imageURL IS NOT excluded.imageURL;
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(sql_query, products)
            return conn.total_changes

    def upsert_skus(self, skus):
        sql_query = """
            INSERT INTO skus (skuId, productId, size, stock)
            VALUES (:skuId, :productId, :size, :stock)
            ON CONFLICT(skuId) DO UPDATE SET
                productId = excluded.productId,
                size = excluded.size,
                stock = excluded.stock,
                recordUpdateStamp = CURRENT_TIMESTAMP
            WHERE skus.productId IS NOT excluded.productId
                OR skus.size IS NOT excluded.size
                OR skus.stock IS NOT excluded.stock;
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(sql_query, skus)
            return conn.total_changes

    def get_updated_records(self, table_name, min_record_update_stamp):
        sql_query = f"""
            SELECT * FROM {table_name}
            WHERE recordUpdateStamp >= ?;
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                sql_query,
                (min_record_update_stamp,),
            )
            return cursor.fetchall()

    def get_discord_message_id(self, product_id):
        sql_query = f"""
            SELECT * FROM products
            WHERE productId = ?;
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                sql_query,
                (product_id,),
            )
            return cursor.fetchone()

    def update_discord_message_id(self, product_id, discord_message_id):
        sql_query = f"""
            UPDATE products
            SET
                discordMessageId = ?,
                recordUpdateStamp = CURRENT_TIMESTAMP
            WHERE productId = ?;
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                sql_query,
                (discord_message_id, product_id),
            )
            return cursor.rowcount
