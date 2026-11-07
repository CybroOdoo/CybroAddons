# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo.tests import Form, TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestBarcodeScanning(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env['product.product'].create({
            'name': 'Scanned product', 'barcode': 'IBS-TEST-001', 'is_storable': True})
        cls.product_2 = cls.env['product.product'].create({
            'name': 'Second product', 'barcode': 'IBS-TEST-002'})
        cls.picking_type = cls.env.ref('stock.picking_type_in')

    def _picking_form(self):
        return Form(self.env['stock.picking'].with_context(
            default_picking_type_id=self.picking_type.id))

    def test_scan_adds_and_increments_lines(self):
        """Scanning on the transfer adds a line, and scanning again counts up."""
        form = self._picking_form()
        form.barcode = 'IBS-TEST-001'
        self.assertFalse(form.barcode, "the field is cleared for the next scan")
        form.barcode = 'IBS-TEST-001'
        form.barcode = 'IBS-TEST-002'
        picking = form.save()
        moves = {move.product_id: move for move in picking.move_ids}
        self.assertEqual(set(moves), {self.product, self.product_2})
        self.assertEqual(moves[self.product].quantity, 2)
        self.assertEqual(moves[self.product].uom_id, self.product.uom_id)
        self.assertEqual(moves[self.product].barcode, 'IBS-TEST-001')
        self.assertEqual(moves[self.product_2].quantity, 1)
        self.assertEqual(moves[self.product].location_id, picking.location_id)
        self.assertEqual(moves[self.product].location_dest_id, picking.location_dest_id)

    def test_unknown_barcode_warns(self):
        picking = self.env['stock.picking'].new({
            'picking_type_id': self.picking_type.id, 'barcode': 'IBS-UNKNOWN'})
        result = picking._onchange_barcode()
        self.assertIn('IBS-UNKNOWN', result['warning']['message'])
        self.assertFalse(picking.barcode)
        self.assertFalse(picking.move_ids)

    def test_empty_barcode_does_nothing(self):
        picking = self.env['stock.picking'].new({'picking_type_id': self.picking_type.id})
        self.assertIsNone(picking._onchange_barcode())
        self.assertFalse(picking.move_ids)

    def test_barcode_on_move_line(self):
        """A barcode typed on a line picks the product, and picking a product
        fills its barcode."""
        form = self._picking_form()
        with form.move_ids.new() as move:
            move.barcode = 'IBS-TEST-002'
            self.assertEqual(move.product_id, self.product_2)
            move.product_uom_qty = 3
        with form.move_ids.new() as move:
            move.product_id = self.product
            self.assertEqual(move.barcode, 'IBS-TEST-001')
        picking = form.save()
        self.assertEqual(picking.move_ids.product_id, self.product | self.product_2)

    def test_unknown_barcode_on_move_line_keeps_product(self):
        form = self._picking_form()
        with form.move_ids.new() as move:
            move.product_id = self.product
            move.barcode = 'IBS-UNKNOWN'
            self.assertEqual(move.product_id, self.product)
