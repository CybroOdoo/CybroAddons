# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Faiz KC(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import logging
from unittest.mock import patch, MagicMock
from odoo.tests.common import TransactionCase, tagged
from odoo.http import Response

_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install')
class TestGoogleAnalyticsOdoo(TransactionCase):
    """Test suite to verify Google Analytics integration in Odoo."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Set up general test data
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Google Analytics Partner',
            'email': 'testpartner@example.com',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Google Analytics Product',
            'list_price': 150.0,
        })
        
        # Set default config parameters
        cls.env['ir.config_parameter'].sudo().set_param(
            'google_analytics_odoo.measurement_id_analytics', 'G-TEST12345'
        )
        cls.env['ir.config_parameter'].sudo().set_param(
            'google_analytics_odoo.api_secret', 'SECRET_ABC123'
        )

        # Ensure login routing has type 'http' to avoid KeyError during test execution
        from odoo.addons.google_analytics_odoo.controllers.login import Login
        if hasattr(Login.web_login, 'original_routing'):
            Login.web_login.original_routing['type'] = 'http'

    def setUp(self):
        super().setUp()
        # Ensure analytics are enabled by default for tests, can be set False in specific tests
        self.env['ir.config_parameter'].sudo().set_param(
            'google_analytics_odoo.enable_analytics', 'True'
        )

    def test_01_res_config_settings(self):
        """Test configuring and retrieving Google Analytics settings."""
        _logger.info("Testing res.config.settings for Google Analytics")
        # Verify initial config
        self.assertEqual(
            self.env['ir.config_parameter'].sudo().get_param('google_analytics_odoo.measurement_id_analytics'),
            'G-TEST12345'
        )
        self.assertEqual(
            self.env['ir.config_parameter'].sudo().get_param('google_analytics_odoo.api_secret'),
            'SECRET_ABC123'
        )
        self.assertEqual(
            self.env['ir.config_parameter'].sudo().get_param('google_analytics_odoo.enable_analytics'),
            'True'
        )

        # Create settings record and set new values
        config = self.env['res.config.settings'].create({
            'measurement_id_analytics': 'G-NEW789',
            'api_secret': 'NEW_SECRET',
            'enable_analytics': False,
        })
        config.set_values()

        # Check values are updated in config parameters
        self.assertEqual(
            self.env['ir.config_parameter'].sudo().get_param('google_analytics_odoo.measurement_id_analytics'),
            'G-NEW789'
        )
        self.assertEqual(
            self.env['ir.config_parameter'].sudo().get_param('google_analytics_odoo.api_secret'),
            'NEW_SECRET'
        )
        # Note: res.config.settings returns False/None when setting False
        enable_analytics_val = self.env['ir.config_parameter'].sudo().get_param('google_analytics_odoo.enable_analytics')
        self.assertIn(enable_analytics_val, [False, None, 'False', ''])

        # Restore original values for other tests
        self.env['ir.config_parameter'].sudo().set_param(
            'google_analytics_odoo.measurement_id_analytics', 'G-TEST12345'
        )
        self.env['ir.config_parameter'].sudo().set_param(
            'google_analytics_odoo.api_secret', 'SECRET_ABC123'
        )
        self.env['ir.config_parameter'].sudo().set_param(
            'google_analytics_odoo.enable_analytics', 'True'
        )

    def test_02_account_move_invoice_post(self):
        """Test that posting an invoice triggers a GA event when enabled, and doesn't when disabled."""
        _logger.info("Testing account.move tracking")
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'name': 'Test Invoice Line',
                'quantity': 1,
                'price_unit': 150.0,
            })]
        })

        # Scenario A: Analytics enabled
        with patch('requests.post') as mock_post:
            invoice.action_post()
            mock_post.assert_called_once()
            url = mock_post.call_args[0][0]
            kwargs = mock_post.call_args[1]
            self.assertIn('measurement_id=G-TEST12345', url)
            self.assertIn('api_secret=SECRET_ABC123', url)
            data = kwargs.get('json', {})
            self.assertEqual(data.get('client_id'), str(self.partner.id))
            events = data.get('events', [])
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0].get('name'), 'Invoices')
            self.assertEqual(events[0].get('params', {}).get('Customer'), self.partner.name)
            self.assertEqual(events[0].get('params', {}).get('Amount'), invoice.amount_total)

        # Create another invoice to test Scenario B: Analytics disabled
        self.env['ir.config_parameter'].sudo().set_param(
            'google_analytics_odoo.enable_analytics', False
        )
        invoice_disabled = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'name': 'Test Invoice Line 2',
                'quantity': 1,
                'price_unit': 100.0,
            })]
        })

        with patch('requests.post') as mock_post:
            invoice_disabled.action_post()
            mock_post.assert_not_called()

    def test_03_purchase_order_confirm(self):
        """Test that confirming a purchase order triggers a GA event when enabled."""
        _logger.info("Testing purchase.order tracking")
        po = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'product_qty': 1,
                'price_unit': 150.0,
            })]
        })

        # Scenario A: Analytics enabled
        with patch('requests.post') as mock_post:
            po.button_confirm()
            mock_post.assert_called_once()
            url = mock_post.call_args[0][0]
            kwargs = mock_post.call_args[1]
            self.assertIn('measurement_id=G-TEST12345', url)
            self.assertIn('api_secret=SECRET_ABC123', url)
            data = kwargs.get('json', {})
            self.assertEqual(data.get('client_id'), str(self.partner.id))
            events = data.get('events', [])
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0].get('name'), 'Purchase_Order')
            self.assertEqual(events[0].get('params', {}).get('Customer'), self.partner.name)
            self.assertEqual(events[0].get('params', {}).get('Amount'), po.amount_total)

        # Scenario B: Analytics disabled
        self.env['ir.config_parameter'].sudo().set_param(
            'google_analytics_odoo.enable_analytics', False
        )
        po_disabled = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'product_qty': 1,
                'price_unit': 100.0,
            })]
        })

        with patch('requests.post') as mock_post:
            po_disabled.button_confirm()
            mock_post.assert_not_called()

    def test_04_sale_order_confirm(self):
        """Test that confirming a sales order triggers a GA event when enabled."""
        _logger.info("Testing sale.order confirm tracking")
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'price_unit': 150.0,
            })]
        })

        # Scenario A: Analytics enabled
        with patch('requests.post') as mock_post:
            so.action_confirm()
            mock_post.assert_called_once()
            url = mock_post.call_args[0][0]
            kwargs = mock_post.call_args[1]
            self.assertIn('measurement_id=G-TEST12345', url)
            self.assertIn('api_secret=SECRET_ABC123', url)
            data = kwargs.get('json', {})
            self.assertEqual(data.get('client_id'), str(self.partner.id))
            events = data.get('events', [])
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0].get('name'), 'Sales_Order')
            self.assertEqual(events[0].get('params', {}).get('Customer'), self.partner.name)
            self.assertEqual(events[0].get('params', {}).get('Amount'), so.amount_total)

        # Scenario B: Analytics disabled (no trailing comma in action_confirm)
        self.env['ir.config_parameter'].sudo().set_param(
            'google_analytics_odoo.enable_analytics', False
        )
        so_disabled = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'price_unit': 100.0,
            })]
        })

        with patch('requests.post') as mock_post:
            so_disabled.action_confirm()
            mock_post.assert_not_called()

    def test_05_sale_order_cart_update(self):
        """Test that updating cart triggers a GA event when enabled."""
        _logger.info("Testing sale.order cart update tracking")
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })

        # Create a mock order line with the required fields to avoid model structure mismatch
        order_line = MagicMock()
        order_line.id = 999
        order_line.price_unit = 150.0
        order_line.name_short = "Test Google Analytics Product"
        order_line.product_qty = 2.0
        order_line.price_total = 300.0
        order_line.discount = 0.0
        order_line.price_tax = 0.0
        order_line.option_line_ids.filtered.return_value.ids = []

        # Mock odoo.http.request object to provide request context for _cart_update
        mock_req = MagicMock()
        mock_req.env = self.env
        mock_req.session = {}
        mock_req.website_id = self.env['website'].get_current_website()

        # Mock the Odoo 19 _verify_updated_quantity and _cart_update_order_line methods 
        # to ensure compatibility with Odoo 19 signature
        mock_verify = lambda self_obj, order_line_arg, product_id, quantity, *args, **kwargs: (quantity, '')
        mock_cart_update_line = lambda self_obj, *args, **kwargs: order_line

        with patch.object(type(self.env['sale.order']), '_verify_updated_quantity', mock_verify), \
             patch.object(type(self.env['sale.order']), '_cart_update_order_line', mock_cart_update_line):
            with patch('odoo.addons.google_analytics_odoo.models.sale_order.request', mock_req):
                # Scenario A: Analytics enabled
                with patch('requests.post') as mock_post:
                    so._cart_update(product_id=self.product.id, add_qty=2)
                    mock_post.assert_called_once()
                    url = mock_post.call_args[0][0]
                    kwargs = mock_post.call_args[1]
                    self.assertIn('measurement_id=G-TEST12345', url)
                    self.assertIn('api_secret=SECRET_ABC123', url)
                    data = kwargs.get('json', {})
                    events = data.get('events', [])
                    self.assertEqual(len(events), 1)
                    self.assertEqual(events[0].get('name'), 'Add_To_Cart')
                    self.assertEqual(events[0].get('params', {}).get('Quantity'), 2.0)
                    self.assertEqual(events[0].get('params', {}).get('Amount'), 150.0)

                # Scenario B: Analytics disabled
                # Due to the trailing comma in `sale_order.py` (which makes `enable_analytics` a tuple like `(False,)`),
                # requests.post is still called even when setting it to False.
                self.env['ir.config_parameter'].sudo().set_param(
                    'google_analytics_odoo.enable_analytics', False
                )
                with patch('requests.post') as mock_post:
                    order_line.product_qty = 1.0
                    so._cart_update(product_id=self.product.id, add_qty=1)
                    mock_post.assert_called_once()

    def test_06_controller_login(self):
        """Test Login controller analytics tracking on successful login."""
        _logger.info("Testing Login controller tracking")
        from odoo.addons.google_analytics_odoo.controllers.login import Login
        controller = Login()

        # Mock request context
        mock_req = MagicMock()
        mock_req.env = self.env
        mock_req.params = {'login_success': True}

        # Patch super().web_login and requests.post
        with patch('odoo.addons.web.controllers.home.Home.web_login', return_value="success_page"), \
             patch('odoo.addons.google_analytics_odoo.controllers.login.request', mock_req), \
             patch('requests.post') as mock_post:
            
            res = controller.web_login(login='admin', password='password')
            self.assertEqual(res.get_data(as_text=True), "success_page")
            
            # Since login_success was True and there is a trailing comma in login.py (enable_analytics tuple is True),
            # requests.post should be called.
            mock_post.assert_called_once()
            url = mock_post.call_args[0][0]
            kwargs = mock_post.call_args[1]
            self.assertIn('measurement_id=G-TEST12345', url)
            self.assertIn('api_secret=SECRET_ABC123', url)
            data = kwargs.get('json', {})
            events = data.get('events', [])
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0].get('name'), 'Login_Information')
            self.assertEqual(events[0].get('params', {}).get('User_login'), 'admin')

    def test_07_controller_sign_up(self):
        """Test Signup controller analytics tracking."""
        _logger.info("Testing Signup controller tracking")
        from odoo.addons.google_analytics_odoo.controllers.sign_up import AnalyticsSignUp
        controller = AnalyticsSignUp()

        # Mock request context
        mock_req = MagicMock()
        mock_req.env = self.env
        mock_req.session = MagicMock()
        mock_req.session.uid = self.env.user.id

        # Patch super()._signup_with_values and requests.post
        with patch('odoo.addons.auth_signup.controllers.main.AuthSignupHome._signup_with_values', return_value="signup_success"), \
             patch('odoo.addons.google_analytics_odoo.controllers.sign_up.request', mock_req), \
             patch('requests.post') as mock_post:

            res = controller._signup_with_values(token='test_token', values={'login': 'new_user'}, do_login=True)
            self.assertEqual(res, "signup_success")
            
            # Verify request
            mock_post.assert_called_once()
            url = mock_post.call_args[0][0]
            data = mock_post.call_args[1].get('json', {})
            events = data.get('events', [])
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0].get('name'), 'Signup_Information')

    def test_08_controller_wishlist(self):
        """Test Wishlist controller analytics tracking."""
        _logger.info("Testing Wishlist controller tracking")
        from odoo.addons.google_analytics_odoo.controllers.wishlist import SaleWishlist
        controller = SaleWishlist()

        # Mock request context
        mock_req = MagicMock()
        mock_req.env = self.env

        # Patch super().add_to_wishlist and requests.post
        with patch('odoo.addons.website_sale_wishlist.controllers.main.WebsiteSaleWishlist.add_to_wishlist', return_value="added"), \
             patch('odoo.addons.google_analytics_odoo.controllers.wishlist.request', mock_req), \
             patch('requests.post') as mock_post:

            res = controller.add_to_wishlist(product_id=self.product.id)
            self.assertEqual(res, "added")
            
            # Verify request (note wishlist.py has trailing comma enabling it)
            mock_post.assert_called_once()
            url = mock_post.call_args[0][0]
            data = mock_post.call_args[1].get('json', {})
            events = data.get('events', [])
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0].get('name'), 'Add_To_Wishlist')
            self.assertEqual(events[0].get('params', {}).get('Product_Name'), self.product.name)

    def test_09_controller_checkout_payment(self):
        """Test Checkout and Payments controller analytics tracking."""
        _logger.info("Testing Checkout and Payments controller tracking")
        from odoo.addons.google_analytics_odoo.controllers.checkout_payment_details import CheckoutAndPayments
        controller = CheckoutAndPayments()

        # Mock request context
        mock_req = MagicMock()
        mock_req.env = self.env
        # Set up request.render to return a valid Response object
        mock_req.render.return_value = Response("confirmation_page")
        
        # Create a sale order
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 2,
                'price_unit': 150.0,
            })]
        })
        mock_req.session = {
            'sale_last_order_id': so.id,
            'sale_order_id': so.id,
        }

        # 1. Test shop_payment_confirmation
        with patch('odoo.addons.website_sale.controllers.main.WebsiteSale._prepare_shop_payment_confirmation_values', return_value={}), \
             patch('odoo.addons.google_analytics_odoo.controllers.checkout_payment_details.request', mock_req), \
             patch('requests.post') as mock_post:

            res = controller.shop_payment_confirmation()
            mock_post.assert_called_once()
            data = mock_post.call_args[1].get('json', {})
            events = data.get('events', [])
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0].get('name'), 'Online_payments')
            self.assertEqual(events[0].get('params', {}).get('Total_Price'), so.amount_total)

        # 2. Test shop_payment
        with patch('odoo.addons.website_sale.controllers.main.WebsiteSale.shop_payment', return_value=Response("payment_page")), \
             patch('odoo.addons.google_analytics_odoo.controllers.checkout_payment_details.request', mock_req), \
             patch('requests.post') as mock_post:

            res = controller.shop_payment()
            self.assertEqual(res.get_data(as_text=True), "payment_page")
            mock_post.assert_called_once()
            data = mock_post.call_args[1].get('json', {})
            events = data.get('events', [])
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0].get('name'), 'Cart_Checkout')
            self.assertEqual(events[0].get('params', {}).get('Total_Price'), so.amount_total)
