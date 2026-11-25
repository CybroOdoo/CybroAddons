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


class TestStockMove(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
            'is_storable': True,
        })
        cls.location_src = cls.env['stock.location'].create({'name': 'Source', 'usage': 'internal'})
        cls.location_dest = cls.env['stock.location'].create({'name': 'Dest', 'usage': 'internal'})

    def test_compute_done_quantity(self):
        """Test logic for computing done quantity via barcode"""
        move = self.env['stock.move'].create({
            'description_picking': 'Test Move',
            'product_id': self.product.id,
            'product_uom_qty': 10,
            'product_uom': self.product.uom_id.id,
            'location_id': self.location_src.id,
            'location_dest_id': self.location_dest.id,
            'with_barcode': True,
        })
        move.quantity = 4
        self.assertEqual(move.done_quantity, 4)

        move.with_barcode = False
        move._compute_done_quantity()
        self.assertEqual(move.done_quantity, 0)

    def test_inverse_done_quantity(self):
        """Test inverse done quantity writing to quantity"""
        move = self.env['stock.move'].create({
            'description_picking': 'Test Move Inverse',
            'product_id': self.product.id,
            'product_uom_qty': 5,
            'product_uom': self.product.uom_id.id,
            'location_id': self.location_src.id,
            'location_dest_id': self.location_dest.id,
            'with_barcode': True,
        })
        move.done_quantity = 3
        self.assertEqual(move.quantity, 3)

    def test_generate_serial_numbers(self):
        """Test serial numbers generation method"""
        product_serial = self.env['product.product'].create({
            'name': 'Tracked Product',
            'type': 'consu',
            'is_storable': True,
            'tracking': 'serial',
        })
        move = self.env['stock.move'].create({
            'description_picking': 'Test Move Serial',
            'product_id': product_serial.id,
            'product_uom_qty': 2,
            'product_uom': product_serial.uom_id.id,
            'location_id': self.location_src.id,
            'location_dest_id': self.location_dest.id,
        })
        move.generate_serial_numbers({'sn': 'SN001', 'count': 2})
        self.assertEqual(move.next_serial, 'SN001')
