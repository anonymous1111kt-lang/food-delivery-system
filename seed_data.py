import datetime
from werkzeug.security import generate_password_hash
from database import get_db_connection
import logging

logger = logging.getLogger(__name__)

def seed_sample_data():
    """Seeds rich sample data into the database if tables are empty."""
    try:
        conn = get_db_connection(use_db=True)
        with conn.cursor() as cursor:
            # 1. Seed Users
            cursor.execute("SELECT COUNT(*) AS count FROM users;")
            user_count = cursor.fetchone()['count']

            if user_count == 0:
                logger.info("Seeding initial users...")
                users = [
                    (
                        "Admin", "Director", "admin@quickbite.com",
                        generate_password_hash("admin123"), "555-0100",
                        "HQ 100 Main Street, Suite 400", "admin"
                    ),
                    (
                        "Luigi", "Rossi", "luigi@quickbite.com",
                        generate_password_hash("owner123"), "555-0101",
                        "42 Little Italy Ave, Downtown", "restaurant_owner"
                    ),
                    (
                        "Priya", "Sharma", "priya@quickbite.com",
                        generate_password_hash("owner123"), "555-0102",
                        "88 Spice Boulevard, Midtown", "restaurant_owner"
                    ),
                    (
                        "Kenji", "Sato", "kenji@quickbite.com",
                        generate_password_hash("owner123"), "555-0103",
                        "12 Cherry Blossom Lane, Uptown", "restaurant_owner"
                    ),
                    (
                        "David", "Miller", "david.rider@quickbite.com",
                        generate_password_hash("rider123"), "555-0150",
                        "Zone 1 Dispatch Hub", "delivery_agent"
                    ),
                    (
                        "Sarah", "Jenkins", "sarah.rider@quickbite.com",
                        generate_password_hash("rider123"), "555-0151",
                        "Zone 2 Dispatch Hub", "delivery_agent"
                    ),
                    (
                        "John", "Doe", "john.doe@example.com",
                        generate_password_hash("customer123"), "555-0199",
                        "742 Evergreen Terrace, Apt 4B, Downtown", "customer"
                    ),
                    (
                        "Emily", "Clark", "emily.clark@example.com",
                        generate_password_hash("customer123"), "555-0188",
                        "1204 Elm Street, Flat 2A, Midtown", "customer"
                    )
                ]
                cursor.executemany("""
                    INSERT INTO users (first_name, last_name, email, password_hash, phone, address, role)
                    VALUES (%s, %s, %s, %s, %s, %s, %s);
                """, users)

            # Get user IDs for relationships
            cursor.execute("SELECT user_id, email FROM users;")
            user_map = {row['email']: row['user_id'] for row in cursor.fetchall()}

            # 2. Seed Categories
            cursor.execute("SELECT COUNT(*) AS count FROM categories;")
            cat_count = cursor.fetchone()['count']

            if cat_count == 0:
                logger.info("Seeding categories...")
                categories = [
                    ("Pizza & Italian", "bi-pie-chart-fill", 1),
                    ("Burgers & Fast Food", "bi-box-seam", 2),
                    ("Indian & Curries", "bi-fire", 3),
                    ("Sushi & Asian", "bi-tropical-storm", 4),
                    ("Mexican & Tacos", "bi-sun-fill", 5),
                    ("Healthy Bowls & Salads", "bi-heart-pulse-fill", 6),
                    ("Desserts & Shakes", "bi-cake2-fill", 7)
                ]
                cursor.executemany("""
                    INSERT INTO categories (name, icon, display_order)
                    VALUES (%s, %s, %s);
                """, categories)

            cursor.execute("SELECT category_id, name FROM categories;")
            cat_map = {row['name']: row['category_id'] for row in cursor.fetchall()}

            # 3. Seed Restaurants
            cursor.execute("SELECT COUNT(*) AS count FROM restaurants;")
            rest_count = cursor.fetchone()['count']

            if rest_count == 0:
                logger.info("Seeding restaurants...")
                restaurants = [
                    (
                        user_map.get("luigi@quickbite.com"),
                        "Bella Napoli Pizzeria",
                        "Italian & Pizza",
                        "Authentic wood-fired Neapolitan pizzas, handmade pastas, and classic Italian antipasti crafted using imported Italian flour and San Marzano tomatoes.",
                        "555-2001",
                        "42 Little Italy Ave",
                        "Downtown",
                        4.8,
                        25,
                        2.49,
                        15.00,
                        "https://images.unsplash.com/photo-1513104890138-7c749659a591?auto=format&fit=crop&w=800&q=80",
                        "https://images.unsplash.com/photo-1579684947550-22e945225d9a?auto=format&fit=crop&w=1200&q=80",
                        True
                    ),
                    (
                        user_map.get("priya@quickbite.com"),
                        "Spice Symphony Royal Kitchen",
                        "Indian & Mughlai",
                        "Rich aromatic biryanis, slow-cooked buttery gravies, tandoori kebabs, and warm garlic naans bursting with royal Indian spices.",
                        "555-2002",
                        "88 Spice Boulevard",
                        "Midtown",
                        4.9,
                        30,
                        1.99,
                        12.00,
                        "https://images.unsplash.com/photo-1585937421612-70a008356fbe?auto=format&fit=crop&w=800&q=80",
                        "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=1200&q=80",
                        True
                    ),
                    (
                        user_map.get("kenji@quickbite.com"),
                        "Tokyo Ramen & Sushi Bar",
                        "Japanese & Sushi",
                        "Master-crafted tonkotsu ramen broth simmered for 18 hours, fresh salmon and tuna sashimi, and artisanal dragon rolls.",
                        "555-2003",
                        "12 Cherry Blossom Lane",
                        "Uptown",
                        4.7,
                        25,
                        2.99,
                        18.00,
                        "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?auto=format&fit=crop&w=800&q=80",
                        "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=1200&q=80",
                        True
                    ),
                    (
                        user_map.get("admin@quickbite.com"),
                        "The Prime Burger Co.",
                        "Burgers & Grills",
                        "Gourmet smashed Angus beef patties, caramelized onions, melted cheddar cheese, and crispy golden truffle parmesan fries.",
                        "555-2004",
                        "105 West Street",
                        "Downtown",
                        4.6,
                        20,
                        1.49,
                        10.00,
                        "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=800&q=80",
                        "https://images.unsplash.com/photo-1550547660-d9450f859349?auto=format&fit=crop&w=1200&q=80",
                        True
                    ),
                    (
                        user_map.get("admin@quickbite.com"),
                        "Cantina Viva Mexican Grill",
                        "Mexican Street Food",
                        "Sizzling fajitas, birria tacos with rich dipping consommé, guacamole made table-side, and crispy loaded nachos.",
                        "555-2005",
                        "77 Fiesta Way",
                        "Midtown",
                        4.7,
                        25,
                        1.99,
                        12.00,
                        "https://images.unsplash.com/photo-1565299585323-38d6b0865b47?auto=format&fit=crop&w=800&q=80",
                        "https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=1200&q=80",
                        True
                    ),
                    (
                        user_map.get("admin@quickbite.com"),
                        "Green Garden Clean Bowls",
                        "Healthy & Vegan",
                        "Wholesome vibrant quinoa bowls, avocado goddess toasts, organic cold-pressed juices, and fresh Mediterranean protein salads.",
                        "555-2006",
                        "33 Wellness Avenue",
                        "Uptown",
                        4.8,
                        18,
                        0.99,
                        10.00,
                        "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=800&q=80",
                        "https://images.unsplash.com/photo-1540420773420-3366772f4999?auto=format&fit=crop&w=1200&q=80",
                        True
                    )
                ]
                cursor.executemany("""
                    INSERT INTO restaurants (
                        owner_id, name, cuisine_type, description, phone, address, city,
                        rating, delivery_time_mins, delivery_fee, minimum_order, image_url, banner_url, is_active
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                """, restaurants)

            # Get restaurant map
            cursor.execute("SELECT restaurant_id, name FROM restaurants;")
            rest_map = {row['name']: row['restaurant_id'] for row in cursor.fetchall()}

            # 4. Seed Menu Items
            cursor.execute("SELECT COUNT(*) AS count FROM menu_items;")
            menu_count = cursor.fetchone()['count']

            if menu_count == 0:
                logger.info("Seeding menu items...")
                pizzas_cat = cat_map.get("Pizza & Italian", 1)
                burgers_cat = cat_map.get("Burgers & Fast Food", 2)
                indian_cat = cat_map.get("Indian & Curries", 3)
                asian_cat = cat_map.get("Sushi & Asian", 4)
                mexican_cat = cat_map.get("Mexican & Tacos", 5)
                healthy_cat = cat_map.get("Healthy Bowls & Salads", 6)
                desserts_cat = cat_map.get("Desserts & Shakes", 7)

                pizzeria_id = rest_map.get("Bella Napoli Pizzeria")
                spice_id = rest_map.get("Spice Symphony Royal Kitchen")
                tokyo_id = rest_map.get("Tokyo Ramen & Sushi Bar")
                burger_id = rest_map.get("The Prime Burger Co.")
                cantina_id = rest_map.get("Cantina Viva Mexican Grill")
                green_id = rest_map.get("Green Garden Clean Bowls")

                menu_items = [
                    # Bella Napoli Pizzeria
                    (
                        pizzeria_id, pizzas_cat, "Margherita D.O.P.",
                        "San Marzano tomato sauce, fresh buffalo mozzarella, fresh basil, extra virgin olive oil.",
                        14.99, "veg", False, True, "available",
                        "https://images.unsplash.com/photo-1604382354936-07c5d9983bd3?auto=format&fit=crop&w=600&q=80"
                    ),
                    (
                        pizzeria_id, pizzas_cat, "Spicy Diavola Pepperoni",
                        "Spicy Calabrian salami, crushed chili flakes, mozzarella, homemade tomato sauce.",
                        17.49, "non-veg", True, True, "available",
                        "https://images.unsplash.com/photo-1628840042765-356cda07504e?auto=format&fit=crop&w=600&q=80"
                    ),
                    (
                        pizzeria_id, pizzas_cat, "Truffle Mushroom Fettuccine",
                        "Handmade fettuccine pasta, wild forest mushrooms, black truffle cream, aged parmesan.",
                        18.99, "veg", False, True, "available",
                        "https://images.unsplash.com/photo-1645112411341-6c4fd023714a?auto=format&fit=crop&w=600&q=80"
                    ),
                    (
                        pizzeria_id, desserts_cat, "Classic Venetian Tiramisu",
                        "Espresso-soaked ladyfingers layered with creamy mascarpone custard and dusted with dark cocoa.",
                        8.50, "veg", False, True, "available",
                        "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?auto=format&fit=crop&w=600&q=80"
                    ),

                    # Spice Symphony
                    (
                        spice_id, indian_cat, "Dum Handi Chicken Biryani",
                        "Long grain basmati rice slow cooked in a sealed clay pot with marinated tender chicken and saffron.",
                        16.99, "non-veg", True, True, "available",
                        "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?auto=format&fit=crop&w=600&q=80"
                    ),
                    (
                        spice_id, indian_cat, "Paneer Butter Masala",
                        "Fresh cottage cheese cubes simmered in a luscious tomato, butter, and cashew nut gravy.",
                        14.49, "veg", False, True, "available",
                        "https://images.unsplash.com/photo-1631452180519-c014fe946bc7?auto=format&fit=crop&w=600&q=80"
                    ),
                    (
                        spice_id, indian_cat, "Garlic Butter Naan (2 pcs)",
                        "Traditional clay oven baked flatbread brushed with crushed roasted garlic and melted butter.",
                        4.99, "veg", False, False, "available",
                        "https://images.unsplash.com/photo-1626074353765-517a681e40be?auto=format&fit=crop&w=600&q=80"
                    ),
                    (
                        spice_id, indian_cat, "Dal Makhani Grand Reserve",
                        "Black lentils slow cooked overnight with rich butter and fresh cream on a charcoal hearth.",
                        12.99, "veg", False, True, "available",
                        "https://images.unsplash.com/photo-1546833999-b9f581a1996d?auto=format&fit=crop&w=600&q=80"
                    ),

                    # Tokyo Ramen & Sushi Bar
                    (
                        tokyo_id, asian_cat, "Rich Tonkotsu Black Garlic Ramen",
                        "Pork bone broth, tender chashu pork belly, bamboo shoots, soft-boiled ajitsuke tamago, nori.",
                        16.50, "non-veg", False, True, "available",
                        "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=600&q=80"
                    ),
                    (
                        tokyo_id, asian_cat, "Spicy Dragon Roll (8 pcs)",
                        "Tempura prawn, avocado, cucumber, topped with spicy tuna, eel sauce, and tobiko.",
                        15.99, "non-veg", True, True, "available",
                        "https://images.unsplash.com/photo-1617196034796-73dfa7b1fd56?auto=format&fit=crop&w=600&q=80"
                    ),
                    (
                        tokyo_id, asian_cat, "Crispy Gyoza Dumplings (6 pcs)",
                        "Pan-seared Japanese dumplings stuffed with minced pork and scallions, served with spicy ponzu dip.",
                        8.99, "non-veg", False, False, "available",
                        "https://images.unsplash.com/photo-1496116218417-1a781b1c416c?auto=format&fit=crop&w=600&q=80"
                    ),

                    # The Prime Burger Co.
                    (
                        burger_id, burgers_cat, "The Prime Double Smash Burger",
                        "Two smashed Angus beef patties, double American cheese, caramelized onions, house secret sauce on brioche.",
                        13.99, "non-veg", False, True, "available",
                        "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=600&q=80"
                    ),
                    (
                        burger_id, burgers_cat, "Crispy Nashville Hot Chicken Burger",
                        "Spicy fried chicken breast dipped in cayenne oil, dill pickles, vinegar slaw on toasted potato bun.",
                        12.99, "non-veg", True, True, "available",
                        "https://images.unsplash.com/photo-1625813506062-0aeb1d7a094b?auto=format&fit=crop&w=600&q=80"
                    ),
                    (
                        burger_id, burgers_cat, "Truffle Parmesan Fries",
                        "Crisp russet potato fries tossed in aromatic white truffle oil, grated pecorino, and fresh parsley.",
                        6.99, "veg", False, True, "available",
                        "https://images.unsplash.com/photo-1576107232684-1279f3908594?auto=format&fit=crop&w=600&q=80"
                    ),

                    # Cantina Viva Mexican Grill
                    (
                        cantina_id, mexican_cat, "Birria Quesatacos Trio",
                        "Three crispy corn tortillas dipped in chili broth, melted Oaxaca cheese, slow-braised beef, with hot consommé dip.",
                        15.49, "non-veg", True, True, "available",
                        "https://images.unsplash.com/photo-1565299585323-38d6b0865b47?auto=format&fit=crop&w=600&q=80"
                    ),
                    (
                        cantina_id, mexican_cat, "Loaded Guacamole & House Tortilla Chips",
                        "Hass avocados mashed with lime juice, cilantro, jalapeños, red onions, and warm salted chips.",
                        9.49, "vegan", False, False, "available",
                        "https://images.unsplash.com/photo-1541544741938-0af808871cc0?auto=format&fit=crop&w=600&q=80"
                    ),

                    # Green Garden Clean Bowls
                    (
                        green_id, healthy_cat, "Rainbow Avocado & Quinoa Bowl",
                        "Tricolor quinoa, Hass avocado, edamame, roasted chickpeas, purple cabbage, tahini lemon dressing.",
                        13.49, "vegan", False, True, "available",
                        "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=600&q=80"
                    ),
                    (
                        green_id, healthy_cat, "Mediterranean Falafel Harvest Salad",
                        "Crispy herb falafels, kalamata olives, cherry tomatoes, cucumbers, hummus, warm pita points.",
                        12.99, "vegan", False, False, "available",
                        "https://images.unsplash.com/photo-1540420773420-3366772f4999?auto=format&fit=crop&w=600&q=80"
                    )
                ]

                # Filter out any items where restaurant_id is None
                valid_items = [item for item in menu_items if item[0] is not None]
                cursor.executemany("""
                    INSERT INTO menu_items (
                        restaurant_id, category_id, name, description, price, dietary_type,
                        is_spicy, is_popular, status, image_url
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                """, valid_items)

            # 5. Seed Orders and Order Items
            cursor.execute("SELECT COUNT(*) AS count FROM orders;")
            order_count = cursor.fetchone()['count']

            if order_count == 0:
                logger.info("Seeding orders and items...")
                customer_john = user_map.get("john.doe@example.com")
                customer_emily = user_map.get("emily.clark@example.com")
                rider_david = user_map.get("david.rider@quickbite.com")
                rider_sarah = user_map.get("sarah.rider@quickbite.com")
                pizzeria_id = rest_map.get("Bella Napoli Pizzeria")
                spice_id = rest_map.get("Spice Symphony Royal Kitchen")
                burger_id = rest_map.get("The Prime Burger Co.")

                now = datetime.datetime.now()

                # Order 1: Delivered
                cursor.execute("""
                    INSERT INTO orders (
                        customer_id, restaurant_id, delivery_agent_id, delivery_address, customer_phone,
                        special_instructions, subtotal, delivery_fee, tax_amount, total_amount,
                        payment_method, payment_status, order_status, estimated_delivery_time, created_at
                    ) VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s
                    );
                """, (
                    customer_john, pizzeria_id, rider_david,
                    "742 Evergreen Terrace, Apt 4B, Downtown", "555-0199",
                    "Ring buzzer #4B, leave outside door.",
                    32.48, 2.49, 2.60, 37.57,
                    "credit_card", "completed", "delivered",
                    now - datetime.timedelta(hours=2), now - datetime.timedelta(hours=2, minutes=45)
                ))
                order1_id = cursor.lastrowid

                # Items for Order 1
                cursor.execute("""
                    INSERT INTO order_items (order_id, item_id, item_name, unit_price, quantity, subtotal)
                    VALUES 
                    (%s, NULL, 'Margherita D.O.P.', 14.99, 1, 14.99),
                    (%s, NULL, 'Spicy Diavola Pepperoni', 17.49, 1, 17.49);
                """, (order1_id, order1_id))

                # Review for Order 1
                cursor.execute("""
                    INSERT INTO reviews (order_id, customer_id, restaurant_id, rating, comment)
                    VALUES (%s, %s, %s, %s, %s);
                """, (order1_id, customer_john, pizzeria_id, 5, "Pizza was piping hot with incredible blistered crust! Best in town."))

                # Order 2: Out for delivery
                cursor.execute("""
                    INSERT INTO orders (
                        customer_id, restaurant_id, delivery_agent_id, delivery_address, customer_phone,
                        special_instructions, subtotal, delivery_fee, tax_amount, total_amount,
                        payment_method, payment_status, order_status, estimated_delivery_time, created_at
                    ) VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s
                    );
                """, (
                    customer_emily, spice_id, rider_sarah,
                    "1204 Elm Street, Flat 2A, Midtown", "555-0188",
                    "Please provide extra green mint chutney.",
                    31.48, 1.99, 2.52, 35.99,
                    "upi", "completed", "out_for_delivery",
                    now + datetime.timedelta(minutes=15), now - datetime.timedelta(minutes=25)
                ))
                order2_id = cursor.lastrowid

                cursor.execute("""
                    INSERT INTO order_items (order_id, item_id, item_name, unit_price, quantity, subtotal)
                    VALUES 
                    (%s, NULL, 'Dum Handi Chicken Biryani', 16.99, 1, 16.99),
                    (%s, NULL, 'Paneer Butter Masala', 14.49, 1, 14.49);
                """, (order2_id, order2_id))

                # Order 3: Preparing
                cursor.execute("""
                    INSERT INTO orders (
                        customer_id, restaurant_id, delivery_agent_id, delivery_address, customer_phone,
                        special_instructions, subtotal, delivery_fee, tax_amount, total_amount,
                        payment_method, payment_status, order_status, estimated_delivery_time, created_at
                    ) VALUES (
                        %s, %s, NULL, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s
                    );
                """, (
                    customer_john, burger_id,
                    "742 Evergreen Terrace, Apt 4B, Downtown", "555-0199",
                    "Extra napkins please.",
                    20.98, 1.49, 1.68, 24.15,
                    "cash_on_delivery", "pending", "preparing",
                    now + datetime.timedelta(minutes=30), now - datetime.timedelta(minutes=10)
                ))
                order3_id = cursor.lastrowid

                cursor.execute("""
                    INSERT INTO order_items (order_id, item_id, item_name, unit_price, quantity, subtotal)
                    VALUES 
                    (%s, NULL, 'The Prime Double Smash Burger', 13.99, 1, 13.99),
                    (%s, NULL, 'Truffle Parmesan Fries', 6.99, 1, 6.99);
                """, (order3_id, order3_id))

        conn.commit()
        conn.close()
        logger.info("Sample food delivery data seeded successfully.")
        return True
    except Exception as e:
        logger.error(f"Seeding error: {e}")
        return False
