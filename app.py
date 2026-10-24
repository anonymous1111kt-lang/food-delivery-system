import os
import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql

from config import Config
from database import get_db_connection, test_connection, init_db
from seed_data import seed_sample_data

app = Flask(__name__)
app.config.from_object(Config)

# Make config and cart info available in all Jinja templates
@app.context_processor
def inject_global_context():
    cart = session.get('cart', {})
    cart_items = cart.get('items', {})
    cart_count = sum(cart_items.values())
    return {
        'config': Config,
        'cart_count': cart_count
    }

# -------------------------------------------------------------
# Auth Decorators
# -------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please sign in to proceed.", "info")
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please sign in with administrator credentials.", "warning")
            return redirect(url_for('login', next=request.url))
        if session.get('role') != 'admin':
            flash("Restricted area. Administrator privileges required.", "danger")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def restaurant_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please sign in as a restaurant partner.", "warning")
            return redirect(url_for('login', next=request.url))
        if session.get('role') not in ['restaurant_owner', 'admin']:
            flash("Access restricted to restaurant kitchen partners.", "danger")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def rider_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please sign in as a delivery courier partner.", "warning")
            return redirect(url_for('login', next=request.url))
        if session.get('role') not in ['delivery_agent', 'admin']:
            flash("Access restricted to registered delivery agents.", "danger")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


# -------------------------------------------------------------
# Customer & Public Catalog Routes
# -------------------------------------------------------------
@app.route('/')
def index():
    search_query = request.args.get('q', '').strip()
    selected_category = request.args.get('category', '').strip()

    restaurants = []
    categories = []
    popular_items = []

    try:
        conn = get_db_connection(use_db=True)
        with conn.cursor() as cursor:
            # 1. Fetch Categories
            cursor.execute("SELECT * FROM categories ORDER BY display_order ASC, name ASC;")
            categories = cursor.fetchall()

            # 2. Build Restaurant Query
            query = "SELECT * FROM restaurants WHERE 1=1"
            params = []

            if selected_category:
                # Match either restaurant cuisine or restaurants having menu items in that category
                query += """ AND (
                    cuisine_type LIKE %s 
                    OR restaurant_id IN (
                        SELECT m.restaurant_id FROM menu_items m 
                        JOIN categories c ON m.category_id = c.category_id 
                        WHERE c.name = %s
                    )
                )"""
                params.extend([f"%{selected_category}%", selected_category])

            if search_query:
                query += """ AND (
                    name LIKE %s 
                    OR cuisine_type LIKE %s 
                    OR description LIKE %s
                    OR restaurant_id IN (
                        SELECT restaurant_id FROM menu_items WHERE name LIKE %s OR description LIKE %s
                    )
                )"""
                term = f"%{search_query}%"
                params.extend([term, term, term, term, term])

            query += " ORDER BY rating DESC, restaurant_id DESC;"
            cursor.execute(query, params)
            restaurants = cursor.fetchall()

            # 3. Fetch Trending / Popular Dishes
            cursor.execute("""
                SELECT m.*, r.name AS restaurant_name, c.name AS category_name
                FROM menu_items m
                JOIN restaurants r ON m.restaurant_id = r.restaurant_id
                LEFT JOIN categories c ON m.category_id = c.category_id
                WHERE m.is_popular = TRUE AND m.status = 'available' AND r.is_active = TRUE
                ORDER BY m.item_id ASC
                LIMIT 6;
            """)
            popular_items = cursor.fetchall()

        conn.close()
    except Exception as e:
        flash(f"Database error: {e}. Configure database connection below if needed.", "warning")
        return redirect(url_for('db_status'))

    return render_template(
        'index.html',
        restaurants=restaurants,
        categories=categories,
        popular_items=popular_items,
        search_query=search_query,
        selected_category=selected_category
    )

@app.route('/restaurant/<int:restaurant_id>')
def restaurant_detail(restaurant_id):
    selected_cat_id = request.args.get('category', type=int)
    diet_filter = request.args.get('diet', 'all').strip().lower()

    try:
        conn = get_db_connection(use_db=True)
        with conn.cursor() as cursor:
            # 1. Fetch Restaurant details
            cursor.execute("SELECT * FROM restaurants WHERE restaurant_id = %s;", (restaurant_id,))
            restaurant = cursor.fetchone()
            if not restaurant:
                conn.close()
                flash("Restaurant not found.", "danger")
                return redirect(url_for('index'))

            # 2. Categories for this restaurant
            cursor.execute("""
                SELECT DISTINCT c.category_id, c.name, c.icon, c.display_order
                FROM categories c
                JOIN menu_items m ON c.category_id = m.category_id
                WHERE m.restaurant_id = %s
                ORDER BY c.display_order ASC;
            """, (restaurant_id,))
            categories = cursor.fetchall()

            # 3. Menu items
            query = "SELECT * FROM menu_items WHERE restaurant_id = %s"
            params = [restaurant_id]

            if selected_cat_id:
                query += " AND category_id = %s"
                params.append(selected_cat_id)

            if diet_filter in ['veg', 'non-veg', 'vegan']:
                query += " AND dietary_type = %s"
                params.append(diet_filter)

            query += " ORDER BY is_popular DESC, item_id ASC;"
            cursor.execute(query, params)
            menu_items = cursor.fetchall()

            # 4. Reviews
            cursor.execute("""
                SELECT r.*, u.first_name, u.last_name
                FROM reviews r
                JOIN users u ON r.customer_id = u.user_id
                WHERE r.restaurant_id = %s
                ORDER BY r.review_id DESC
                LIMIT 10;
            """, (restaurant_id,))
            reviews = cursor.fetchall()

        conn.close()
    except Exception as e:
        flash(f"Error loading menu: {e}", "danger")
        return redirect(url_for('index'))

    return render_template(
        'restaurant_detail.html',
        restaurant=restaurant,
        categories=categories,
        menu_items=menu_items,
        reviews=reviews,
        selected_cat_id=selected_cat_id,
        diet_filter=diet_filter
    )


