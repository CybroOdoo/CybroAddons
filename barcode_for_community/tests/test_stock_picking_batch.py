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


class TestStockPickingBatch(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.picking_type = cls.env.ref('stock.picking_type_internal', raise_if_not_found=False)
        if not cls.picking_type:
            cls.picking_type = cls.env['stock.picking.type'].search([('code', '=', 'internal')], limit=1)

    def test_batch_operations(self):
        """Test full batch methods and barcode data extraction"""
        batch = self.env['stock.picking.batch'].create({
            'name': 'Test Batch Comprehensive',
            'picking_type_id': self.picking_type.id if self.picking_type else False,
        })
        action = batch.open_batch_record()
        self.assertEqual(action.get('type'), 'ir.actions.client')
        self.assertEqual(action.get('tag'), 'custom_batch_lines_client_action')

        form_action = batch.open_batch_picking()
        self.assertEqual(form_action.get('type'), 'ir.actions.act_window')
        self.assertEqual(form_action.get('res_model'), 'stock.picking.batch')
        self.assertEqual(form_action.get('res_id'), batch.id)

        fields_batch = batch.get_barcode_batch_fields()
        self.assertIn('name', fields_batch)

        batch_data = batch.get_barcode_batch()
        self.assertTrue(len(batch_data) > 0)
        self.assertEqual(batch_data[0]['name'], 'Test Batch Comprehensive')

        line_fields = batch.batch_barcode_move_line_fields()
        self.assertIn('product_id', line_fields)

        move_lines = batch.get_barcode_batch_move_line()
        self.assertIsInstance(move_lines, list)
