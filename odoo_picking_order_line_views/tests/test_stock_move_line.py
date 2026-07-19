# -*- coding: utf-8 -*-
#############################################################################
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
#############################################################################
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestStockMoveLine(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
        })

        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer',
        })

        cls.picking_type = cls.env.ref(
            'stock.picking_type_out'
        )

        cls.picking = cls.env['stock.picking'].create({
            'partner_id': cls.partner.id,
            'picking_type_id': cls.picking_type.id,
            'location_id':
                cls.picking_type.default_location_src_id.id,
            'location_dest_id':
                cls.picking_type.default_location_dest_id.id,
        })

        cls.move = cls.env['stock.move'].create({
            'product_id': cls.product.id,
            'product_uom_qty': 1,
            'product_uom': cls.product.uom_id.id,
            'picking_id': cls.picking.id,
            'location_id': cls.picking.location_id.id,
            'location_dest_id': cls.picking.location_dest_id.id,
        })

        cls.move_line = cls.env['stock.move.line'].create({
            'move_id': cls.move.id,
            'product_id': cls.product.id,
            'product_uom_id': cls.product.uom_id.id,
            'quantity': 1,
            'picking_id': cls.picking.id,
            'location_id': cls.picking.location_id.id,
            'location_dest_id':
                cls.picking.location_dest_id.id,
        })

    def test_move_line_image_relation(self):
        """Test move image related field"""
        self.assertEqual(
            self.move.move_line_image,
            self.product.image_1920
        )

    def test_move_line_related_fields(self):
        """Test related fields"""
        self.assertEqual(
            self.move_line.picking_type_id,
            self.picking.picking_type_id
        )
        self.assertEqual(
            self.move_line.code,
            self.picking.picking_type_id.code
        )