# -------------------------------------------------------------
# Cart Operations
# -------------------------------------------------------------
@app.route('/cart')
def view_cart():
    cart = session.get('cart', {})
    cart_items_dict = cart.get('items', {})
    restaurant_id = cart.get('restaurant_id')

    cart_items = []
    restaurant = None
    subtotal = 0.0
    delivery_fee = 0.0
    tax = 0.0
    total = 0.0

    if cart_items_dict and restaurant_id:
        try:
            conn = get_db_connection(use_db=True)
            with conn.cursor() as cursor:
                # Fetch restaurant
                cursor.execute("SELECT * FROM restaurants WHERE restaurant_id = %s;", (restaurant_id,))
                restaurant = cursor.fetchone()

                # Fetch items
                item_ids = list(map(int, cart_items_dict.keys()))
                format_strings = ','.join(['%s'] * len(item_ids))
                cursor.execute(f"SELECT * FROM menu_items WHERE item_id IN ({format_strings});", tuple(item_ids))
                db_items = cursor.fetchall()

                for it in db_items:
                    qty = cart_items_dict.get(str(it['item_id']), 0)
                    if qty > 0:
                        line_total = float(it['price']) * qty
                        subtotal += line_total
                        cart_items.append({
                            'item_id': it['item_id'],
                            'name': it['name'],
                            'price': float(it['price']),
                            'quantity': qty,
                            'subtotal': line_total,
                            'image_url': it['image_url'],
                            'dietary_type': it['dietary_type']
                        })
            conn.close()

            if restaurant:
                delivery_fee = float(restaurant['delivery_fee'])
            tax = round(subtotal * 0.08, 2)
            total = round(subtotal + delivery_fee + tax, 2)
        except Exception as e:
            flash(f"Error loading cart items: {e}", "danger")

    return render_template(
        'cart.html',
        cart_items=cart_items,
        restaurant=restaurant,
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        tax=tax,
        total=total
    )

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    item_id = request.form.get('item_id')
    restaurant_id = request.form.get('restaurant_id')
    quantity = int(request.form.get('quantity', 1))

    if not item_id or not restaurant_id:
        flash("Invalid item.", "danger")
        return redirect(request.referrer or url_for('index'))

    cart = session.get('cart', {'restaurant_id': None, 'items': {}})

    # If items in cart from another restaurant, reset cart to new restaurant
    if cart.get('restaurant_id') and str(cart['restaurant_id']) != str(restaurant_id):
        cart = {'restaurant_id': int(restaurant_id), 'items': {}}
        flash("Starting a new order from this restaurant (previous cart cleared).", "info")

    cart['restaurant_id'] = int(restaurant_id)
    current_qty = cart['items'].get(str(item_id), 0)
    cart['items'][str(item_id)] = current_qty + quantity

    session['cart'] = cart
    session.modified = True
    flash("Item added to cart!", "success")
    return redirect(request.referrer or url_for('view_cart'))

@app.route('/cart/update', methods=['POST'])
def update_cart():
    item_id = str(request.form.get('item_id'))
    action = request.form.get('action')

    cart = session.get('cart', {'restaurant_id': None, 'items': {}})
    if 'items' in cart and item_id in cart['items']:
        if action == 'increase':
            cart['items'][item_id] += 1
        elif action == 'decrease':
            cart['items'][item_id] -= 1
            if cart['items'][item_id] <= 0:
                del cart['items'][item_id]

        if not cart['items']:
            cart['restaurant_id'] = None

        session['cart'] = cart
        session.modified = True

    return redirect(url_for('view_cart'))

@app.route('/cart/remove/<int:item_id>', methods=['POST'])
def remove_from_cart(item_id):
    cart = session.get('cart', {'restaurant_id': None, 'items': {}})
    str_id = str(item_id)
    if 'items' in cart and str_id in cart['items']:
        del cart['items'][str_id]
        if not cart['items']:
            cart['restaurant_id'] = None
        session['cart'] = cart
        session.modified = True
        flash("Item removed from cart.", "info")
    return redirect(url_for('view_cart'))

@app.route('/cart/clear', methods=['POST'])
def clear_cart():
    session['cart'] = {'restaurant_id': None, 'items': {}}
    session.modified = True
    flash("Cart cleared.", "info")
    return redirect(url_for('view_cart'))


