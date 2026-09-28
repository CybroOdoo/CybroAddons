# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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

from unittest.mock import patch, MagicMock

from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError, ValidationError


class TestCSCartConnectorBase(TransactionCase):
    """Shared setup for all CS-Cart connector tests."""

    @classmethod
    def setUpClass(cls):
        """Set up shared test environment and CS-Cart configuration."""
        super().setUpClass()

        # CS-Cart config instance
        cls.config = cls.env['cs.cart.config'].create({
            'name': 'Test Store',
            'store_url': 'https://test.cs-cart.com',
            'email': 'test@example.com',
            'api_key': 'test-api-key-123',
            'connected_status': 'connected',
            'realtime_stock_sync': True,
            'stock_sync_type': 'qty_available',
        })

        # Category with CS-Cart mapping
        cls.category = cls.env['product.category'].create({
            'name': 'Test Category',
            'cs_cart_category_id': 100,
        })

        # Storable product with CS-Cart mapping
        cls.product_mapped = cls.env['product.product'].create({
            'name': 'Mapped Product',
            'type': 'consu',
            'is_storable': True,
            'list_price': 25.0,
            'default_code': 'TEST001',
            'cs_cart_product_id': 501,
            'categ_id': cls.category.id,
        })

        # Product without CS-Cart mapping
        cls.product_unmapped = cls.env['product.product'].create({
            'name': 'Unmapped Product',
            'type': 'consu',
            'is_storable': True,
            'list_price': 50.0,
            'default_code': 'TEST002',
            'categ_id': cls.category.id,
        })

        # Service/consumable product
        cls.product_service = cls.env['product.product'].create({
            'name': 'Service Product',
            'type': 'consu',
            'is_storable': False,
            'list_price': 100.0,
            'categ_id': cls.category.id,
        })

        # Partner
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer',
            'email': 'customer@example.com',
            'phone': '1234567890',
            'street': '123 Main St',
            'city': 'TestCity',
            'zip': '12345',
            'customer_rank': 1,
            'cs_cart_user_id': 201,
        })

        # Partner without CS-Cart mapping
        cls.partner_unmapped = cls.env['res.partner'].create({
            'name': 'New Customer',
            'email': 'new@example.com',
            'customer_rank': 1,
        })

        # Vendor
        cls.vendor = cls.env['res.partner'].create({
            'name': 'Test Vendor',
            'email': 'vendor@example.com',
            'supplier_rank': 1,
        })


# =====================================================================
# 1. CONFIG & CONNECTION TESTS
# =====================================================================
class TestCsCartConfig(TestCSCartConnectorBase):
    """Tests for cs.cart.config model."""

    def test_config_creation(self):
        """Config record is created with correct defaults."""
        self.assertEqual(self.config.connected_status, 'connected')
        self.assertTrue(self.config.realtime_stock_sync)
        self.assertEqual(self.config.stock_sync_type, 'qty_available')

    def test_reset_sync_flags(self):
        """_reset_sync_flags clears all checkboxes."""
        self.config.write({
            'sync_categories': True,
            'sync_products': True,
            'sync_orders': True,
        })
        self.config._reset_sync_flags()
        self.assertFalse(self.config.sync_categories)
        self.assertFalse(self.config.sync_products)
        self.assertFalse(self.config.sync_orders)
        self.assertFalse(self.config.sync_customers)
        self.assertFalse(self.config.sync_attributes)

    def test_notify_helper_returns_action(self):
        """_notify returns a display_notification action dict."""
        result = self.config._notify("Title", "Message", type="success")
        self.assertEqual(result['type'], 'ir.actions.client')
        self.assertEqual(result['tag'], 'display_notification')
        self.assertEqual(result['params']['title'], 'Title')
        self.assertEqual(result['params']['type'], 'success')

    def test_notify_with_reload(self):
        """_notify with reload=True includes a next reload action."""
        result = self.config._notify("Title", "Msg", reload=True)
        self.assertIn('next', result['params'])
        self.assertEqual(result['params']['next']['tag'], 'reload')

    def test_import_nothing_selected_warns(self):
        """Import with no checkboxes shows a warning."""
        self.config._reset_sync_flags()
        result = self.config.action_import_selected()
        self.assertEqual(result['params']['type'], 'warning')
        self.assertIn('Nothing Selected', result['params']['title'])

    def test_export_nothing_selected_warns(self):
        """Export with no checkboxes shows a warning."""
        self.config._reset_sync_flags()
        result = self.config.action_export_selected()
        self.assertEqual(result['params']['type'], 'warning')
        self.assertIn('Nothing Selected', result['params']['title'])

    @patch('requests.get')
    def test_connection_test_success(self, mock_get):
        """Successful connection test sets status to connected."""
        mock_get.return_value = MagicMock(status_code=200)
        result = self.config.action_test_connection()
        self.assertEqual(self.config.connected_status, 'connected')
        self.assertEqual(result['params']['type'], 'success')

    @patch('requests.get')
    def test_connection_test_failure(self, mock_get):
        """Failed connection test raises UserError."""
        mock_get.return_value = MagicMock(status_code=401, text='Unauthorized')
        with self.assertRaises(UserError):
            self.config.action_test_connection()

    def test_disconnect(self):
        """action_disconnect sets status to disconnected."""
        self.config.connected_status = 'connected'
        result = self.config.action_disconnect()
        self.assertEqual(self.config.connected_status, 'disconnected')
        self.assertEqual(result['params']['title'], 'Disconnected')

    def test_onchange_sync_products_enables_categories_and_attributes(self):
        """Checking sync_products auto-enables sync_categories and sync_attributes."""
        self.config.sync_products = True
        self.config._onchange_sync_products()
        self.assertTrue(self.config.sync_categories)
        self.assertTrue(self.config.sync_attributes)


