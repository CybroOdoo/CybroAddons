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


class TestStockPicking(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.stock_loc = cls.env.ref('stock.stock_location_stock', raise_if_not_found=False)
        if not cls.stock_loc:
            cls.stock_loc = cls.env['stock.location'].search([('usage', '=', 'internal')], limit=1)
        if not cls.stock_loc:
            cls.stock_loc = cls.env['stock.location'].create({'name': 'Stock', 'usage': 'internal'})

        cls.cust_loc = cls.env.ref('stock.stock_location_customers', raise_if_not_found=False)
        if not cls.cust_loc:
            cls.cust_loc = cls.env['stock.location'].search([('usage', '=', 'customer')], limit=1)
        if not cls.cust_loc:
            cls.cust_loc = cls.env['stock.location'].create({'name': 'Customers', 'usage': 'customer'})

        cls.picking_type = cls.env.ref('stock.picking_type_out', raise_if_not_found=False)
        if not cls.picking_type:
            cls.picking_type = cls.env['stock.picking.type'].search([('code', '=', 'outgoing')], limit=1)

    def test_open_record(self):
        """Test open custom stock picking client action format"""
        picking = self.env['stock.picking'].create({
            'location_id': self.stock_loc.id,
            'location_dest_id': self.cust_loc.id,
            'picking_type_id': self.picking_type.id,
        })
        action = picking.open_record()
        self.assertEqual(action.get('type'), 'ir.actions.client')
        self.assertEqual(action.get('tag'), 'custom_location_client_action')

    def test_open_picking(self):
        """Test open standard stock picking form action"""
        picking = self.env['stock.picking'].create({
            'location_id': self.stock_loc.id,
            'location_dest_id': self.cust_loc.id,
            'picking_type_id': self.picking_type.id,
        })
        action = picking.open_picking()
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), 'stock.picking')
        self.assertEqual(action.get('res_id'), picking.id)

    def test_get_barcode_picking(self):
        """Test read and return barcode related picking data"""
        picking = self.env['stock.picking'].create({
            'location_id': self.stock_loc.id,
            'location_dest_id': self.cust_loc.id,
            'picking_type_id': self.picking_type.id,
            'with_barcode': True,
        })
        fields_list = picking.picking_barcode_fields()
        self.assertIn('with_barcode', fields_list)
        res = picking.get_barcode_picking()
        self.assertTrue(len(res) > 0)
        self.assertIn('picking_type', res[0])
