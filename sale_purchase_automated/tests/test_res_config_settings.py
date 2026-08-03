# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestResConfigSettings(TransactionCase):
    """Test cases for ResConfigSettings model — verifies all config parameters
    are correctly defined and can be toggled."""

    def setUp(self):
        super().setUp()
        # Clean up existing parameters to ensure a clean slate for config testing
        params = self.env['ir.config_parameter'].sudo()
        for key in ('automate_purchase', 'automate_print_bills',
                    'automate_sale', 'automate_invoice',
                    'automate_validate_invoice', 'automate_print_invoices'):
            params.set_param(key, False)
        self.config = self.env['res.config.settings'].create({})

    def test_automate_purchase_field_exists(self):
        """automate_purchase field should exist on res.config.settings."""
        self.assertIn('automate_purchase', self.config._fields)

    def test_automate_print_bills_field_exists(self):
        """automate_print_bills field should exist on res.config.settings."""
        self.assertIn('automate_print_bills', self.config._fields)

    def test_automate_sale_field_exists(self):
        """automate_sale field should exist on res.config.settings."""
        self.assertIn('automate_sale', self.config._fields)

    def test_automate_invoice_field_exists(self):
        """automate_invoice field should exist on res.config.settings."""
        self.assertIn('automate_invoice', self.config._fields)

    def test_automate_validate_invoice_field_exists(self):
        """automate_validate_invoice field should exist on res.config.settings."""
        self.assertIn('automate_validate_invoice', self.config._fields)

    def test_automate_print_invoices_field_exists(self):
        """automate_print_invoices field should exist on res.config.settings."""
        self.assertIn('automate_print_invoices', self.config._fields)

    def test_config_parameter_automate_purchase(self):
        """Setting automate_purchase=True should persist as ir.config_parameter."""
        self.config.automate_purchase = True
        self.config.execute()
        val = self.env['ir.config_parameter'].sudo().get_param('automate_purchase')
        self.assertEqual(val, 'True')

    def test_config_parameter_automate_sale(self):
        """Setting automate_sale=True should persist as ir.config_parameter."""
        self.config.automate_sale = True
        self.config.execute()
        val = self.env['ir.config_parameter'].sudo().get_param('automate_sale')
        self.assertEqual(val, 'True')

    def test_config_parameter_automate_invoice(self):
        """Setting automate_invoice=True should persist as ir.config_parameter."""
        self.config.automate_invoice = True
        self.config.execute()
        val = self.env['ir.config_parameter'].sudo().get_param('automate_invoice')
        self.assertEqual(val, 'True')

    def test_config_parameter_automate_validate_invoice(self):
        """Setting automate_validate_invoice=True should persist as ir.config_parameter."""
        self.config.automate_validate_invoice = True
        self.config.execute()
        val = self.env['ir.config_parameter'].sudo().get_param(
            'automate_validate_invoice')
        self.assertEqual(val, 'True')

    def test_config_parameter_automate_print_invoices(self):
        """Setting automate_print_invoices=True should persist as ir.config_parameter."""
        self.config.automate_print_invoices = True
        self.config.execute()
        val = self.env['ir.config_parameter'].sudo().get_param(
            'automate_print_invoices')
        self.assertEqual(val, 'True')

    def test_config_parameter_automate_print_bills(self):
        """Setting automate_print_bills=True should persist as ir.config_parameter."""
        self.config.automate_print_bills = True
        self.config.execute()
        val = self.env['ir.config_parameter'].sudo().get_param(
            'automate_print_bills')
        self.assertEqual(val, 'True')

    def test_all_flags_default_to_false(self):
        """All automation flags should default to False."""
        fresh = self.env['res.config.settings'].create({})
        print('fresh',fresh.automate_purchase)
        self.assertFalse(fresh.automate_purchase)
        self.assertFalse(fresh.automate_print_bills)
        self.assertFalse(fresh.automate_sale)
        self.assertFalse(fresh.automate_invoice)
        self.assertFalse(fresh.automate_validate_invoice)
        self.assertFalse(fresh.automate_print_invoices)
