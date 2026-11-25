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


class TestResConfigSettings(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

    def test_action_print_barcode_product(self):
        """Test printing barcode from res_config_settings for product"""
        config = self.env['res.config.settings'].with_context(model='product.product').create({})
        action = config.action_print_barcode()
        self.assertIn(action.get('type'), ['ir.actions.report', 'ir.actions.act_window'])

    def test_action_print_barcode_location(self):
        """Test printing barcode for location"""
        config = self.env['res.config.settings'].with_context(model='stock.location').create({})
        action = config.action_print_barcode()
        self.assertIn(action.get('type'), ['ir.actions.report', 'ir.actions.act_window'])

    def test_action_print_barcode_picking_type(self):
        """Test printing barcode for picking type"""
        config = self.env['res.config.settings'].with_context(model='stock.picking.type').create({})
        action = config.action_print_barcode()
        self.assertIn(action.get('type'), ['ir.actions.report', 'ir.actions.act_window'])

    def test_action_print_barcode_inventory_commands(self):
        """Test printing barcode for inventory commands (default branch)"""
        config = self.env['res.config.settings'].with_context(model='inventory_commands').create({})
        action = config.action_print_barcode()
        self.assertIn(action.get('type'), ['ir.actions.report', 'ir.actions.act_window'])
