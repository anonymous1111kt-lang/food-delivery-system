import pymysql
from pymysql.cursors import DictCursor
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection(use_db=True):
    """
    Establish a connection to the MySQL server.
    If use_db=True, connects to Config.DB_NAME.
    Otherwise, connects to the server without selecting a specific database.
    """
    return pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME if use_db else None,
        cursorclass=DictCursor,
        autocommit=False,
        charset='utf8mb4'
    )

def test_connection():
    """
    Tests connectivity to the MySQL database.
    Returns (True, message) or (False, error_message).
    """
    try:
        conn = get_db_connection(use_db=False)
        with conn.cursor() as cursor:
            cursor.execute("SELECT VERSION() AS version;")
            row = cursor.fetchone()
            version = row['version'] if row else "Unknown"
        conn.close()
        return True, f"Connected to MySQL {version} successfully."
    except Exception as e:
        return False, str(e)

def init_db():
    """
    Initializes the database and all required tables.
    """
    try:
        # Step 1: Connect to MySQL server and ensure database exists
        conn = get_db_connection(use_db=False)
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{Config.DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        conn.commit()
        conn.close()

        # Step 2: Connect to the specific database and create tables
        conn = get_db_connection(use_db=True)
        with conn.cursor() as cursor:
            # Users
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INT AUTO_INCREMENT PRIMARY KEY,
                    first_name VARCHAR(50) NOT NULL,
                    last_name VARCHAR(50) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    phone VARCHAR(20) NOT NULL,
                    address TEXT,
                    role ENUM('customer', 'restaurant_owner', 'delivery_agent', 'admin') DEFAULT 'customer',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # Categories
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    category_id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(50) UNIQUE NOT NULL,
                    icon VARCHAR(50) DEFAULT 'bi-egg-fried',
                    display_order INT DEFAULT 0
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # Restaurants
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS restaurants (
                    restaurant_id INT AUTO_INCREMENT PRIMARY KEY,
                    owner_id INT NULL,
                    name VARCHAR(100) NOT NULL,
                    cuisine_type VARCHAR(50) NOT NULL,
                    description TEXT,
                    phone VARCHAR(20) NOT NULL,
                    address VARCHAR(255) NOT NULL,
                    city VARCHAR(50) DEFAULT 'Downtown',
                    rating DECIMAL(2,1) DEFAULT 4.5,
                    delivery_time_mins INT DEFAULT 30,
                    delivery_fee DECIMAL(6,2) DEFAULT 2.99,
                    minimum_order DECIMAL(6,2) DEFAULT 10.00,
                    image_url VARCHAR(500) DEFAULT '',
                    banner_url VARCHAR(500) DEFAULT '',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (owner_id) REFERENCES users(user_id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # Menu Items
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS menu_items (
                    item_id INT AUTO_INCREMENT PRIMARY KEY,
                    restaurant_id INT NOT NULL,
                    category_id INT NULL,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    price DECIMAL(10,2) NOT NULL,
                    dietary_type ENUM('veg', 'non-veg', 'vegan') DEFAULT 'veg',
                    is_spicy BOOLEAN DEFAULT FALSE,
                    is_popular BOOLEAN DEFAULT FALSE,
                    status ENUM('available', 'out_of_stock') DEFAULT 'available',
                    image_url VARCHAR(500) DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (restaurant_id) REFERENCES restaurants(restaurant_id) ON DELETE CASCADE,
                    FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # Orders
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    order_id INT AUTO_INCREMENT PRIMARY KEY,
                    customer_id INT NOT NULL,
                    restaurant_id INT NOT NULL,
                    delivery_agent_id INT NULL,
                    delivery_address TEXT NOT NULL,
                    customer_phone VARCHAR(20) NOT NULL,
                    special_instructions TEXT,
                    subtotal DECIMAL(10,2) NOT NULL DEFAULT 0.00,
                    delivery_fee DECIMAL(10,2) NOT NULL DEFAULT 0.00,
                    tax_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
                    total_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
                    payment_method ENUM('credit_card', 'upi', 'cash_on_delivery', 'net_banking') NOT NULL,
                    payment_status ENUM('pending', 'completed', 'failed', 'refunded') DEFAULT 'pending',
                    order_status ENUM('placed', 'confirmed', 'preparing', 'out_for_delivery', 'delivered', 'cancelled') DEFAULT 'placed',
                    estimated_delivery_time DATETIME NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY (restaurant_id) REFERENCES restaurants(restaurant_id) ON DELETE CASCADE,
                    FOREIGN KEY (delivery_agent_id) REFERENCES users(user_id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # Order Items
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS order_items (
                    order_item_id INT AUTO_INCREMENT PRIMARY KEY,
                    order_id INT NOT NULL,
                    item_id INT NULL,
                    item_name VARCHAR(100) NOT NULL,
                    unit_price DECIMAL(10,2) NOT NULL,
                    quantity INT NOT NULL DEFAULT 1,
                    subtotal DECIMAL(10,2) NOT NULL,
                    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
                    FOREIGN KEY (item_id) REFERENCES menu_items(item_id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # Reviews
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reviews (
                    review_id INT AUTO_INCREMENT PRIMARY KEY,
                    order_id INT UNIQUE NOT NULL,
                    customer_id INT NOT NULL,
                    restaurant_id INT NOT NULL,
                    rating INT NOT NULL DEFAULT 5,
                    comment TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
                    FOREIGN KEY (customer_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY (restaurant_id) REFERENCES restaurants(restaurant_id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # Schema compatibility check helpers
            _ensure_column_exists(cursor, 'restaurants', 'banner_url', "VARCHAR(500) DEFAULT ''")
            _ensure_column_exists(cursor, 'menu_items', 'is_spicy', "BOOLEAN DEFAULT FALSE")
            _ensure_column_exists(cursor, 'menu_items', 'is_popular', "BOOLEAN DEFAULT FALSE")

        conn.commit()
        conn.close()
        logger.info("Food delivery database initialized successfully.")
        return True, "Database and tables verified successfully."
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        return False, str(e)

def _ensure_column_exists(cursor, table_name, column_name, column_definition):
    """Adds a column if it does not already exist."""
    try:
        cursor.execute(f"""
            SELECT COUNT(*) AS cnt 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = '{Config.DB_NAME}' 
              AND TABLE_NAME = '{table_name}' 
              AND COLUMN_NAME = '{column_name}';
        """)
        res = cursor.fetchone()
        if res and res['cnt'] == 0:
            cursor.execute(f"ALTER TABLE `{table_name}` ADD COLUMN `{column_name}` {column_definition};")
            logger.info(f"Added column {column_name} to {table_name}")
    except Exception as e:
        logger.warning(f"Could not verify/add column {column_name} on {table_name}: {e}")
