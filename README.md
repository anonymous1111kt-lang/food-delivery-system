# QuickBite — Online Food Delivery Management System (Python + MySQL + Web Frontend)

A full-stack, internship-ready **Online Food Delivery Management System** built with a **Python (Flask)** backend, responsive **Bootstrap 5** frontend, and a high-performance relational **MySQL** database.

---

## 🌟 Key Features

1. **Restaurant & Cuisine Catalog**:
   - Browse gourmet restaurants with high-resolution food imagery, live ratings, and estimated delivery windows.
   - Filter by cuisine categories (`Pizza & Italian`, `Burgers`, `Indian & Curries`, `Sushi & Asian`, `Mexican`, `Healthy Bowls`, `Desserts`).
   - Dynamic search by restaurant name, cuisine type, and dish name.
   - Trending & Popular Dishes showcase with 1-click ordering.

2. **Interactive Restaurant Menu & Cart Flow**:
   - Menu navigation with category tabs and dietary badges (`Veg`, `Non-Veg`, `Vegan`).
   - Spicy indicators and Chef Bestseller badges.
   - Smart session cart with restaurant validation, quantity adjustments (+/-), and minimum order checks.
   - Verified customer review section with star ratings.

3. **Doorstep Checkout & Settlement**:
   - Custom delivery address, landmark notes, and phone number.
   - Dynamic fee calculator: items subtotal + delivery partner fee + 8% taxes.
   - Multi-modality settlements: `UPI / Instant QR`, `Credit / Debit Card`, `Net Banking`, and `Cash on Delivery (COD)`.

4. **Live Visual Order Tracking**:
   - 5-stage real-time visual progress stepper:
     `Placed` ➔ `Confirmed` ➔ `Cooking / Preparing` ➔ `Out for Delivery` ➔ `Delivered`
   - Real-time courier partner assignment card (rider name, contact phone, safety check).
   - Self-service cancellation for orders still in `Placed` or `Confirmed` status.

5. **Customer Hub (`My Orders`)**:
   - View order history with itemized summaries and delivery timestamps.
   - Leave post-delivery reviews and star ratings to update restaurant metrics.

6. **Restaurant Kitchen Partner Portal (`/restaurant/dashboard`)**:
   - Kitchen KPI dashboard: Active Orders, Total Orders, Gross Revenue, Menu item count.
   - Live Order Queue with one-click status transitions: `Accept & Confirm`, `Start Cooking`, `Dispatch Rider`.
   - Full menu inventory CRUD: Add Dish, Edit Dish, Delete Dish, and instant In-Stock / Out-of-Stock toggles.
   - Kitchen store status toggle (`Open for Orders` vs `Kitchen Closed`).

7. **Courier Rider Dispatch Portal (`/delivery/dashboard`)**:
   - Rider KPI summary: Active runs, Completed deliveries, Total earnings ($5 per drop).
   - Available orders pool: Claim and accept unassigned orders ready for delivery.
   - Real-time status updates: `Mark Picked Up` ➔ `Mark Delivered`.

8. **Admin Operations Portal (`/admin/dashboard`)**:
   - Platform-wide telemetry: Gross Volume, Total Orders, Partner Kitchens, Registered Users.
   - Master Orders Audit Log with multilateral joins and status badges.
   - Restaurant management with on-demand activation / deactivation.
   - Direct user registry with role breakdowns.

9. **Self-Healing Diagnostics & Setup (`/db-status`)**:
   - Live MySQL server connection monitor and database table breakdown.
   - In-browser credential manager (updates `.env` on the fly).
   - One-click sample data seeder.
   - CLI diagnostic scripts (`test_connection.py` and `setup_db.py`).

---

## 📂 Project Structure

```
food_delivery_system/
├── app.py                      # Main Flask application and API route controllers
├── config.py                   # Configuration loader from .env
├── database.py                 # PyMySQL connection manager, migration checks
├── seed_data.py                # Rich sample users, restaurants, menu dishes, orders, reviews
├── setup_db.py                 # CLI database initializer & seeder script
├── test_connection.py          # CLI MySQL diagnostic tool
├── schema.sql                  # MySQL 8 relational schema DDL
├── requirements.txt            # Python dependencies (Flask, PyMySQL, Werkzeug, etc.)
├── run.sh                      # Executable launch script
├── .env                        # Local database credentials & port settings
├── .env.example                # Example configuration template
├── static/
│   ├── css/
│   │   └── style.css           # Modern food delivery UI styling & stepper animations
│   └── js/
│       └── cart.js             # Cart interactivity and tooltips
└── templates/
    ├── base.html               # Master layout with navigation, cart badge & footer
    ├── index.html              # Customer home catalog, cuisine filters & search
    ├── restaurant_detail.html  # Restaurant menu page, dietary tabs & reviews
    ├── cart.html               # Shopping cart summary & quantity adjustments
    ├── checkout.html           # Address entry & payment method selection
    ├── order_success.html      # Order confirmation receipt
    ├── order_tracker.html      # 5-stage live visual stepper tracking page
    ├── my_orders.html          # Customer order history & review modal
    ├── login.html              # Sign in with 1-click demo login pills
    ├── register.html           # Account registration with role selector
    ├── restaurant_dashboard.html # Partner portal: live orders & menu CRUD
    ├── menu_item_form.html     # Add / Edit food dish form
    ├── delivery_dashboard.html # Rider portal: claim orders & complete deliveries
    ├── admin_dashboard.html    # Admin management, metrics & master order audit
    └── db_status.html          # Self-healing database connection & diagnostic panel
```

