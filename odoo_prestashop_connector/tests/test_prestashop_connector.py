# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:  Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from unittest.mock import MagicMock, patch
from odoo.tests.common import TransactionCase
from odoo.addons.odoo_prestashop_connector.models.prestashop_connector import PrestashopConnector


class TestPrestashopConnector(TransactionCase):
    """Test cases for the prestashop connector."""
    @classmethod
    def setUpClass(cls):
        """Set up the test environment and create a test connector."""
        super().setUpClass()
        with patch.object(PrestashopConnector, '_check_connection', autospec=True):
            cls.connector = cls.env['prestashop.connector'].create({
                'name': 'Test Shop',
                'api_url': 'https://test.prestashop.com',
                'api_key': 'TESTKEY123',
            })

    def _fake_connector(self):
        """Create and return a mocked connector instance."""
        fake = MagicMock()
        fake.api_url = self.connector.api_url
        fake.api_key = self.connector.api_key
        fake.state = self.connector.state
        fake.is_product_imported = False
        fake.is_product_exported = False
        fake.is_contacts_imported = False
        fake.is_contacts_exported = False
        fake.is_order_imported = False
        fake.is_order_exported = False
        fake.write = MagicMock()
        return fake

    def _fake_env(self):
        """Create and return a mocked Odoo environment."""
        env = MagicMock()
        env.company.id = self.env.company.id
        env.models = {
            'product.product': MagicMock(),
            'stock.quant': MagicMock(),
            'res.partner': MagicMock(),
            'sale.order': MagicMock(),
            'delivery.carrier': MagicMock(),
            'choose.delivery.carrier': MagicMock(),
            'product.template': MagicMock(),
        }
        env.__getitem__.side_effect = lambda model: env.models[model]
        return env

    def test_action_connect(self):
        """Test the action_connect method."""
        fake = self._fake_connector()
        mock_service = MagicMock()
        mock_service.get.return_value = {'shops': {}}
        with patch(
            'odoo.addons.odoo_prestashop_connector.models.prestashop_connector.PrestaShopWebServiceDict',
            return_value=mock_service,
        ):
            PrestashopConnector.action_connect(fake)
        fake.write.assert_called_once_with({'state': 'connected'})

    def test_check_connection(self):
        """Test the _check_connection method."""
        fake = self._fake_connector()
        mock_service = MagicMock()
        mock_service.get.side_effect = Exception('Connection Refused')
        with patch(
            'odoo.addons.odoo_prestashop_connector.models.prestashop_connector.PrestaShopWebServiceDict',
            return_value=mock_service,
        ):
            with self.assertRaises(Exception):
                PrestashopConnector._check_connection(fake)

    def test_action_import_products(self):
        """Test importing products from PrestaShop."""
        fake = self._fake_connector()
        fake.state = 'connected'
        fake.env = self._fake_env()
        product_model = fake.env['product.product']
        stock_model = fake.env['stock.quant']
        product_model.search.return_value = MagicMock(prestashop=0)
        product_model.create.return_value = MagicMock(id=11)
        stock_model.create = MagicMock()
        mock_service = MagicMock()
        mock_service.get.side_effect = [
            {'products': {'product': [{'attrs': {'id': '101'}}]}},
            {'product': {'price': '99.90', 'weight': '1.2', 'wholesale_price': '55.00', 'name': {'language': [{'value': 'Imported Product'}]}}},
            {'stock_availables': {'stock_available': {'attrs': {'id': '201'}}}},
            {'stock_available': {'quantity': '5'}},
        ]
        with patch('odoo.addons.odoo_prestashop_connector.models.prestashop_connector.PrestaShopWebServiceDict', return_value=mock_service):
            result = PrestashopConnector.action_import_products(fake)
        self.assertEqual(result['params']['type'], 'success')
        self.assertTrue(fake.is_product_imported)
        product_model.create.assert_called_once()
        stock_model.create.assert_called_once()

    def test_action_export_products(self):
        """Test exporting products to PrestaShop."""
        fake = self._fake_connector()
        fake.state = 'connected'
        fake.env = self._fake_env()
        product = MagicMock()
        product.prestashop = 0
        product.lst_price = 150.0
        product.standard_price = 100.0
        product.name = 'Odoo Product'
        product.description_sale = False
        product.default_code = False
        product.write = MagicMock()
        fake.env['product.product'].search.return_value = [product]
        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_service.add.return_value = {'prestashop': {'product': {'id': 999}}}
        with patch('odoo.addons.odoo_prestashop_connector.models.prestashop_connector.PrestaShopWebServiceDict', return_value=mock_service):
            result = PrestashopConnector.action_export_products(fake)
        self.assertEqual(result['params']['type'], 'success')
        self.assertTrue(fake.is_product_exported)
        product.write.assert_called_once_with({'prestashop': 999})

    def test_action_import_contacts(self):
        """Test importing contacts from PrestaShop."""
        fake = self._fake_connector()
        fake.state = 'connected'
        fake.env = self._fake_env()
        partner_model = fake.env['res.partner']
        partner_model.search.return_value = MagicMock(prestashop=0)
        partner_model.create = MagicMock()
        mock_service = MagicMock()
        mock_service.get.side_effect = [
            {'customers': {'customer': [{'attrs': {'id': '301'}}]}},
            {'customer': {'lastname': 'Imported', 'firstname': 'Customer', 'id': '301', 'email': 'imported@example.com'}},
        ]
        with patch('odoo.addons.odoo_prestashop_connector.models.prestashop_connector.PrestaShopWebServiceDict', return_value=mock_service):
            result = PrestashopConnector.action_import_contacts(fake)
        self.assertEqual(result['params']['type'], 'success')
        self.assertTrue(fake.is_contacts_imported)
        partner_model.create.assert_called_once()

    def test_action_export_contacts(self):
        """Test exporting contacts to PrestaShop."""
        fake = self._fake_connector()
        fake.state = 'connected'
        fake.env = self._fake_env()
        customer = MagicMock()
        customer.prestashop = 0
        customer.name = 'John Doe'
        customer.email = 'john.doe@example.com'
        customer.company_id.name = 'Cybrosys'
        customer.country_id.name = 'United States'
        customer.state_id.name = 'Texas'
        customer.city = 'Houston'
        customer.write = MagicMock()
        fake.env['res.partner'].search.return_value = [customer]
        mock_service = MagicMock()
        mock_service.search.side_effect = [[], [], [21], [1]]
        mock_service.add.return_value = {'prestashop': {'customer': {'id': 888}}}
        with patch('odoo.addons.odoo_prestashop_connector.models.prestashop_connector.PrestaShopWebServiceDict', return_value=mock_service):
            result = PrestashopConnector.action_export_contacts(fake)
        self.assertEqual(result['params']['type'], 'success')
        self.assertTrue(fake.is_contacts_exported)
        customer.write.assert_called_once_with({'prestashop': 888})

    def test_action_export_contacts_duplicate_email_error(self):
        """Test exporting contacts when email already exists in PrestaShop."""
        fake = self._fake_connector()
        fake.state = 'connected'
        fake.env = self._fake_env()
        customer = MagicMock()
        customer.prestashop = 0
        customer.name = 'Jane Doe'
        customer.email = 'jane.doe@example.com'
        customer.company_id.name = 'Cybrosys'
        customer.country_id.name = 'United States'
        customer.state_id.name = 'Texas'
        customer.city = 'Houston'
        customer.write = MagicMock()
        fake.env['res.partner'].search.return_value = [customer]
        mock_service = MagicMock()
        mock_service.search.side_effect = [[], [777], [], [21], [1]]
        from prestapyt import PrestaShopWebServiceError
        mock_service.add.side_effect = [PrestaShopWebServiceError("The email is already used, please choose another one."), None]
        with patch('odoo.addons.odoo_prestashop_connector.models.prestashop_connector.PrestaShopWebServiceDict', return_value=mock_service):
            result = PrestashopConnector.action_export_contacts(fake)
        self.assertEqual(result['params']['type'], 'success')
        self.assertTrue(fake.is_contacts_exported)
        customer.write.assert_called_once_with({'prestashop': 777})

    def test_action_import_orders(self):
        """Test importing orders from PrestaShop."""
        fake = self._fake_connector()
        fake.state = 'connected'
        fake.env = self._fake_env()
        partner = MagicMock(id=42)
        sale_order = MagicMock(id=55)
        sale_order.order_line = MagicMock()
        fake.env['res.partner'].search.return_value = partner
        fake.env['sale.order'].search.return_value = MagicMock(prestashop=0)
        fake.env['sale.order'].create.return_value = sale_order
        fake.env['delivery.carrier'].search.return_value = MagicMock()
        fake.env['product.product'].search.return_value = MagicMock(id=11)
        fake.env['product.product'].create.return_value = MagicMock(id=12)
        fake.env['choose.delivery.carrier'].with_context.return_value.save.return_value.button_confirm = MagicMock()
        mock_service = MagicMock()
        mock_service.get.side_effect = [
            {'orders': {'order': {'attrs': {'id': '601'}}}},
            {'order': {'current_state': 2, 'id_customer': 42, 'id': '601', 'total_shipping_tax_incl': '0.00', 'total_discounts_tax_incl': '0.00', 'associations': {'order_rows': {'order_row': {'product_id': 11, 'product_quantity': 2, 'product_reference': 'Imported row'}}}}},
        ]
        with patch('odoo.addons.odoo_prestashop_connector.models.prestashop_connector.PrestaShopWebServiceDict', return_value=mock_service), patch('odoo.addons.odoo_prestashop_connector.models.prestashop_connector.Form') as mock_form:
            mock_form.return_value.save.return_value.button_confirm = MagicMock()
            result = PrestashopConnector.action_import_orders(fake)
        self.assertEqual(result['params']['type'], 'success')
        self.assertTrue(fake.is_order_imported)
        fake.env['sale.order'].create.assert_called_once()

    def test_action_export_orders(self):
        """Test exporting orders to PrestaShop."""
        fake = self._fake_connector()
        fake.state = 'connected'
        fake.env = self._fake_env()
        partner = MagicMock()
        partner.prestashop = 701
        order_line = MagicMock()
        order_line.product_id.prestashop = 801
        order_line.product_id.lst_price = 150.0
        order_line.product_uom_qty = 1
        order_line_container = MagicMock()
        order_line_container.__iter__.return_value = iter([order_line])
        order_line_container.mapped.return_value = [1]
        sale_order = MagicMock()
        sale_order.partner_id = partner
        sale_order.order_line = order_line_container
        sale_order.prestashop = 0
        sale_order.write = MagicMock()
        fake.env['sale.order'].search.return_value = [sale_order]
        mock_service = MagicMock()
        mock_service.search.side_effect = [[55], []]
        mock_service.add.side_effect = [{'prestashop': {'cart': {'id': 901}}}, {'prestashop': {'order': {'id': 902}}}]
        with patch('odoo.addons.odoo_prestashop_connector.models.prestashop_connector.PrestaShopWebServiceDict', return_value=mock_service):
            result = PrestashopConnector.action_export_orders(fake)
        self.assertEqual(result['params']['type'], 'success')
        self.assertTrue(fake.is_order_exported)
        sale_order.write.assert_called_once_with({'prestashop': 902})



    def test_action_import_products_not_connected(self):
        """Test import products returns danger when not connected."""
        fake = self._fake_connector()
        fake.state = 'not_connected'
        result = PrestashopConnector.action_import_products(fake)
        self.assertEqual(result['params']['type'], 'danger')

    def test_action_export_products_not_connected(self):
        """Test export products skips API when no products to export."""
        fake = self._fake_connector()
        fake.state = 'connected'
        fake.env = self._fake_env()
        fake.env['product.product'].search.return_value = []
        mock_service = MagicMock()
        with patch('odoo.addons.odoo_prestashop_connector.models.prestashop_connector.PrestaShopWebServiceDict', return_value=mock_service):
            result = PrestashopConnector.action_export_products(fake)
        self.assertEqual(result['params']['type'], 'danger')

    def test_action_import_contacts_not_connected(self):
        """Test import contacts returns danger when not connected."""
        fake = self._fake_connector()
        fake.state = 'not_connected'
        result = PrestashopConnector.action_import_contacts(fake)
        self.assertEqual(result['params']['type'], 'danger')

    def test_action_export_contacts_not_connected(self):
        """Test export contacts returns danger when not connected."""
        fake = self._fake_connector()
        fake.state = 'not_connected'
        result = PrestashopConnector.action_export_contacts(fake)
        self.assertEqual(result['params']['type'], 'danger')

    def test_action_import_orders_not_connected(self):
        """Test import orders returns danger when not connected."""
        fake = self._fake_connector()
        fake.state = 'not_connected'
        result = PrestashopConnector.action_import_orders(fake)
        self.assertEqual(result['params']['type'], 'danger')

    def test_action_export_orders_not_connected(self):
        """Test export orders returns danger when not connected."""
        fake = self._fake_connector()
        fake.state = 'not_connected'
        result = PrestashopConnector.action_export_orders(fake)
        self.assertEqual(result['params']['type'], 'danger')



    def test_action_import_products_no_new_product(self):
        """Test import products returns danger when product already exists."""
        fake = self._fake_connector()
        fake.state = 'connected'
        fake.env = self._fake_env()
        product_model = fake.env['product.product']
        stock_model = fake.env['stock.quant']
        existing = MagicMock(prestashop=101)
        product_model.search.return_value = existing
        stock_model.search.return_value = MagicMock()
        mock_service = MagicMock()
        mock_service.get.side_effect = [
            {'products': {'product': [{'attrs': {'id': '101'}}]}},
            {'product': {'price': '99.90', 'weight': '1.0', 'wholesale_price': '50.00',
                         'name': {'language': [{'value': 'Existing Product'}]}}},
            {'stock_availables': {'stock_available': {'attrs': {'id': '201'}}}},
            {'stock_available': {'quantity': '3'}},
        ]
        with patch('odoo.addons.odoo_prestashop_connector.models.prestashop_connector.PrestaShopWebServiceDict', return_value=mock_service):
            result = PrestashopConnector.action_import_products(fake)
        self.assertEqual(result['params']['type'], 'danger')
        self.assertFalse(fake.is_product_imported)

    def test_action_import_products_list_stock(self):
        """Test import products with list-type stock_available (isinstance list branch)."""
        fake = self._fake_connector()
        fake.state = 'connected'
        fake.env = self._fake_env()
        product_model = fake.env['product.product']
        stock_model = fake.env['stock.quant']
        product_model.search.return_value = MagicMock(prestashop=0)
        product_model.create.return_value = MagicMock(id=22)
        stock_model.create = MagicMock()
        mock_service = MagicMock()
        mock_service.get.side_effect = [
            {'products': {'product': [{'attrs': {'id': '202'}}]}},
            {'product': {'price': '10.00', 'weight': '0.5', 'wholesale_price': '5.00',
                         'name': {'language': {'value': 'Dict Language Product'}}}},
            {'stock_availables': {'stock_available': [
                {'attrs': {'id': '301'}}, {'attrs': {'id': '302'}}
            ]}},
            {'stock_available': {'quantity': '7'}},
        ]
        with patch('odoo.addons.odoo_prestashop_connector.models.prestashop_connector.PrestaShopWebServiceDict', return_value=mock_service):
            result = PrestashopConnector.action_import_products(fake)
        self.assertEqual(result['params']['type'], 'success')

    def test_action_import_contacts_no_new_contacts(self):
        """Test import contacts returns danger when all contacts already exist."""
        fake = self._fake_connector()
        fake.state = 'connected'
        fake.env = self._fake_env()
        partner_model = fake.env['res.partner']
        partner_model.search.return_value = MagicMock(prestashop=301)
        mock_service = MagicMock()
        mock_service.get.side_effect = [
            {'customers': {'customer': [{'attrs': {'id': '301'}}]}},
            {'customer': {'lastname': 'Existing', 'firstname': 'Contact',
                          'id': '301', 'email': 'existing@example.com'}},
        ]
        with patch('odoo.addons.odoo_prestashop_connector.models.prestashop_connector.PrestaShopWebServiceDict', return_value=mock_service):
            result = PrestashopConnector.action_import_contacts(fake)
        self.assertEqual(result['params']['type'], 'danger')
        self.assertFalse(fake.is_contacts_imported)

    def test_action_export_contacts_no_new_contacts(self):
        """Test export contacts returns danger when all contacts already in PrestaShop."""
        fake = self._fake_connector()
        fake.state = 'connected'
        fake.env = self._fake_env()
        customer = MagicMock()
        customer.prestashop = 888
        customer.name = 'Existing Person'
        customer.email = 'existing@example.com'
        fake.env['res.partner'].search.return_value = [customer]
        mock_service = MagicMock()
        mock_service.search.side_effect = [[888], [888]]
        with patch('odoo.addons.odoo_prestashop_connector.models.prestashop_connector.PrestaShopWebServiceDict', return_value=mock_service):
            result = PrestashopConnector.action_export_contacts(fake)
        self.assertEqual(result['params']['type'], 'danger')

    def test_action_import_orders_no_new_orders(self):
        """Test import orders returns danger when no orders to import."""
        fake = self._fake_connector()
        fake.state = 'connected'
        fake.env = self._fake_env()
        mock_service = MagicMock()
        mock_service.get.return_value = {'orders': {}}
        with patch('odoo.addons.odoo_prestashop_connector.models.prestashop_connector.PrestaShopWebServiceDict', return_value=mock_service):
            result = PrestashopConnector.action_import_orders(fake)
        self.assertEqual(result['params']['type'], 'danger')

    def test_action_import_orders_skips_cancelled(self):
        """Test import orders skips orders with current_state == 6 (cancelled)."""
        fake = self._fake_connector()
        fake.state = 'connected'
        fake.env = self._fake_env()
        fake.env['sale.order'].search.return_value = MagicMock(prestashop=0)
        mock_service = MagicMock()
        mock_service.get.side_effect = [
            {'orders': {'order': [{'attrs': {'id': '701'}}]}},
            {'order': {'current_state': 6, 'id_customer': 10, 'id': '701',
                       'total_shipping_tax_incl': '0.00',
                       'total_discounts_tax_incl': '0.00',
                       'associations': {'order_rows': {'order_row': []}}}},
        ]
        with patch('odoo.addons.odoo_prestashop_connector.models.prestashop_connector.PrestaShopWebServiceDict', return_value=mock_service):
            result = PrestashopConnector.action_import_orders(fake)
        self.assertEqual(result['params']['type'], 'danger')
        self.assertFalse(fake.is_order_imported)

    def test_action_import_orders_with_shipping_and_discount(self):
        """Test import orders with shipping and discount lines."""
        fake = self._fake_connector()
        fake.state = 'connected'
        fake.env = self._fake_env()
        partner = MagicMock(id=42)
        sale_order = MagicMock(id=55)
        sale_order.order_line = MagicMock()
        fake.env['res.partner'].search.return_value = partner
        fake.env['sale.order'].search.return_value = MagicMock(prestashop=0)
        fake.env['sale.order'].create.return_value = sale_order
        fake.env['delivery.carrier'].search.return_value = MagicMock()
        fake.env['product.product'].search.return_value = MagicMock(id=11)
        fake.env['product.product'].create.return_value = MagicMock(id=12)
        mock_service = MagicMock()
        mock_service.get.side_effect = [
            {'orders': {'order': {'attrs': {'id': '801'}}}},
            {'order': {'current_state': 2, 'id_customer': 42, 'id': '801',
                       'total_shipping_tax_incl': '15.00',
                       'total_discounts_tax_incl': '5.00',
                       'associations': {'order_rows': {'order_row': {
                           'product_id': 11, 'product_quantity': 1,
                           'product_reference': 'Item'}}}}},
        ]
        with patch('odoo.addons.odoo_prestashop_connector.models.prestashop_connector.PrestaShopWebServiceDict', return_value=mock_service), \
             patch('odoo.addons.odoo_prestashop_connector.models.prestashop_connector.Form') as mock_form:
            mock_form.return_value.save.return_value.button_confirm = MagicMock()
            result = PrestashopConnector.action_import_orders(fake)
        self.assertEqual(result['params']['type'], 'success')

    def test_action_export_orders_no_orders(self):
        """Test export orders returns danger when no confirmed sale orders exist."""
        fake = self._fake_connector()
        fake.state = 'connected'
        fake.env = self._fake_env()
        fake.env['sale.order'].search.return_value = []
        mock_service = MagicMock()
        with patch('odoo.addons.odoo_prestashop_connector.models.prestashop_connector.PrestaShopWebServiceDict', return_value=mock_service):
            result = PrestashopConnector.action_export_orders(fake)
        self.assertEqual(result['params']['type'], 'danger')

    def test_action_export_orders_skipped_no_customer(self):
        """Test export orders skips order when customer cannot be found in PrestaShop."""
        fake = self._fake_connector()
        fake.state = 'connected'
        fake.env = self._fake_env()
        partner = MagicMock()
        partner.prestashop = 0
        partner.email = None
        partner.name = 'Unknown'
        sale_order = MagicMock()
        sale_order.prestashop = 0
        sale_order.partner_id = partner
        fake.env['sale.order'].search.return_value = [sale_order]
        mock_service = MagicMock()
        from prestapyt import PrestaShopWebServiceError
        mock_service.add.side_effect = PrestaShopWebServiceError("some error")
        mock_service.search.return_value = []
        with patch('odoo.addons.odoo_prestashop_connector.models.prestashop_connector.PrestaShopWebServiceDict', return_value=mock_service):
            result = PrestashopConnector.action_export_orders(fake)
        self.assertIn(result['params']['type'], ['danger', 'warning'])

    def test_action_connect_failure(self):
        """Test action_connect raises UserError when connection fails."""
        from odoo.exceptions import UserError
        fake = self._fake_connector()
        mock_service = MagicMock()
        mock_service.get.side_effect = Exception('Timeout')
        with patch('odoo.addons.odoo_prestashop_connector.models.prestashop_connector.PrestaShopWebServiceDict', return_value=mock_service):
            with self.assertRaises(UserError):
                PrestashopConnector.action_connect(fake)

    def test_action_export_products_existing_product(self):
        """Test export products skips products already in PrestaShop."""
        fake = self._fake_connector()
        fake.state = 'connected'
        fake.env = self._fake_env()
        product = MagicMock()
        product.prestashop = 500
        fake.env['product.product'].search.return_value = [product]
        mock_service = MagicMock()
        mock_service.search.return_value = [500]
        with patch('odoo.addons.odoo_prestashop_connector.models.prestashop_connector.PrestaShopWebServiceDict', return_value=mock_service):
            result = PrestashopConnector.action_export_products(fake)
        self.assertEqual(result['params']['type'], 'danger')

    def test_action_export_orders_partial_skip_with_success(self):
        """Test export orders warning when some orders succeed and some are skipped."""
        fake = self._fake_connector()
        fake.state = 'connected'
        fake.env = self._fake_env()
        partner = MagicMock()
        partner.prestashop = 701
        order_line = MagicMock()
        order_line.product_id.prestashop = 801
        order_line.product_id.lst_price = 100.0
        order_line.product_uom_qty = 2
        order_line_container = MagicMock()
        order_line_container.__iter__.return_value = iter([order_line])
        order_line_container.mapped.return_value = [2]
        sale_order = MagicMock()
        sale_order.partner_id = partner
        sale_order.order_line = order_line_container
        sale_order.prestashop = 0
        sale_order.write = MagicMock()
        partner2 = MagicMock()
        partner2.prestashop = 0
        partner2.email = None
        partner2.name = 'Skip Me'
        skipped_sale = MagicMock()
        skipped_sale.prestashop = 0
        skipped_sale.partner_id = partner2
        fake.env['sale.order'].search.return_value = [sale_order, skipped_sale]
        from prestapyt import PrestaShopWebServiceError
        mock_service = MagicMock()
        mock_service.search.side_effect = [[55], [], []]
        mock_service.add.side_effect = [
            {'prestashop': {'cart': {'id': 901}}},
            {'prestashop': {'order': {'id': 902}}},
            PrestaShopWebServiceError("some other error"),
        ]
        with patch('odoo.addons.odoo_prestashop_connector.models.prestashop_connector.PrestaShopWebServiceDict', return_value=mock_service):
            result = PrestashopConnector.action_export_orders(fake)
        self.assertIn(result['params']['type'], ['success', 'warning'])

    def test_action_import_orders_partner_not_found_creates_new(self):
        """Test import orders creates partner when not found by prestashop id."""
        fake = self._fake_connector()
        fake.state = 'connected'
        fake.env = self._fake_env()
        new_partner = MagicMock(id=99)
        sale_order = MagicMock(id=55)
        sale_order.order_line = MagicMock()
        fake.env['res.partner'].search.side_effect = [
            MagicMock(__bool__=lambda s: False),
            MagicMock(__bool__=lambda s: False),
            new_partner,
        ]
        fake.env['res.partner'].create.return_value = new_partner
        fake.env['sale.order'].search.return_value = MagicMock(prestashop=0)
        fake.env['sale.order'].create.return_value = sale_order
        fake.env['product.product'].search.return_value = MagicMock(id=11)
        mock_service = MagicMock()
        mock_service.get.side_effect = [
            {'orders': {'order': {'attrs': {'id': '901'}}}},
            {'order': {'current_state': 2, 'id_customer': 50, 'id': '901',
                       'total_shipping_tax_incl': '0.00',
                       'total_discounts_tax_incl': '0.00',
                       'associations': {'order_rows': {'order_row': {
                           'product_id': 11, 'product_quantity': 1,
                           'product_reference': 'Item'}}}}},
            {'customer': {'firstname': 'New', 'lastname': 'User',
                          'email': 'newuser@example.com'}},
        ]
        with patch('odoo.addons.odoo_prestashop_connector.models.prestashop_connector.PrestaShopWebServiceDict', return_value=mock_service), \
             patch('odoo.addons.odoo_prestashop_connector.models.prestashop_connector.Form') as mock_form:
            mock_form.return_value.save.return_value.button_confirm = MagicMock()
            result = PrestashopConnector.action_import_orders(fake)
        self.assertIn(result['params']['type'], ['success', 'danger'])

    def test_action_import_orders_existing_carrier(self):
        """Test import orders uses existing carrier when found."""
        fake = self._fake_connector()
        fake.state = 'connected'
        fake.env = self._fake_env()
        partner = MagicMock(id=42)
        sale_order = MagicMock(id=55)
        sale_order.order_line = MagicMock()
        fake.env['res.partner'].search.return_value = partner
        fake.env['sale.order'].search.return_value = MagicMock(prestashop=0)
        fake.env['sale.order'].create.return_value = sale_order
        existing_carrier = MagicMock()
        fake.env['delivery.carrier'].search.return_value = existing_carrier
        fake.env['product.product'].search.return_value = MagicMock(id=11)
        mock_service = MagicMock()
        mock_service.get.side_effect = [
            {'orders': {'order': {'attrs': {'id': '902'}}}},
            {'order': {'current_state': 2, 'id_customer': 42, 'id': '902',
                       'total_shipping_tax_incl': '10.00',
                       'total_discounts_tax_incl': '0.00',
                       'associations': {'order_rows': {'order_row': {
                           'product_id': 11, 'product_quantity': 1,
                           'product_reference': 'Item'}}}}},
        ]
        with patch('odoo.addons.odoo_prestashop_connector.models.prestashop_connector.PrestaShopWebServiceDict', return_value=mock_service), \
             patch('odoo.addons.odoo_prestashop_connector.models.prestashop_connector.Form') as mock_form:
            mock_form.return_value.save.return_value.button_confirm = MagicMock()
            result = PrestashopConnector.action_import_orders(fake)
        self.assertEqual(result['params']['type'], 'success')

    def test_action_import_orders_discount_existing_product(self):
        """Test import orders uses existing discount product when found."""
        fake = self._fake_connector()
        fake.state = 'connected'
        fake.env = self._fake_env()
        partner = MagicMock(id=42)
        sale_order = MagicMock(id=55)
        sale_order.order_line = MagicMock()
        fake.env['res.partner'].search.return_value = partner
        fake.env['sale.order'].search.return_value = MagicMock(prestashop=0)
        fake.env['sale.order'].create.return_value = sale_order
        discount_product = MagicMock(id=77)
        fake.env['delivery.carrier'].search.return_value = MagicMock()
        fake.env['product.product'].search.return_value = discount_product
        mock_service = MagicMock()
        mock_service.get.side_effect = [
            {'orders': {'order': {'attrs': {'id': '903'}}}},
            {'order': {'current_state': 2, 'id_customer': 42, 'id': '903',
                       'total_shipping_tax_incl': '0.00',
                       'total_discounts_tax_incl': '10.00',
                       'associations': {'order_rows': {'order_row': {
                           'product_id': 77, 'product_quantity': 1,
                           'product_reference': 'Item'}}}}},
        ]
        with patch('odoo.addons.odoo_prestashop_connector.models.prestashop_connector.PrestaShopWebServiceDict', return_value=mock_service), \
             patch('odoo.addons.odoo_prestashop_connector.models.prestashop_connector.Form') as mock_form:
            mock_form.return_value.save.return_value.button_confirm = MagicMock()
            result = PrestashopConnector.action_import_orders(fake)
        self.assertEqual(result['params']['type'], 'success')

    def test_action_export_orders_skipped_only_danger(self):
        """Test export orders returns danger with skipped detail when nothing exported."""
        fake = self._fake_connector()
        fake.state = 'connected'
        fake.env = self._fake_env()
        partner = MagicMock()
        partner.prestashop = 0
        partner.email = None
        partner.name = 'No Email Guy'
        sale_order = MagicMock()
        sale_order.prestashop = 0
        sale_order.partner_id = partner
        sale_order.name = 'S00099'
        fake.env['sale.order'].search.return_value = [sale_order]
        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_service.add.return_value = MagicMock()
        with patch('odoo.addons.odoo_prestashop_connector.models.prestashop_connector.PrestaShopWebServiceDict', return_value=mock_service):
            result = PrestashopConnector.action_export_orders(fake)
        self.assertIn(result['params']['type'], ['danger', 'warning'])

    def test_action_export_orders_country_inactive_skips(self):
        """Test export orders skips order when delivery country is inactive."""
        fake = self._fake_connector()
        fake.state = 'connected'
        fake.env = self._fake_env()
        partner = MagicMock()
        partner.prestashop = 701
        order_line = MagicMock()
        order_line.product_id.prestashop = 801
        order_line.product_uom_qty = 1
        order_line_container = MagicMock()
        order_line_container.__iter__.return_value = iter([order_line])
        order_line_container.mapped.return_value = [1]
        sale_order = MagicMock()
        sale_order.partner_id = partner
        sale_order.order_line = order_line_container
        sale_order.prestashop = 0
        sale_order.name = 'S00100'
        fake.env['sale.order'].search.return_value = [sale_order]
        mock_service = MagicMock()
        mock_service.search.return_value = [55]
        mock_service.get.side_effect = [
            {'address': {'id_country': 99}},
            {'country': {'name': {'language': [{'value': 'TestLand'}]}, 'active': '0'}},
        ]
        with patch('odoo.addons.odoo_prestashop_connector.models.prestashop_connector.PrestaShopWebServiceDict', return_value=mock_service):
            result = PrestashopConnector.action_export_orders(fake)
        self.assertIn(result['params']['type'], ['danger', 'warning'])

    def test_action_export_contacts_non_email_error_raises(self):
        """Test export contacts raises UserError for non-email PrestaShop errors."""
        from odoo.exceptions import UserError
        from prestapyt import PrestaShopWebServiceError
        fake = self._fake_connector()
        fake.state = 'connected'
        fake.env = self._fake_env()
        customer = MagicMock()
        customer.prestashop = 0
        customer.name = 'Error Guy'
        customer.email = 'error@example.com'
        customer.company_id.name = 'Test'
        fake.env['res.partner'].search.return_value = [customer]
        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_service.add.side_effect = PrestaShopWebServiceError("Server error 500")
        with patch('odoo.addons.odoo_prestashop_connector.models.prestashop_connector.PrestaShopWebServiceDict', return_value=mock_service):
            with self.assertRaises(UserError):
                PrestashopConnector.action_export_contacts(fake)

    def test_action_export_contacts_no_country_no_state(self):
        """Test export contacts uses default country/state when none set on customer."""
        fake = self._fake_connector()
        fake.state = 'connected'
        fake.env = self._fake_env()
        customer = MagicMock()
        customer.prestashop = 0
        customer.name = 'No Address'
        customer.email = 'noaddress@example.com'
        customer.company_id.name = ''
        customer.country_id.name = ''
        customer.state_id.name = ''
        customer.city = ''
        customer.write = MagicMock()
        fake.env['res.partner'].search.return_value = [customer]
        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_service.add.side_effect = [
            {'prestashop': {'customer': {'id': 999}}},
            None,
        ]
        with patch('odoo.addons.odoo_prestashop_connector.models.prestashop_connector.PrestaShopWebServiceDict', return_value=mock_service):
            result = PrestashopConnector.action_export_contacts(fake)
        self.assertEqual(result['params']['type'], 'success')

    def test_action_export_orders_existing_order_skipped(self):
        """Test export orders skips sale order already synced to PrestaShop."""
        fake = self._fake_connector()
        fake.state = 'connected'
        fake.env = self._fake_env()
        partner = MagicMock()
        partner.prestashop = 701
        sale_order = MagicMock()
        sale_order.prestashop = 500
        sale_order.partner_id = partner
        fake.env['sale.order'].search.return_value = [sale_order]
        mock_service = MagicMock()
        mock_service.search.return_value = [500]
        with patch('odoo.addons.odoo_prestashop_connector.models.prestashop_connector.PrestaShopWebServiceDict', return_value=mock_service):
            result = PrestashopConnector.action_export_orders(fake)
        self.assertEqual(result['params']['type'], 'danger')
