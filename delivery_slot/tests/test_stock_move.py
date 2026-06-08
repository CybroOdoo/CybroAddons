# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:  Cybrosys Technologies (odoo@cybrosys.com)
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

from odoo.addons.stock.tests.common import TestStockCommon


class TestStockMoveDeliverySlot(TestStockCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Stock Slot Partner'})

    def _create_sale_order_for_origin(self, name, slot_per_product):
        return self.env['sale.order'].create({
            'name': name,
            'partner_id': self.partner.id,
            'slot_per_product': slot_per_product,
        })

    def _create_moves(self, origin):
        move_values = {
            'product_id': self.product_1.id,
            'product_uom_qty': 1.0,
            'product_uom': self.product_1.uom_id.id,
            'location_id': self.stock_location.id,
            'location_dest_id': self.customer_location.id,
            'warehouse_id': self.warehouse_1.id,
            'picking_type_id': self.picking_type_out.id,
            'origin': origin,
            'state': 'confirmed',
        }
        return self.env['stock.move'].create([
            dict(move_values, description_picking='Slot Move A'),
            dict(move_values, description_picking='Slot Move B'),
        ])

    def test_assign_picking_splits_moves_when_sale_order_uses_slot_per_product(self):
        origin = 'SO-SLOT-PER-PRODUCT'
        self._create_sale_order_for_origin(origin, slot_per_product=True)
        moves = self._create_moves(origin)

        moves._assign_picking()

        self.assertEqual(len(moves.picking_id), 2)

    def test_assign_picking_groups_moves_when_sale_order_does_not_use_slot_per_product(self):
        origin = 'SO-NORMAL-DELIVERY'
        self._create_sale_order_for_origin(origin, slot_per_product=False)
        moves = self._create_moves(origin)

        moves._assign_picking()

        self.assertEqual(len(moves.picking_id), 1)