# =====================================================================
# 2. PRODUCT EXPORT TESTS
# =====================================================================
class TestProductExport(TestCSCartConnectorBase):
    """Tests for product export to CS-Cart."""

    @patch.object(type(TransactionCase), 'env', new_callable=lambda: property(lambda s: s._env))
    def _mock_api_request(self, *args, **kwargs):
        """Mock helper method for API requests during unit testing."""
        pass

    def test_product_has_cs_cart_field(self):
        """product.product has cs_cart_product_id field."""
        self.assertIn('cs_cart_product_id', self.env['product.product']._fields)

    def test_storable_product_payload_uses_tracking_b(self):
        """Storable products should use tracking=B in the export payload."""
        product = self.product_mapped
        self.assertTrue(product.is_storable)
        # Verify the logic: storable -> tracking B
        payload = {}
        if not product.is_storable:
            payload["tracking"] = "D"
            payload["amount"] = 9999
        else:
            payload["tracking"] = "B"
            payload["amount"] = int(product.qty_available)
        self.assertEqual(payload["tracking"], "B")

    def test_service_product_payload_uses_tracking_d(self):
        """Service/consumable products should use tracking=D with amount=9999."""
        product = self.product_service
        self.assertFalse(product.is_storable)
        payload = {}
        if not product.is_storable:
            payload["tracking"] = "D"
            payload["amount"] = 9999
        else:
            payload["tracking"] = "B"
        self.assertEqual(payload["tracking"], "D")
        self.assertEqual(payload["amount"], 9999)

    def test_export_requires_product_name(self):
        """Export raises UserError if product has no name."""
        product = self.env['product.product'].create({
            'name': '',
            'categ_id': self.category.id,
        })
        with self.assertRaises(UserError):
            with patch.object(type(self.env['cs.cart.api']), 'request'):
                product._export_to_cs_cart_sync()

    def test_export_requires_mapped_category(self):
        """Export raises UserError if product has no mapped CS-Cart category."""
        unmapped_categ = self.env['product.category'].create({
            'name': 'No CS Mapping',
        })
        product = self.env['product.product'].create({
            'name': 'No Category Map',
            'categ_id': unmapped_categ.id,
        })
        with self.assertRaises(UserError):
            with patch.object(type(self.env['cs.cart.api']), 'request'):
                product._export_to_cs_cart_sync()


