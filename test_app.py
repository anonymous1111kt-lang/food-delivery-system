#!/usr/bin/env python3
"""
Comprehensive functional and endpoint test suite for QuickBite Food Delivery System.
"""
import unittest
from app import app
from database import get_db_connection

class TestQuickBiteApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        cls.client = app.test_client()

    def test_01_index_page(self):
        """Test home catalog page renders with restaurants and filters."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'QuickBite', response.data)
        self.assertIn(b'Bella Napoli Pizzeria', response.data)
        self.assertIn(b'Explore by Cuisine', response.data)

        # Test search query
        res_search = self.client.get('/?q=burger')
        self.assertEqual(res_search.status_code, 200)
        self.assertIn(b'The Prime Burger Co.', res_search.data)

        # Test category filter
        res_cat = self.client.get('/?category=Pizza+%26+Italian')
        self.assertEqual(res_cat.status_code, 200)
        self.assertIn(b'Bella Napoli Pizzeria', res_cat.data)

    def test_02_restaurant_detail(self):
        """Test restaurant menu page with dietary filters."""
        response = self.client.get('/restaurant/1')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Bella Napoli Pizzeria', response.data)
        self.assertIn(b'Margherita D.O.P.', response.data)

        # Dietary filter: veg
        res_veg = self.client.get('/restaurant/1?diet=veg')
        self.assertEqual(res_veg.status_code, 200)
        self.assertIn(b'Margherita D.O.P.', res_veg.data)

    def test_03_db_status(self):
        """Test database status diagnostic view."""
        response = self.client.get('/db-status')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'MySQL Database Diagnostics', response.data)
        self.assertIn(b'Connected', response.data)

    def test_04_auth_login_and_roles(self):
        """Test logging in as customer, admin, partner, rider."""
        # 1. Customer login
        res = self.client.post('/login', data={
            'email': 'john.doe@example.com',
            'password': 'customer123'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Welcome back, John', res.data)

        # Logout
        self.client.get('/logout', follow_redirects=True)

        # 2. Admin login
        res = self.client.post('/login', data={
            'email': 'admin@quickbite.com',
            'password': 'admin123'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Admin Operations Portal', res.data)

        # Logout
        self.client.get('/logout', follow_redirects=True)

    def test_05_cart_and_order_flow(self):
        """Test adding item to cart, checkout, placing order, tracking, and my-orders."""
        with self.client:
            # Login as customer
            self.client.post('/login', data={
                'email': 'john.doe@example.com',
                'password': 'customer123'
            }, follow_redirects=True)

            # Add item 1 to cart
            res = self.client.post('/cart/add', data={
                'item_id': 1,
                'restaurant_id': 1,
                'quantity': 2
            }, follow_redirects=True)
            self.assertEqual(res.status_code, 200)

            # View cart
            res = self.client.get('/cart')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b'Margherita D.O.P.', res.data)

            # Checkout page
            res = self.client.get('/checkout')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b'Select Payment Method', res.data)

            # Place order
            res = self.client.post('/order/place', data={
                'delivery_address': '742 Evergreen Terrace, Apt 4B, Downtown',
                'customer_phone': '555-0199',
                'special_instructions': 'Test unit order',
                'payment_method': 'upi'
            }, follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn(b'Order Confirmed!', res.data)

            # My Orders
            res_orders = self.client.get('/my-orders')
            self.assertEqual(res_orders.status_code, 200)
            self.assertIn(b'My Orders', res_orders.data)

    def test_06_partner_portal_and_menu(self):
        """Test restaurant partner dashboard and menu item manipulation."""
        with self.client:
            self.client.post('/login', data={
                'email': 'luigi@quickbite.com',
                'password': 'owner123'
            }, follow_redirects=True)

            res = self.client.get('/restaurant/dashboard')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b'Bella Napoli Pizzeria', res.data)
            self.assertIn(b'Live Kitchen Queue', res.data)

            # Get menu add form
            res_form = self.client.get('/restaurant/menu/add/1')
            self.assertEqual(res_form.status_code, 200)
            self.assertIn(b'Add New Menu Dish', res_form.data)

    def test_07_rider_portal(self):
        """Test courier rider portal."""
        with self.client:
            self.client.post('/login', data={
                'email': 'david.rider@quickbite.com',
                'password': 'rider123'
            }, follow_redirects=True)

            res = self.client.get('/delivery/dashboard')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b'Rider Dispatch Portal', res.data)

    def test_08_admin_portal(self):
        """Test admin dashboard telemetry and tables."""
        with self.client:
            self.client.post('/login', data={
                'email': 'admin@quickbite.com',
                'password': 'admin123'
            }, follow_redirects=True)

            res = self.client.get('/admin/dashboard')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b'Admin Operations Portal', res.data)
            self.assertIn(b'Platform Gross Volume', res.data)
            self.assertIn(b'Master Orders Audit', res.data)

if __name__ == '__main__':
    unittest.main()
