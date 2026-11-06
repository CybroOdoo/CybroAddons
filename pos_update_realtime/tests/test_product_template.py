# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies(odoo@cybrosys.com)
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
from types import SimpleNamespace
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestProductTemplate(TransactionCase):
    """Test cases for real-time POS product notifications."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_model = cls.env['product.template']
        cls.pos_session_model = cls.env['pos.session']
        cls.bus_model = cls.env['bus.bus']

    def _create_product(self, available_in_pos=True):
        """Create a product for testing."""
        return self.product_model.create({
            'name': 'Test POS Product',
            'available_in_pos': available_in_pos,
            'list_price': 100.0,
        })

    def _mock_sessions(self):
        """Return mock POS sessions."""
        return [
            SimpleNamespace(id=10),
            SimpleNamespace(id=20),
        ]

    def test_create_product_without_pos_session(self):
        """Test product creation without an active POS session."""
        with patch.object(
            type(self.pos_session_model),
            'search',
            return_value=self.pos_session_model.browse(),
        ), patch.object(
            type(self.bus_model), '_sendone'
        ) as sendone:
            product = self._create_product()

            self.assertTrue(product)
            self.assertEqual(product.name, 'Test POS Product')
            sendone.assert_not_called()

    def test_create_product_with_pos_session(self):
        """Test bus notification when a POS product is created."""
        with patch.object(
            type(self.pos_session_model),
            'search',
            return_value=self._mock_sessions(),
        ), patch.object(
            type(self.bus_model), '_sendone'
        ) as sendone:
            product = self._create_product()

            self.assertTrue(product)
            self.assertEqual(sendone.call_count, 2)

            notification = sendone.call_args_list[0].args

            self.assertEqual(notification[0], '10')
            self.assertEqual(notification[1], 'product_update')
            self.assertEqual(
                notification[2]['product_id'],
                product.product_variant_id.id
            )
            self.assertEqual(
                notification[2]['name'],
                product.product_variant_id.display_name
            )

    def test_create_product_not_available_in_pos(self):
        """Test that unavailable products do not trigger notifications."""
        with patch.object(
            type(self.pos_session_model),
            'search',
            return_value=self._mock_sessions(),
        ), patch.object(
            type(self.bus_model), '_sendone'
        ) as sendone:
            product = self._create_product(available_in_pos=False)

            self.assertTrue(product)
            sendone.assert_not_called()

    def test_write_product_with_pos_session(self):
        """Test bus notification when an existing POS product is updated."""
        product = self._create_product()

        with patch.object(
            type(self.pos_session_model),
            'search',
            return_value=self._mock_sessions(),
        ), patch.object(
            type(self.bus_model), '_sendone'
        ) as sendone:
            product.write({
                'list_price': 200.0,
            })

            self.assertEqual(sendone.call_count, 2)

            notification = sendone.call_args_list[0].args

            self.assertEqual(notification[0], '10')
            self.assertEqual(notification[1], 'product_update')
            self.assertEqual(
                notification[2]['list_price'],
                200.0
            )

    def test_write_product_not_available_in_pos(self):
        """Test updating a product unavailable in POS."""
        product = self._create_product(available_in_pos=False)

        with patch.object(
            type(self.pos_session_model),
            'search',
            return_value=self._mock_sessions(),
        ), patch.object(
            type(self.bus_model), '_sendone'
        ) as sendone:
            product.write({
                'list_price': 150.0,
            })

            sendone.assert_not_called()

    def test_notify_product_change(self):
        """Test notification data sent to multiple POS sessions."""
        product = self._create_product()

        sessions = self._mock_sessions()

        with patch.object(
            type(self.bus_model), '_sendone'
        ) as sendone:
            product._notify_pos_product_change(
                product.product_variant_id,
                sessions
            )

            self.assertEqual(sendone.call_count, 2)

            for call in sendone.call_args_list:
                channel, notification_type, notification_data = call.args

                self.assertEqual(notification_type, 'product_update')
                self.assertIn(channel, ['10', '20'])
                self.assertIn('product_id', notification_data)
                self.assertIn('name', notification_data)
                self.assertIn('list_price', notification_data)
                self.assertIn('standard_price', notification_data)
                self.assertIn('qty_available', notification_data)
                self.assertIn('barcode', notification_data)
                self.assertIn('categ_id', notification_data)
                self.assertIn('taxes_id', notification_data)

    def test_notify_product_change_exception(self):
        """Test exception handling during bus notification."""
        product = self._create_product()

        sessions = self._mock_sessions()

        with patch.object(
            type(self.bus_model),
            '_sendone',
            side_effect=Exception('Bus notification failed')
        ):
            # Notification failure should not interrupt execution.
            product._notify_pos_product_change(
                product.product_variant_id,
                sessions
            )