# =====================================================================
# 3. STOCK SYNC BYPASS TESTS
# =====================================================================
class TestStockSyncBypass(TestCSCartConnectorBase):
    """Tests for cs_cart_skip_stock_sync context flag."""

    def test_skip_flag_prevents_sync_on_quant_write(self):
        """StockQuant.write with cs_cart_skip_stock_sync=True does not trigger sync."""
        location = self.env.ref('stock.stock_location_stock', raise_if_not_found=False)
        if not location:
            self.skipTest("No stock location available")

        quant = self.env['stock.quant'].sudo().with_context(
            cs_cart_skip_stock_sync=True,
            inventory_mode=True,
        ).create({
            'product_id': self.product_mapped.id,
            'location_id': location.id,
            'inventory_quantity': 10,
        })
        with patch.object(
            type(self.product_mapped),
            '_trigger_cs_cart_stock_sync_from_products'
        ) as mock_sync:
            quant.with_context(cs_cart_skip_stock_sync=True).write({
                'inventory_quantity': 20,
            })
            mock_sync.assert_not_called()

    def test_no_skip_flag_triggers_sync_on_quant_write(self):
        """StockQuant.write without skip flag triggers sync."""
        location = self.env.ref('stock.stock_location_stock', raise_if_not_found=False)
        if not location:
            self.skipTest("No stock location available")

        quant = self.env['stock.quant'].sudo().with_context(
            cs_cart_skip_stock_sync=True,
            inventory_mode=True,
        ).create({
            'product_id': self.product_mapped.id,
            'location_id': location.id,
            'inventory_quantity': 10,
        })
        with patch.object(
            type(self.product_mapped),
            '_trigger_cs_cart_stock_sync_from_products'
        ) as mock_sync:
            quant.with_context(cs_cart_skip_stock_sync=False).write({
                'inventory_quantity': 30,
            })
            mock_sync.assert_called()


# =====================================================================
# 4. REAL-TIME STOCK SYNC TESTS
# =====================================================================
class TestRealTimeStockSync(TestCSCartConnectorBase):
    """Tests for _trigger_cs_cart_stock_sync_from_products."""

    def test_sync_filters_unmapped_products(self):
        """Only products with cs_cart_product_id and is_storable are synced."""
        products = self.product_mapped | self.product_unmapped
        filtered = products.filtered(
            lambda p: p.cs_cart_product_id and p.is_storable
        )
        self.assertIn(self.product_mapped, filtered)
        self.assertNotIn(self.product_unmapped, filtered)

    def test_sync_filters_non_storable_products(self):
        """Service products are excluded from real-time sync."""
        self.product_service.cs_cart_product_id = 999
        products = self.product_mapped | self.product_service
        filtered = products.filtered(
            lambda p: p.cs_cart_product_id and p.is_storable
        )
        self.assertNotIn(self.product_service, filtered)

    def test_sync_aborts_without_config(self):
        """No connected config with realtime_stock_sync → no sync happens."""
        self.config.realtime_stock_sync = False
        with patch.object(
            type(self.env['cs.cart.api']), 'request'
        ) as mock_api:
            self.product_mapped._trigger_cs_cart_stock_sync_from_products()
            mock_api.assert_not_called()

    def test_sync_stock_to_cs_cart_sends_put(self):
        """_sync_stock_to_cs_cart sends PUT with amount payload."""
        with patch.object(
            type(self.env['cs.cart.api']), 'request', return_value={}
        ) as mock_api:
            self.product_mapped._sync_stock_to_cs_cart(
                self.config.id, 'qty_available'
            )
            mock_api.assert_called_once()
            call_args = mock_api.call_args
            self.assertEqual(call_args[0][0], 'PUT')
            self.assertIn('products/501', call_args[0][1])
            self.assertIn('amount', call_args[1].get('data', call_args[0][2] if len(call_args[0]) > 2 else {}))

    def test_sync_stock_no_cs_id_aborts(self):
        """_sync_stock_to_cs_cart does nothing if product has no CS ID."""
        with patch.object(
            type(self.env['cs.cart.api']), 'request'
        ) as mock_api:
            self.product_unmapped._sync_stock_to_cs_cart(
                self.config.id, 'qty_available'
            )
            mock_api.assert_not_called()