# -------------------------------------------------------------
# Checkout & Order Placement
# -------------------------------------------------------------
@app.route('/checkout', methods=['GET'])
@login_required
def checkout():
    cart = session.get('cart', {})
    cart_items_dict = cart.get('items', {})
    restaurant_id = cart.get('restaurant_id')

    if not cart_items_dict or not restaurant_id:
        flash("Your cart is empty.", "warning")
        return redirect(url_for('index'))

    user = None
    restaurant = None
    cart_items = []
    subtotal = 0.0

    try:
        conn = get_db_connection(use_db=True)
        with conn.cursor() as cursor:
            # User profile
            cursor.execute("SELECT * FROM users WHERE user_id = %s;", (session['user_id'],))
            user = cursor.fetchone()

            # Restaurant
            cursor.execute("SELECT * FROM restaurants WHERE restaurant_id = %s;", (restaurant_id,))
            restaurant = cursor.fetchone()

            # Items
            item_ids = list(map(int, cart_items_dict.keys()))
            format_strings = ','.join(['%s'] * len(item_ids))
            cursor.execute(f"SELECT * FROM menu_items WHERE item_id IN ({format_strings});", tuple(item_ids))
            db_items = cursor.fetchall()

            for it in db_items:
                qty = cart_items_dict.get(str(it['item_id']), 0)
                if qty > 0:
                    line_total = float(it['price']) * qty
                    subtotal += line_total
                    cart_items.append({
                        'item_id': it['item_id'],
                        'name': it['name'],
                        'unit_price': float(it['price']),
                        'quantity': qty,
                        'subtotal': line_total
                    })
        conn.close()
    except Exception as e:
        flash(f"Error loading checkout: {e}", "danger")
        return redirect(url_for('view_cart'))

    if not restaurant:
        flash("Selected restaurant is no longer available.", "danger")
        return redirect(url_for('view_cart'))

    if subtotal < float(restaurant['minimum_order']):
        flash(f"Minimum order for {restaurant['name']} is ${restaurant['minimum_order']:.2f}.", "warning")
        return redirect(url_for('view_cart'))

    delivery_fee = float(restaurant['delivery_fee'])
    tax = round(subtotal * 0.08, 2)
    total = round(subtotal + delivery_fee + tax, 2)

    return render_template(
        'checkout.html',
        user=user,
        restaurant=restaurant,
        cart_items=cart_items,
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        tax=tax,
        total=total
    )

@app.route('/order/place', methods=['POST'])
@login_required
def place_order():
    cart = session.get('cart', {})
    cart_items_dict = cart.get('items', {})
    restaurant_id = cart.get('restaurant_id')

    if not cart_items_dict or not restaurant_id:
        flash("Your cart is empty.", "warning")
        return redirect(url_for('index'))

    delivery_address = request.form.get('delivery_address', '').strip()
    customer_phone = request.form.get('customer_phone', '').strip()
    special_instructions = request.form.get('special_instructions', '').strip()
    payment_method = request.form.get('payment_method', 'upi')

    if not delivery_address or not customer_phone:
        flash("Please provide a complete delivery address and phone number.", "warning")
        return redirect(url_for('checkout'))

    order_id = None
    try:
        conn = get_db_connection(use_db=True)
        with conn.cursor() as cursor:
            # 1. Fetch restaurant
            cursor.execute("SELECT * FROM restaurants WHERE restaurant_id = %s;", (restaurant_id,))
            restaurant = cursor.fetchone()
            if not restaurant:
                conn.close()
                flash("Restaurant not found.", "danger")
                return redirect(url_for('view_cart'))

            # 2. Fetch items and compute totals
            item_ids = list(map(int, cart_items_dict.keys()))
            format_strings = ','.join(['%s'] * len(item_ids))
            cursor.execute(f"SELECT * FROM menu_items WHERE item_id IN ({format_strings});", tuple(item_ids))
            db_items = cursor.fetchall()

            subtotal = 0.0
            order_items_to_insert = []
            for it in db_items:
                qty = cart_items_dict.get(str(it['item_id']), 0)
                if qty > 0:
                    line_subtotal = float(it['price']) * qty
                    subtotal += line_subtotal
                    order_items_to_insert.append((
                        it['item_id'],
                        it['name'],
                        float(it['price']),
                        qty,
                        line_subtotal
                    ))

            delivery_fee = float(restaurant['delivery_fee'])
            tax_amount = round(subtotal * 0.08, 2)
            total_amount = round(subtotal + delivery_fee + tax_amount, 2)
            est_delivery = datetime.datetime.now() + datetime.timedelta(minutes=int(restaurant['delivery_time_mins'] or 30))

            # 3. Insert order
            cursor.execute("""
                INSERT INTO orders (
                    customer_id, restaurant_id, delivery_address, customer_phone,
                    special_instructions, subtotal, delivery_fee, tax_amount, total_amount,
                    payment_method, payment_status, order_status, estimated_delivery_time
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, 'placed', %s
                );
            """, (
                session['user_id'], restaurant_id, delivery_address, customer_phone,
                special_instructions, subtotal, delivery_fee, tax_amount, total_amount,
                payment_method, 'completed' if payment_method != 'cash_on_delivery' else 'pending',
                est_delivery
            ))
            order_id = cursor.lastrowid

            # 4. Insert order items
            items_payload = [
                (order_id, item[0], item[1], item[2], item[3], item[4])
                for item in order_items_to_insert
            ]
            cursor.executemany("""
                INSERT INTO order_items (order_id, item_id, item_name, unit_price, quantity, subtotal)
                VALUES (%s, %s, %s, %s, %s, %s);
            """, items_payload)

        conn.commit()
        conn.close()

        # Clear cart
        session['cart'] = {'restaurant_id': None, 'items': {}}
        session.modified = True

        flash("Your meal order has been successfully placed!", "success")
        return redirect(url_for('order_success', order_id=order_id))

    except Exception as e:
        flash(f"Error placing order: {e}", "danger")
        return redirect(url_for('checkout'))

