# -*- coding: utf-8 -*-
#################################################################################
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
################################################################################

from odoo.tests.common import TransactionCase
from ..controllers.website_estimated_delivery_time import WebsiteEstimatedDeliveryTime


class TestDeliveryController(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Controller = WebsiteEstimatedDeliveryTime()
        cls.Settings = cls.env['website.estimated.delivery.time'].create({
            'available_message': 'Expected within',
            'display_mode': 'exact',
            'number_of_days': 2,
        })

    def test_format_available_message_exact(self):
        """Test formatting in 'exact' mode"""
        self.Settings.display_mode = 'exact'
        msg = self.Controller._format_available_message(self.Settings, 5)
        self.assertEqual(msg, 'Expected within 5 Days')

    def test_format_available_message_range_after(self):
        """Test formatting in 'range' mode with 'days_after'"""
        self.Settings.display_mode = 'range'
        self.Settings.delivery_day_range = 'days_after'
        self.Settings.number_of_days = 3
        msg = self.Controller._format_available_message(self.Settings, 5)
        self.assertEqual(msg, 'Expected within 5 - 8 Days')

    def test_format_available_message_range_before(self):
        """Test formatting in 'range' mode with 'days_before'"""
        self.Settings.display_mode = 'range'
        self.Settings.delivery_day_range = 'days_before'
        self.Settings.number_of_days = 2
        msg = self.Controller._format_available_message(self.Settings, 5)
        self.assertEqual(msg, 'Expected within 3 - 5 Days')

    def test_format_available_message_no_settings(self):
        """Test formatting when settings are missing (fallback)"""
        msg = self.Controller._format_available_message(None, 5)
        self.assertEqual(msg, 'This Product Will Be Delivered Within 5 Days')

    def test_website_estimated_delivery_time_logic(self):
        """Test the logic of the controller's main method using mocked request.env"""
        import odoo.addons.website_estimated_delivery_time.controllers.website_estimated_delivery_time as ctrl_mod
        from unittest.mock import MagicMock

        product = self.env['product.template'].create({
            'name': 'Test Product',
            'overwrite_existing_config': False,
        })
        product.product_estimated_delivery_time_ids = [(0, 0, {
            'name': 'NY',
            'pin': '10001',
            'days': 3,
        })]
        self.Settings.estimated_delivery_time_ids = [(0, 0, {
            'name': 'Global NY',
            'pin': '10001',
            'days': 5,
        })]

        mock_request = MagicMock()
        mock_request.env = self.env

        original_request = ctrl_mod.request
        ctrl_mod.request = mock_request
        try:
            # Test with matching PIN when overwrite is False -> uses global website config
            result = self.Controller.website_estimated_delivery_time(
                product_template_id=str(product.id), pin_number='10001'
            )
            self.assertEqual(result.get('website_base_availability'), 'True')
            self.assertEqual(result.get('available_message'), 'Expected within 5 Days')

            # Test with non-matching PIN
            result_no_match = self.Controller.website_estimated_delivery_time(
                product_template_id=str(product.id), pin_number='99999'
            )
            self.assertFalse(result_no_match.get('available_message'))
        finally:
            ctrl_mod.request = original_request

    def test_global_delivery_records_are_separated_by_display_mode(self):
        """Range mode uses only PIN estimates entered in Range mode."""
        import odoo.addons.website_estimated_delivery_time.controllers.website_estimated_delivery_time as ctrl_mod
        from unittest.mock import MagicMock

        product = self.env['product.template'].create({
            'name': 'Test Product Mode Separation',
            'overwrite_existing_config': False,
        })
        self.Settings.write({
            'display_mode': 'range',
            'number_of_days': 2,
            'delivery_day_range': 'days_after',
            'estimated_delivery_time_ids': [
                (0, 0, {
                    'name': 'Exact Calicut',
                    'pin': '670001',
                    'days': 3,
                    'display_mode': 'exact',
                }),
                (0, 0, {
                    'name': 'Range Calicut',
                    'pin': '670001',
                    'days': 5,
                    'display_mode': 'range',
                }),
            ],
        })
        self.assertEqual(
            self.Settings.exact_estimated_delivery_time_ids.mapped('name'),
            ['Exact Calicut'],
        )
        self.assertEqual(
            self.Settings.range_estimated_delivery_time_ids.mapped('name'),
            ['Range Calicut'],
        )
        mock_request = MagicMock()
        mock_request.env = self.env
        original_request = ctrl_mod.request
        ctrl_mod.request = mock_request
        try:
            result = self.Controller.website_estimated_delivery_time(
                product_template_id=str(product.id), pin_number='670001'
            )
            self.assertEqual(result.get('website_base_availability'), 'True')
            self.assertEqual(
                result.get('available_message'), 'Expected within 5 - 7 Days'
            )
        finally:
            ctrl_mod.request = original_request

    def test_website_estimated_delivery_time_overwrite(self):
        """Test controller logic when overwrite_existing_config is True"""
        import odoo.addons.website_estimated_delivery_time.controllers.website_estimated_delivery_time as ctrl_mod
        from unittest.mock import MagicMock

        product = self.env['product.template'].create({
            'name': 'Test Product Overwrite',
            'overwrite_existing_config': True,
        })
        product.product_estimated_delivery_time_ids = [(0, 0, {
            'name': 'NY',
            'pin': '10001',
            'days': 3,
        })]
        self.Settings.estimated_delivery_time_ids = [(0, 0, {
            'name': 'Global NY',
            'pin': '10001',
            'days': 5,
        })]

        mock_request = MagicMock()
        mock_request.env = self.env

        original_request = ctrl_mod.request
        ctrl_mod.request = mock_request
        try:
            # Test when overwrite is True -> uses product config (3 days) instead of global
            result = self.Controller.website_estimated_delivery_time(
                product_template_id=str(product.id), pin_number='10001'
            )
            self.assertEqual(result.get('product_base_availability'), 'True')
            self.assertEqual(result.get('available_message'), 'Expected within 3 Days')

            # Test non-matching product PIN when overwrite is True -> should NOT fallback to global
            result_no_fallback = self.Controller.website_estimated_delivery_time(
                product_template_id=str(product.id), pin_number='20002'
            )
            self.assertFalse(result_no_fallback.get('available_message'))
        finally:
            ctrl_mod.request = original_request
