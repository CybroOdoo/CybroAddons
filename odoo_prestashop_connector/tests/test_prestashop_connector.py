# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
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
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with patch.object(PrestashopConnector, 'check_connection', autospec=True):
            cls.connector = cls.env['prestashop.connector'].create({
                'name': 'Test Shop',
                'api_url': 'https://test.prestashop.com',
                'api_key': 'TESTKEY123',
            })

    def _fake_connector(self):
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
        fake = self._fake_connector()
        mock_service = MagicMock()
        mock_service.get.side_effect = Exception('Connection Refused')
        with patch(
            'odoo.addons.odoo_prestashop_connector.models.prestashop_connector.PrestaShopWebServiceDict',
            return_value=mock_service,
        ):
            with self.assertRaises(Exception):
                PrestashopConnector.check_connection(fake)

    def test_action_import_products(self):
        fake = self._fake_connector(); fake.state = 'connected'; fake.env = self._fake_env()
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
        fake = self._fake_connector(); fake.state = 'connected'; fake.env = self._fake_env()
        product = MagicMock(); product.prestashop = 0; product.lst_price = 150.0; product.standard_price = 100.0
        product.name = 'Odoo Product'; product.description_sale = False; product.default_code = False; product.write = MagicMock()
        fake.env['product.product'].search.return_value = [product]
        mock_service = MagicMock(); mock_service.search.return_value = []; mock_service.add.return_value = {'prestashop': {'product': {'id': 999}}}
        with patch('odoo.addons.odoo_prestashop_connector.models.prestashop_connector.PrestaShopWebServiceDict', return_value=mock_service):
            result = PrestashopConnector.action_export_products(fake)
        self.assertEqual(result['params']['type'], 'success')
        self.assertTrue(fake.is_product_exported)
        product.write.assert_called_once_with({'prestashop': 999})

    def test_action_import_contacts(self):
        fake = self._fake_connector(); fake.state = 'connected'; fake.env = self._fake_env()
        partner_model = fake.env['res.partner']
        partner_model.search.return_value = MagicMock(prestashop=0)
        partner_model.create = MagicMock()
        mock_service = MagicMock(); mock_service.get.side_effect = [
            {'customers': {'customer': [{'attrs': {'id': '301'}}]}},
            {'customer': {'lastname': 'Imported', 'firstname': 'Customer', 'id': '301', 'email': 'imported@example.com'}},
        ]
        with patch('odoo.addons.odoo_prestashop_connector.models.prestashop_connector.PrestaShopWebServiceDict', return_value=mock_service):
            result = PrestashopConnector.action_import_contacts(fake)
        self.assertEqual(result['params']['type'], 'success')
        self.assertTrue(fake.is_contacts_imported)
        partner_model.create.assert_called_once()

    def test_action_export_contacts(self):
        fake = self._fake_connector(); fake.state = 'connected'; fake.env = self._fake_env()
        customer = MagicMock(); customer.prestashop = 0; customer.name = 'John Doe'; customer.email = 'john.doe@example.com'
        customer.company_id.name = 'Cybrosys'; customer.country_id.name = 'United States'; customer.state_id.name = 'Texas'; customer.city = 'Houston'; customer.write = MagicMock()
        fake.env['res.partner'].search.return_value = [customer]
        mock_service = MagicMock(); mock_service.search.side_effect = [[], [21], [1]]; mock_service.add.return_value = {'prestashop': {'customer': {'id': 888}}}
        with patch('odoo.addons.odoo_prestashop_connector.models.prestashop_connector.PrestaShopWebServiceDict', return_value=mock_service):
            result = PrestashopConnector.action_export_contacts(fake)
        self.assertEqual(result['params']['type'], 'success')
        self.assertTrue(fake.is_contacts_exported)
        customer.write.assert_called_once_with({'prestashop': 888})

    def test_action_import_orders(self):
        fake = self._fake_connector(); fake.state = 'connected'; fake.env = self._fake_env()
        partner = MagicMock(id=42); sale_order = MagicMock(id=55); sale_order.order_line = MagicMock()
        fake.env['res.partner'].search.return_value = partner
        fake.env['sale.order'].search.return_value = MagicMock(prestashop=0)
        fake.env['sale.order'].create.return_value = sale_order
        fake.env['delivery.carrier'].search.return_value = MagicMock()
        fake.env['product.product'].search.return_value = MagicMock(id=11)
        fake.env['product.product'].create.return_value = MagicMock(id=12)
        fake.env['choose.delivery.carrier'].with_context.return_value.save.return_value.button_confirm = MagicMock()
        mock_service = MagicMock(); mock_service.get.side_effect = [
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
        fake = self._fake_connector(); fake.state = 'connected'; fake.env = self._fake_env()
        partner = MagicMock(); partner.prestashop = 701
        order_line = MagicMock(); order_line.product_id.prestashop = 801; order_line.product_id.lst_price = 150.0; order_line.product_uom_qty = 1
        order_line_container = MagicMock()
        order_line_container.__iter__.return_value = iter([order_line])
        order_line_container.mapped.return_value = [1]
        sale_order = MagicMock(); sale_order.partner_id = partner; sale_order.order_line = order_line_container; sale_order.prestashop = 0; sale_order.write = MagicMock()
        fake.env['sale.order'].search.return_value = [sale_order]
        mock_service = MagicMock(); mock_service.search.side_effect = [[55], []]; mock_service.add.side_effect = [{'prestashop': {'cart': {'id': 901}}}, {'prestashop': {'order': {'id': 902}}}]
        with patch('odoo.addons.odoo_prestashop_connector.models.prestashop_connector.PrestaShopWebServiceDict', return_value=mock_service):
            result = PrestashopConnector.action_export_orders(fake)
        self.assertEqual(result['params']['type'], 'success')
        self.assertTrue(fake.is_order_exported)
        sale_order.write.assert_called_once_with({'prestashop': 902})