@app.route('/order/success/<int:order_id>')
@login_required
def order_success(order_id):
    order = None
    try:
        conn = get_db_connection(use_db=True)
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT o.*, r.name AS restaurant_name, r.delivery_time_mins
                FROM orders o
                JOIN restaurants r ON o.restaurant_id = r.restaurant_id
                WHERE o.order_id = %s AND o.customer_id = %s;
            """, (order_id, session['user_id']))
            order = cursor.fetchone()
        conn.close()
    except Exception as e:
        flash(f"Error loading order details: {e}", "danger")
        return redirect(url_for('my_orders'))

    if not order:
        flash("Order not found.", "danger")
        return redirect(url_for('my_orders'))

    return render_template('order_success.html', order=order)

@app.route('/order/track/<int:order_id>')
@login_required
def order_tracker(order_id):
    order = None
    items = []
    try:
        conn = get_db_connection(use_db=True)
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT o.*, 
                       r.name AS restaurant_name, r.address AS restaurant_address, r.phone AS restaurant_phone, r.delivery_time_mins,
                       CONCAT(u.first_name, ' ', u.last_name) AS customer_name,
                       CONCAT(d.first_name, ' ', d.last_name) AS delivery_agent_name,
                       d.phone AS delivery_agent_phone
                FROM orders o
                JOIN restaurants r ON o.restaurant_id = r.restaurant_id
                JOIN users u ON o.customer_id = u.user_id
                LEFT JOIN users d ON o.delivery_agent_id = d.user_id
                WHERE o.order_id = %s AND (o.customer_id = %s OR %s IN ('admin', 'staff', 'delivery_agent', 'restaurant_owner'));
            """, (order_id, session['user_id'], session.get('role')))
            order = cursor.fetchone()

            if order:
                cursor.execute("SELECT * FROM order_items WHERE order_id = %s;", (order_id,))
                items = cursor.fetchall()
        conn.close()
    except Exception as e:
        flash(f"Error loading tracking status: {e}", "danger")
        return redirect(url_for('my_orders'))

    if not order:
        flash("Order not found or permission denied.", "danger")
        return redirect(url_for('my_orders'))

    return render_template('order_tracker.html', order=order, items=items)

@app.route('/my-orders')
@login_required
def my_orders():
    orders = []
    try:
        conn = get_db_connection(use_db=True)
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT o.*, r.name AS restaurant_name, r.image_url AS restaurant_image,
                       (SELECT COUNT(*) FROM reviews rev WHERE rev.order_id = o.order_id) AS has_review,
                       GROUP_CONCAT(CONCAT(oi.quantity, 'x ', oi.item_name) SEPARATOR ', ') AS items_summary
                FROM orders o
                JOIN restaurants r ON o.restaurant_id = r.restaurant_id
                LEFT JOIN order_items oi ON o.order_id = oi.order_id
                WHERE o.customer_id = %s
                GROUP BY o.order_id
                ORDER BY o.order_id DESC;
            """, (session['user_id'],))
            orders = cursor.fetchall()
        conn.close()
    except Exception as e:
        flash(f"Error fetching orders: {e}", "danger")

    return render_template('my_orders.html', orders=orders)

@app.route('/order/cancel/<int:order_id>', methods=['POST'])
@login_required
def cancel_order(order_id):
    try:
        conn = get_db_connection(use_db=True)
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT order_status FROM orders WHERE order_id = %s AND customer_id = %s;
            """, (order_id, session['user_id']))
            order = cursor.fetchone()

            if not order:
                flash("Order not found.", "danger")
            elif order['order_status'] not in ['placed', 'confirmed']:
                flash("Order cannot be cancelled as kitchen has started cooking.", "warning")
            else:
                cursor.execute("""
                    UPDATE orders 
                    SET order_status = 'cancelled', payment_status = 'refunded' 
                    WHERE order_id = %s;
                """, (order_id,))
                conn.commit()
                flash("Order has been cancelled successfully. Refund initiated.", "info")
        conn.close()
    except Exception as e:
        flash(f"Error cancelling order: {e}", "danger")

    return redirect(url_for('order_tracker', order_id=order_id))

