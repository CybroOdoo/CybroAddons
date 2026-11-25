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


class TestStockMoveLine(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env['product.product'].create({
            'name': 'Test Move Line Product',
            'type': 'consu',
            'is_storable': True,
        })
        cls.location = cls.env['stock.location'].create({'name': 'Loc', 'usage': 'internal'})
        cls.location_dest = cls.env['stock.location'].create({'name': 'DestLoc', 'usage': 'internal'})

    def test_batch_read(self):
        """Testing batch read capability on stock move lines"""
        move = self.env['stock.move'].create({
            'description_picking': 'Test Move for Line',
            'product_id': self.product.id,
            'product_uom_qty': 5,
            'product_uom': self.product.uom_id.id,
            'location_id': self.location.id,
            'location_dest_id': self.location_dest.id,
        })
        line = self.env['stock.move.line'].create({
            'move_id': move.id,
            'product_id': self.product.id,
            'product_uom_id': self.product.uom_id.id,
            'location_id': self.location.id,
            'location_dest_id': self.location_dest.id,
            'quantity': 2,
            'lot_serial_name': 'LOT-001',
            'is_barcode_scanned': True,
            'had_location_by_barcode': True,
            'had_location_by_barcode_dest': False,
        })
        res = line.batch_read(['id', 'product_id', 'quantity'])
        self.assertIsInstance(res, list)
        self.assertEqual(len(res), 1)
        self.assertIn('move_id', res[0])
        self.assertEqual(res[0]['move_id'][0]['product_uom_qty'], 5)
        self.assertTrue(line.is_barcode_scanned)
        self.assertTrue(line.had_location_by_barcode)