---

## 🗄️ Database Architecture (MySQL)

- **`users`**:
  - `user_id` INT AUTO_INCREMENT PRIMARY KEY
  - `first_name`, `last_name`, `email` (UNIQUE), `password_hash`, `phone`, `address`
  - `role` ENUM('customer', 'restaurant_owner', 'delivery_agent', 'admin')

- **`categories`**:
  - `category_id` INT AUTO_INCREMENT PRIMARY KEY
  - `name` (UNIQUE), `icon`, `display_order`

- **`restaurants`**:
  - `restaurant_id` INT AUTO_INCREMENT PRIMARY KEY
  - `owner_id` (FK -> users.user_id)
  - `name`, `cuisine_type`, `description`, `phone`, `address`, `city`
  - `rating`, `delivery_time_mins`, `delivery_fee`, `minimum_order`, `image_url`, `banner_url`, `is_active`

- **`menu_items`**:
  - `item_id` INT AUTO_INCREMENT PRIMARY KEY
  - `restaurant_id` (FK -> restaurants.restaurant_id)
  - `category_id` (FK -> categories.category_id)
  - `name`, `description`, `price`, `dietary_type` ('veg', 'non-veg', 'vegan')
  - `is_spicy`, `is_popular`, `status` ('available', 'out_of_stock'), `image_url`

- **`orders`**:
  - `order_id` INT AUTO_INCREMENT PRIMARY KEY
  - `customer_id` (FK -> users.user_id)
  - `restaurant_id` (FK -> restaurants.restaurant_id)
  - `delivery_agent_id` (FK -> users.user_id)
  - `delivery_address`, `customer_phone`, `special_instructions`
  - `subtotal`, `delivery_fee`, `tax_amount`, `total_amount`
  - `payment_method` ('credit_card', 'upi', 'cash_on_delivery', 'net_banking')
  - `payment_status` ('pending', 'completed', 'failed', 'refunded')
  - `order_status` ('placed', 'confirmed', 'preparing', 'out_for_delivery', 'delivered', 'cancelled')
  - `estimated_delivery_time`, `created_at`, `updated_at`

- **`order_items`**:
  - `order_item_id` INT AUTO_INCREMENT PRIMARY KEY
  - `order_id` (FK -> orders.order_id)
  - `item_id` (FK -> menu_items.item_id)
  - `item_name`, `unit_price`, `quantity`, `subtotal`

- **`reviews`**:
  - `review_id` INT AUTO_INCREMENT PRIMARY KEY
  - `order_id` (UNIQUE, FK -> orders.order_id)
  - `customer_id` (FK -> users.user_id)
  - `restaurant_id` (FK -> restaurants.restaurant_id)
  - `rating` INT (1 to 5), `comment`

---

## 🔑 Demo Login Accounts

| Role | Email | Password | Pre-configured Access |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@quickbite.com` | `admin123` | Full admin portal, revenue metrics, master audit |
| **Restaurant Partner** | `luigi@quickbite.com` | `owner123` | Bella Napoli Pizzeria kitchen & menu CRUD |
| **Restaurant Partner** | `priya@quickbite.com` | `owner123` | Spice Symphony kitchen & menu CRUD |
| **Courier Rider** | `david.rider@quickbite.com` | `rider123` | Courier runs, order claim & delivery completion |
| **Customer** | `john.doe@example.com` | `customer123` | Browsing, ordering, live tracking, order history |

*(Tip: You can click the 1-click demo buttons on the `/login` page to instantly auto-fill credentials!)*

---

## 🚀 Quick Start Guide

### 1. Database Initialization

Run the automated setup CLI tool:
```bash
python setup_db.py
```
*(This creates `food_delivery_db`, initializes all tables, and seeds realistic restaurants, menus, courier riders, and orders).*

### 2. Run Database Diagnostic Test

```bash
python test_connection.py
```

### 3. Launch Web Application

```bash
./run.sh
```
or:
```bash
python app.py
```

Open your browser and navigate to:
👉 **`http://localhost:5001`**
*(Configured to port 5001 to run simultaneously alongside the vehicle rental system on 5000).*