@app.route('/order/review/<int:order_id>', methods=['POST'])
@login_required
def submit_review(order_id):
    restaurant_id = request.form.get('restaurant_id')
    rating = int(request.form.get('rating', 5))
    comment = request.form.get('comment', '').strip()

    try:
        conn = get_db_connection(use_db=True)
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO reviews (order_id, customer_id, restaurant_id, rating, comment)
                VALUES (%s, %s, %s, %s, %s);
            """, (order_id, session['user_id'], restaurant_id, rating, comment))

            # Recalculate restaurant average rating
            cursor.execute("""
                SELECT AVG(rating) AS avg_rating FROM reviews WHERE restaurant_id = %s;
            """, (restaurant_id,))
            res = cursor.fetchone()
            if res and res['avg_rating']:
                cursor.execute("""
                    UPDATE restaurants SET rating = %s WHERE restaurant_id = %s;
                """, (round(float(res['avg_rating']), 1), restaurant_id))

        conn.commit()
        conn.close()
        flash("Thank you for your feedback! Your review has been published.", "success")
    except Exception as e:
        flash(f"Error submitting review: {e}", "danger")

    return redirect(url_for('my_orders'))


# -------------------------------------------------------------
# Authentication Routes
# -------------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        try:
            conn = get_db_connection(use_db=True)
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE email = %s;", (email,))
                user = cursor.fetchone()
            conn.close()

            if user and check_password_hash(user['password_hash'], password):
                session['user_id'] = user['user_id']
                session['name'] = f"{user['first_name']} {user['last_name']}"
                session['email'] = user['email']
                session['role'] = user['role']
                session['phone'] = user['phone']
                session['address'] = user['address']

                flash(f"Welcome back, {user['first_name']}!", "success")

                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)

                if user['role'] == 'admin':
                    return redirect(url_for('admin_dashboard'))
                elif user['role'] == 'restaurant_owner':
                    return redirect(url_for('restaurant_dashboard'))
                elif user['role'] == 'delivery_agent':
                    return redirect(url_for('delivery_dashboard'))
                else:
                    return redirect(url_for('index'))
            else:
                flash("Invalid email address or password.", "danger")
        except Exception as e:
            flash(f"Login error: {e}", "danger")

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        role = request.form.get('role', 'customer')

        if not first_name or not last_name or not email or not password or not phone:
            flash("All required fields must be filled out.", "danger")
            return render_template('register.html')

        try:
            conn = get_db_connection(use_db=True)
            with conn.cursor() as cursor:
                cursor.execute("SELECT user_id FROM users WHERE email = %s;", (email,))
                if cursor.fetchone():
                    conn.close()
                    flash("An account with this email already exists.", "warning")
                    return render_template('register.html')

                hashed_password = generate_password_hash(password)
                cursor.execute("""
                    INSERT INTO users (first_name, last_name, email, password_hash, phone, address, role)
                    VALUES (%s, %s, %s, %s, %s, %s, %s);
                """, (first_name, last_name, email, hashed_password, phone, address, role))
                new_user_id = cursor.lastrowid

            conn.commit()
            conn.close()

            flash("Account registered successfully! Please sign in with your credentials.", "success")
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"Registration error: {e}", "danger")

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been securely signed out.", "info")
    return redirect(url_for('index'))


# -------------------------------------------------------------
# Restaurant Partner Management Portal
# -------------------------------------------------------------
@app.route('/restaurant/dashboard')
@restaurant_required
def restaurant_dashboard():
    restaurant = None
    menu_items = []
    active_orders = []
    total_orders_count = 0
    revenue = 0.0

    try:
        conn = get_db_connection(use_db=True)
        with conn.cursor() as cursor:
            # Find restaurant owned by current user (or first restaurant if admin)
            if session.get('role') == 'admin':
                cursor.execute("SELECT * FROM restaurants ORDER BY restaurant_id ASC LIMIT 1;")
            else:
                cursor.execute("SELECT * FROM restaurants WHERE owner_id = %s LIMIT 1;", (session['user_id'],))
            restaurant = cursor.fetchone()

            if restaurant:
                rest_id = restaurant['restaurant_id']

                # Menu items
                cursor.execute("""
                    SELECT m.*, c.name AS category_name
                    FROM menu_items m
                    LEFT JOIN categories c ON m.category_id = c.category_id
                    WHERE m.restaurant_id = %s
                    ORDER BY m.item_id DESC;
                """, (rest_id,))
                menu_items = cursor.fetchall()

                # Active Orders
                cursor.execute("""
                    SELECT o.*, 
                           CONCAT(u.first_name, ' ', u.last_name) AS customer_name,
                           GROUP_CONCAT(CONCAT(oi.quantity, 'x ', oi.item_name) SEPARATOR ', ') AS items_summary
                    FROM orders o
                    JOIN users u ON o.customer_id = u.user_id
                    LEFT JOIN order_items oi ON o.order_id = oi.order_id
                    WHERE o.restaurant_id = %s AND o.order_status IN ('placed', 'confirmed', 'preparing', 'out_for_delivery')
                    GROUP BY o.order_id
                    ORDER BY o.order_id DESC;
                """, (rest_id,))
                active_orders = cursor.fetchall()

                # Totals
                cursor.execute("SELECT COUNT(*) AS total_orders FROM orders WHERE restaurant_id = %s;", (rest_id,))
                total_orders_count = cursor.fetchone()['total_orders']

                cursor.execute("SELECT COALESCE(SUM(total_amount), 0.00) AS total_revenue FROM orders WHERE restaurant_id = %s AND order_status != 'cancelled';", (rest_id,))
                revenue = float(cursor.fetchone()['total_revenue'])

        conn.close()
    except Exception as e:
        flash(f"Error loading partner portal: {e}", "danger")

    return render_template(
        'restaurant_dashboard.html',
        restaurant=restaurant,
        menu_items=menu_items,
        active_orders=active_orders,
        total_orders_count=total_orders_count,
        revenue=revenue
    )

@app.route('/restaurant/toggle/<int:restaurant_id>', methods=['POST'])
@restaurant_required
def toggle_restaurant_status(restaurant_id):
    try:
        conn = get_db_connection(use_db=True)
        with conn.cursor() as cursor:
            cursor.execute("UPDATE restaurants SET is_active = NOT is_active WHERE restaurant_id = %s;", (restaurant_id,))
        conn.commit()
        conn.close()
        flash("Restaurant store status updated.", "success")
    except Exception as e:
        flash(f"Error toggling status: {e}", "danger")

    return redirect(request.referrer or url_for('restaurant_dashboard'))

@app.route('/restaurant/menu/add/<int:restaurant_id>', methods=['GET', 'POST'])
@restaurant_required
def menu_item_create(restaurant_id):
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        price = float(request.form.get('price', 0.0))
        category_id = int(request.form.get('category_id'))
        dietary_type = request.form.get('dietary_type', 'veg')
        description = request.form.get('description', '').strip()
        image_url = request.form.get('image_url', '').strip()
        is_spicy = 'is_spicy' in request.form
        is_popular = 'is_popular' in request.form
        status = 'available' if 'is_available' in request.form else 'out_of_stock'

        try:
            conn = get_db_connection(use_db=True)
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO menu_items (
                        restaurant_id, category_id, name, description, price, dietary_type,
                        is_spicy, is_popular, status, image_url
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                """, (restaurant_id, category_id, name, description, price, dietary_type, is_spicy, is_popular, status, image_url))
            conn.commit()
            conn.close()
            flash("New menu dish successfully created!", "success")
            return redirect(url_for('restaurant_dashboard'))
        except Exception as e:
            flash(f"Error saving menu item: {e}", "danger")

    # GET
    categories = []
    restaurant = None
    try:
        conn = get_db_connection(use_db=True)
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM categories ORDER BY display_order ASC;")
            categories = cursor.fetchall()
            cursor.execute("SELECT * FROM restaurants WHERE restaurant_id = %s;", (restaurant_id,))
            restaurant = cursor.fetchone()
        conn.close()
    except Exception as e:
        flash(f"Database error: {e}", "danger")

    return render_template('menu_item_form.html', restaurant=restaurant, categories=categories, item=None)