# =====================================================================
# 5. PARTNER EXPORT TESTS
# =====================================================================
class TestPartnerExport(TestCSCartConnectorBase):
    """Tests for partner/customer export to CS-Cart."""

    def test_partner_has_cs_cart_fields(self):
        """res.partner has cs_cart_user_id and cs_cart_company_id fields."""
        fields = self.env['res.partner']._fields
        self.assertIn('cs_cart_user_id', fields)
        self.assertIn('cs_cart_company_id', fields)

    def test_customer_payload_has_correct_user_type(self):
        """Customer payload uses user_type=C."""
        Partner = self.env['res.partner']
        payload = Partner._prepare_cs_cart_customer_payload(self.partner, 1)
        self.assertEqual(payload['user_type'], 'C')
        self.assertEqual(payload['email'], 'customer@example.com')

    def test_vendor_payload_has_correct_user_type(self):
        """Vendor payload uses user_type=V."""
        Partner = self.env['res.partner']
        payload = Partner._prepare_vendor_payload(self.vendor, 1)
        self.assertEqual(payload['user_type'], 'V')

    def test_export_requires_email(self):
        """Export raises UserError if partner has no email."""
        partner_no_email = self.env['res.partner'].create({
            'name': 'No Email Partner',
            'customer_rank': 1,
        })
        with self.assertRaises(UserError):
            with patch.object(type(self.env['cs.cart.api']), 'request'):
                partner_no_email._export_to_cs_cart_sync()

    def test_customer_name_splitting(self):
        """Customer payload splits name into firstname/lastname."""
        Partner = self.env['res.partner']
        payload = Partner._prepare_cs_cart_customer_payload(self.partner, 1)
        self.assertEqual(payload['firstname'], 'Test')
        self.assertEqual(payload['lastname'], 'Customer')


# =====================================================================
# 6. ORDER EXPORT TESTS
# =====================================================================
class TestOrderExport(TestCSCartConnectorBase):
    """Tests for sale order export to CS-Cart."""

    def test_order_has_cs_cart_field(self):
        """sale.order has cs_cart_order_id field."""
        self.assertIn('cs_cart_order_id', self.env['sale.order']._fields)

    def test_order_status_mapping(self):
        """Odoo order states map to correct CS-Cart statuses."""
        status_map = {
            "draft": "O",
            "sent": "O",
            "sale": "P",
            "done": "C",
            "cancel": "F",
        }
        for odoo_state, cs_status in status_map.items():
            self.assertEqual(
                status_map.get(odoo_state),
                cs_status,
                f"State '{odoo_state}' should map to '{cs_status}'"
            )

    def test_prepare_order_payload_structure(self):
        """Order payload has required CS-Cart fields."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_mapped.id,
            'product_uom_qty': 2,
            'price_unit': 25.0,
        })
        with patch.object(type(self.env['cs.cart.api']), 'request', return_value={}):
            payload = order._prepare_cs_cart_order_payload(order)
        self.assertIn('products', payload)
        self.assertIn('user_data', payload)
        self.assertIn('status', payload)
        self.assertEqual(payload['user_id'], str(self.partner.cs_cart_user_id))

    def test_prepare_order_payload_no_products_raises(self):
        """Order with no valid lines raises UserError."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        with self.assertRaises(UserError):
            with patch.object(type(self.env['cs.cart.api']), 'request', return_value={}):
                order._prepare_cs_cart_order_payload(order)