@app.route('/restaurant/menu/edit/<int:item_id>', methods=['GET', 'POST'])
@restaurant_required
def menu_item_edit(item_id):
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        price = float(request.form.get('price', 0.0))
        category_id = int(request.form.get('category_id'))
        dietary_type = request.form.get('dietary_type', 'veg')
        description = request.form.get('description', '').strip()
        image_url = request.form.get('image_url', '').strip()
        is_spicy = 'is_spicy' in request.form
        is_popular = 'is_popular' in request.form
        status = 'available' if 'is_available' in request.form else 'out_of_stock'

        try:
            conn = get_db_connection(use_db=True)
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE menu_items 
                    SET category_id = %s, name = %s, description = %s, price = %s,
                        dietary_type = %s, is_spicy = %s, is_popular = %s,
                        status = %s, image_url = %s
                    WHERE item_id = %s;
                """, (category_id, name, description, price, dietary_type, is_spicy, is_popular, status, image_url, item_id))
            conn.commit()
            conn.close()
            flash("Menu item updated successfully!", "success")
            return redirect(url_for('restaurant_dashboard'))
        except Exception as e:
            flash(f"Error updating item: {e}", "danger")

    # GET
    item = None
    categories = []
    restaurant = None
    try:
        conn = get_db_connection(use_db=True)
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM menu_items WHERE item_id = %s;", (item_id,))
            item = cursor.fetchone()
            if item:
                cursor.execute("SELECT * FROM categories ORDER BY display_order ASC;")
                categories = cursor.fetchall()
                cursor.execute("SELECT * FROM restaurants WHERE restaurant_id = %s;", (item['restaurant_id'],))
                restaurant = cursor.fetchone()
        conn.close()
    except Exception as e:
        flash(f"Database error: {e}", "danger")

    return render_template('menu_item_form.html', restaurant=restaurant, categories=categories, item=item)

@app.route('/restaurant/menu/toggle/<int:item_id>', methods=['POST'])
@restaurant_required
def toggle_menu_item_status(item_id):
    try:
        conn = get_db_connection(use_db=True)
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE menu_items 
                SET status = IF(status = 'available', 'out_of_stock', 'available') 
                WHERE item_id = %s;
            """, (item_id,))
        conn.commit()
        conn.close()
        flash("Item availability updated.", "info")
    except Exception as e:
        flash(f"Error updating availability: {e}", "danger")

    return redirect(url_for('restaurant_dashboard'))

@app.route('/restaurant/menu/delete/<int:item_id>', methods=['POST'])
@restaurant_required
def menu_item_delete(item_id):
    try:
        conn = get_db_connection(use_db=True)
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM menu_items WHERE item_id = %s;", (item_id,))
        conn.commit()
        conn.close()
        flash("Menu item deleted.", "info")
    except Exception as e:
        flash(f"Error deleting dish: {e}", "danger")

    return redirect(url_for('restaurant_dashboard'))

@app.route('/restaurant/order/update/<int:order_id>', methods=['POST'])
@restaurant_required
def update_order_status(order_id):
    new_status = request.form.get('new_status')
    try:
        conn = get_db_connection(use_db=True)
        with conn.cursor() as cursor:
            cursor.execute("UPDATE orders SET order_status = %s WHERE order_id = %s;", (new_status, order_id))
        conn.commit()
        conn.close()
        flash(f"Order #ORD-{order_id} updated to {new_status.replace('_', ' ').capitalize()}.", "success")
    except Exception as e:
        flash(f"Error updating status: {e}", "danger")

    return redirect(url_for('restaurant_dashboard'))


# -------------------------------------------------------------
# Delivery Agent Courier Portal
# -------------------------------------------------------------
@app.route('/delivery/dashboard')
@rider_required
def delivery_dashboard():
    rider_id = session['user_id']
    active_deliveries = []
    available_orders = []
    completed_count = 0

    try:
        conn = get_db_connection(use_db=True)
        with conn.cursor() as cursor:
            # Active Deliveries assigned to this rider
            cursor.execute("""
                SELECT o.*, 
                       r.name AS restaurant_name, r.address AS restaurant_address, r.phone AS restaurant_phone,
                       CONCAT(u.first_name, ' ', u.last_name) AS customer_name
                FROM orders o
                JOIN restaurants r ON o.restaurant_id = r.restaurant_id
                JOIN users u ON o.customer_id = u.user_id
                WHERE o.delivery_agent_id = %s AND o.order_status IN ('confirmed', 'preparing', 'out_for_delivery')
                ORDER BY o.order_id ASC;
            """, (rider_id,))
            active_deliveries = cursor.fetchall()

            # Available unassigned orders ready for pickup
            cursor.execute("""
                SELECT o.*, 
                       r.name AS restaurant_name, r.address AS restaurant_address,
                       CONCAT(u.first_name, ' ', u.last_name) AS customer_name,
                       GROUP_CONCAT(CONCAT(oi.quantity, 'x ', oi.item_name) SEPARATOR ', ') AS items_summary
                FROM orders o
                JOIN restaurants r ON o.restaurant_id = r.restaurant_id
                JOIN users u ON o.customer_id = u.user_id
                LEFT JOIN order_items oi ON o.order_id = oi.order_id
                WHERE o.delivery_agent_id IS NULL AND o.order_status IN ('confirmed', 'preparing')
                GROUP BY o.order_id
                ORDER BY o.order_id ASC;
            """, ())
            available_orders = cursor.fetchall()

            # Completed count for this rider
            cursor.execute("""
                SELECT COUNT(*) AS cnt FROM orders 
                WHERE delivery_agent_id = %s AND order_status = 'delivered';
            """, (rider_id,))
            completed_count = cursor.fetchone()['cnt']

        conn.close()
    except Exception as e:
        flash(f"Error loading rider dashboard: {e}", "danger")

    return render_template(
        'delivery_dashboard.html',
        active_deliveries=active_deliveries,
        available_orders=available_orders,
        completed_count=completed_count
    )

@app.route('/delivery/claim/<int:order_id>', methods=['POST'])
@rider_required
def claim_delivery_order(order_id):
    rider_id = session['user_id']
    try:
        conn = get_db_connection(use_db=True)
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE orders 
                SET delivery_agent_id = %s, order_status = 'out_for_delivery'
                WHERE order_id = %s AND delivery_agent_id IS NULL;
            """, (rider_id, order_id))
        conn.commit()
        conn.close()
        flash(f"Order #ORD-{order_id} assigned to you! Safe riding.", "success")
    except Exception as e:
        flash(f"Error claiming run: {e}", "danger")

    return redirect(url_for('delivery_dashboard'))

@app.route('/delivery/status/<int:order_id>', methods=['POST'])
@rider_required
def update_rider_order_status(order_id):
    new_status = request.form.get('new_status')
    try:
        conn = get_db_connection(use_db=True)
        with conn.cursor() as cursor:
            payment_clause = ", payment_status = 'completed'" if new_status == 'delivered' else ""
            cursor.execute(f"""
                UPDATE orders 
                SET order_status = %s {payment_clause}
                WHERE order_id = %s AND delivery_agent_id = %s;
            """, (new_status, order_id, session['user_id']))
        conn.commit()
        conn.close()
        flash(f"Delivery status updated to {new_status.replace('_', ' ').capitalize()}.", "success")
    except Exception as e:
        flash(f"Error updating status: {e}", "danger")

    return redirect(url_for('delivery_dashboard'))


# -------------------------------------------------------------
# Admin Operations Portal
# -------------------------------------------------------------
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    metrics = {}
    orders = []
    restaurants = []
    users = []

    try:
        conn = get_db_connection(use_db=True)
        with conn.cursor() as cursor:
            # 1. Telemetry Metrics
            cursor.execute("SELECT COALESCE(SUM(total_amount), 0.00) AS gross FROM orders WHERE order_status != 'cancelled';")
            metrics['gross_volume'] = float(cursor.fetchone()['gross'])

            cursor.execute("SELECT COUNT(*) AS cnt FROM orders;")
            metrics['total_orders'] = cursor.fetchone()['cnt']

            cursor.execute("SELECT COUNT(*) AS cnt FROM restaurants;")
            metrics['total_restaurants'] = cursor.fetchone()['cnt']

            cursor.execute("SELECT COUNT(*) AS cnt FROM users;")
            metrics['total_users'] = cursor.fetchone()['cnt']

            # 2. Master Orders Log
            cursor.execute("""
                SELECT o.*, r.name AS restaurant_name,
                       CONCAT(u.first_name, ' ', u.last_name) AS customer_name,
                       CONCAT(d.first_name, ' ', d.last_name) AS delivery_agent_name
                FROM orders o
                JOIN restaurants r ON o.restaurant_id = r.restaurant_id
                JOIN users u ON o.customer_id = u.user_id
                LEFT JOIN users d ON o.delivery_agent_id = d.user_id
                ORDER BY o.order_id DESC;
            """)
            orders = cursor.fetchall()

            # 3. Restaurants Directory
            cursor.execute("""
                SELECT r.*, u.email AS owner_email
                FROM restaurants r
                LEFT JOIN users u ON r.owner_id = u.user_id
                ORDER BY r.restaurant_id DESC;
            """)
            restaurants = cursor.fetchall()

            # 4. Users Directory
            cursor.execute("SELECT user_id, first_name, last_name, email, phone, address, role, created_at FROM users ORDER BY user_id DESC;")
            users = cursor.fetchall()

        conn.close()
    except Exception as e:
        flash(f"Error loading admin portal: {e}", "danger")

    return render_template(
        'admin_dashboard.html',
        metrics=metrics,
        orders=orders,
        restaurants=restaurants,
        users=users
    )

@app.route('/admin/restaurant/add', methods=['POST'])
@admin_required
def admin_add_restaurant():
    name = request.form.get('name', '').strip()
    cuisine_type = request.form.get('cuisine_type', '').strip()
    description = request.form.get('description', '').strip()
    phone = request.form.get('phone', '').strip()
    address = request.form.get('address', '').strip()
    city = request.form.get('city', 'Downtown').strip()
    delivery_time_mins = int(request.form.get('delivery_time_mins', 30))
    delivery_fee = float(request.form.get('delivery_fee', 2.49))
    minimum_order = float(request.form.get('minimum_order', 12.00))
    image_url = request.form.get('image_url', '').strip()

    if not image_url:
        image_url = "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=800&q=80"

    try:
        conn = get_db_connection(use_db=True)
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO restaurants (
                    owner_id, name, cuisine_type, description, phone, address, city,
                    rating, delivery_time_mins, delivery_fee, minimum_order, image_url, is_active
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, 4.5, %s, %s, %s, %s, TRUE);
            """, (session['user_id'], name, cuisine_type, description, phone, address, city, delivery_time_mins, delivery_fee, minimum_order, image_url))
        conn.commit()
        conn.close()
        flash(f"Restaurant '{name}' created successfully!", "success")
    except Exception as e:
        flash(f"Error creating restaurant: {e}", "danger")

    return redirect(url_for('admin_dashboard'))