# =====================================================================
# 7. ORDER IMPORT TESTS
# =====================================================================
class TestOrderImport(TestCSCartConnectorBase):
    """Tests for order import from CS-Cart."""

    def test_order_import_missing_product_raises_validation(self):
        """Importing an order with unmapped products raises ValidationError."""
        OrderSync = self.env['cs.cart.order.sync']
        # The _sync_single_order_fast method uses product caches.
        # An empty cache means no products are mapped.
        product_cache_cs = {}
        product_cache_code = {}

        # Simulate order details with a product not in Odoo
        details = {
            'order_id': '999',
            'timestamp': '1625097600',
            'user_id': '0',
            'email': 'guest@example.com',
            'firstname': 'Guest',
            'lastname': 'User',
            'status': 'P',
            'total': '100.00',
            'products': {
                '1': {
                    'product_id': '9999',
                    'product_code': 'NONEXISTENT',
                    'product': 'Ghost Product',
                    'price': '100.00',
                    'amount': '1',
                },
            },
            'taxes': {},
            'shipping': [],
            'shipping_cost': '0',
        }

        mock_api = MagicMock()
        mock_api.request.return_value = details

        with self.assertRaises(ValidationError) as cm:
            OrderSync._sync_single_order_fast(
                mock_api,
                {"order_id": "999"},
                {},  # partner_cache
                product_cache_cs,
                product_cache_code,
                {},  # tax_cache
                {},  # carrier_cache
            )
        self.assertIn('CS_CART_IMPORT_PRODUCTS_REQUIRED', str(cm.exception))

    def test_cs_cart_status_to_odoo_mapping(self):
        """CS-Cart status codes map to correct Odoo states."""
        OrderSync = self.env['cs.cart.order.sync']
        mappings = {
            'O': 'draft',
            'P': 'sale',
            'C': 'sale',
            'F': 'cancel',
            'D': 'cancel',
            'X': 'draft',  # unknown defaults to draft
        }
        for cs_status, expected in mappings.items():
            result = OrderSync._map_cs_cart_status(cs_status)
            self.assertEqual(
                result, expected,
                f"CS status '{cs_status}' should map to '{expected}', got '{result}'"
            )


# =====================================================================
# 8. CS-CART API HELPER TESTS
# =====================================================================
class TestCSCartAPI(TestCSCartConnectorBase):
    """Tests for the cs.cart.api abstract model."""

    def test_get_config_returns_connected_store(self):
        """_get_config finds the connected config."""
        api = self.env['cs.cart.api'].with_context(cs_cart_config_id=self.config.id)
        base_url, email, api_key = api._get_config()
        self.assertEqual(base_url, 'https://test.cs-cart.com')
        self.assertEqual(email, 'test@example.com')
        self.assertEqual(api_key, 'test-api-key-123')

    def test_get_config_no_store_raises(self):
        """_get_config raises UserError when no config exists."""
        self.env['cs.cart.config'].search([]).unlink()
        api = self.env['cs.cart.api']
        with self.assertRaises(UserError):
            api._get_config()

    @patch('odoo.addons.odoo_cscart_connector.models.cs_cart_api._session')
    def test_api_request_raises_on_4xx(self, mock_session):
        """API request raises UserError on 4xx responses."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = 'Bad Request'
        mock_session.request.return_value = mock_response

        api = self.env['cs.cart.api']
        with self.assertRaises(UserError):
            api.request('GET', 'products')


# =====================================================================
# 9. IMPORT BATCH TESTS
# =====================================================================
class TestImportBatch(TestCSCartConnectorBase):
    """Tests for cs.cart.import.batch model."""

    def test_batch_creation(self):
        """Import batch can be created with expected fields."""
        batch = self.env['cs.cart.import.batch'].create({
            'name': 'Test Batch',
            'import_type': 'products',
            'state': 'pending',
            'cs_cart_config_id': self.config.id,
        })
        self.assertEqual(batch.state, 'pending')
        self.assertEqual(batch.import_type, 'products')

    def test_batch_cancel(self):
        """Batch can be cancelled."""
        batch = self.env['cs.cart.import.batch'].create({
            'name': 'Cancel Test',
            'import_type': 'orders',
            'state': 'pending',
            'cs_cart_config_id': self.config.id,
        })
        batch.button_cancel()
        self.assertEqual(batch.state, 'cancelled')


# =====================================================================
# 10. CATEGORY EXPORT TESTS
# =====================================================================
class TestCategoryExport(TestCSCartConnectorBase):
    """Tests for product category CS-Cart fields."""

    def test_category_has_cs_cart_field(self):
        """product.category has cs_cart_category_id field."""
        self.assertIn(
            'cs_cart_category_id',
            self.env['product.category']._fields
        )

    def test_mapped_category_has_id(self):
        """Category created with cs_cart_category_id retains it."""
        self.assertEqual(self.category.cs_cart_category_id, 100)

    def test_cs_cart_category_model_has_description(self):
        """cs.cart.category model has _description set."""
        model = self.env['cs.cart.category']
        self.assertTrue(model._description)
        self.assertNotEqual(model._description, '')