# -------------------------------------------------------------
# Self-Healing Database Diagnostics & Status Panel
# -------------------------------------------------------------
@app.route('/db-status')
def db_status():
    connected, db_msg = test_connection()

    table_stats = {
        'users': {'exists': False, 'count': 0},
        'categories': {'exists': False, 'count': 0},
        'restaurants': {'exists': False, 'count': 0},
        'menu_items': {'exists': False, 'count': 0},
        'orders': {'exists': False, 'count': 0},
        'order_items': {'exists': False, 'count': 0},
        'reviews': {'exists': False, 'count': 0}
    }

    if connected:
        try:
            conn = get_db_connection(use_db=True)
            with conn.cursor() as cursor:
                cursor.execute("SHOW TABLES;")
                existing_tables = [list(r.values())[0] for r in cursor.fetchall()]

                for table in table_stats.keys():
                    if table in existing_tables:
                        table_stats[table]['exists'] = True
                        cursor.execute(f"SELECT COUNT(*) AS count FROM `{table}`;")
                        row = cursor.fetchone()
                        table_stats[table]['count'] = row['count'] if row else 0
            conn.close()
        except Exception as e:
            db_msg += f" (Warning: Error inspecting tables: {e})"

    return render_template(
        'db_status.html',
        connected=connected,
        db_msg=db_msg,
        table_stats=table_stats
    )

@app.route('/db-status/update-credentials', methods=['POST'])
def update_db_credentials():
    host = request.form.get('db_host', '127.0.0.1').strip()
    user = request.form.get('db_user', 'root').strip()
    password = request.form.get('db_password', '').strip()
    name = request.form.get('db_name', 'food_delivery_db').strip()
    port = request.form.get('db_port', '3306').strip()

    env_path = os.path.join(os.path.dirname(__file__), '.env')
    try:
        lines = []
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                lines = f.readlines()

        keys = {'DB_HOST': host, 'DB_PORT': port, 'DB_USER': user, 'DB_PASSWORD': password, 'DB_NAME': name}
        new_lines = []
        found_keys = set()

        for line in lines:
            parts = line.strip().split('=', 1)
            if len(parts) == 2 and parts[0] in keys:
                new_lines.append(f"{parts[0]}={keys[parts[0]]}\n")
                found_keys.add(parts[0])
            else:
                new_lines.append(line)

        for k, v in keys.items():
            if k not in found_keys:
                new_lines.append(f"{k}={v}\n")

        with open(env_path, 'w') as f:
            f.writelines(new_lines)

        Config.DB_HOST = host
        Config.DB_PORT = int(port)
        Config.DB_USER = user
        Config.DB_PASSWORD = password
        Config.DB_NAME = name

        ok, msg = test_connection()
        if ok:
            init_db()
            flash("Database credentials updated and connection established successfully!", "success")
        else:
            flash(f"Credentials saved to .env, but connection failed: {msg}", "warning")
    except Exception as e:
        flash(f"Failed to update .env: {e}", "danger")

    return redirect(url_for('db_status'))

@app.route('/db-status/seed', methods=['POST'])
def seed_database():
    try:
        init_db()
        success = seed_sample_data()
        if success:
            flash("Sample food delivery data seeded successfully!", "success")
        else:
            flash("Database already contains data or seeding encountered an error.", "info")
    except Exception as e:
        flash(f"Seeding error: {e}", "danger")
    return redirect(url_for('db_status'))


# -------------------------------------------------------------
# Main Application Launcher
# -------------------------------------------------------------
if __name__ == '__main__':
    # Verify and initialize schema on startup
    init_db()
    seed_sample_data()
    app.run(host='0.0.0.0', port=Config.PORT, debug=Config.FLASK_DEBUG)
