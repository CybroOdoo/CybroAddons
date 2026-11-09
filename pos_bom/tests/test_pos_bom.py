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
#############################################################################
from odoo import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestPosBom(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.finished_product = cls.env['product.template'].create({
            'name': 'POS BOM finished product',
            'is_bom': True,
            'type': 'consu',
            'is_storable': True,
        })
        cls.component = cls.env['product.product'].create({
            'name': 'POS BOM component',
            'type': 'consu',
            'is_storable': True,
        })

    def test_bom_product_onchange_sets_product_unit(self):
        bom = self.env['pos.product.bom'].new({
            'product_id': self.finished_product.id,
        })

        bom.onchange_product_id()

        self.assertEqual(bom.product_uom_id, self.finished_product.uom_id)

    def test_component_onchange_sets_component_unit(self):
        component_line = self.env['pos.bom.line'].new({
            'product_id': self.component.id,
        })

        component_line.onchange_product()

        self.assertEqual(component_line.product_uom_id, self.component.uom_id)

    def test_bom_stores_finished_product_and_component_quantities(self):
        bom = self.env['pos.product.bom'].create({
            'product_id': self.finished_product.id,
            'quantity': 2,
            'product_uom_id': self.finished_product.uom_id.id,
            'bom_line_ids': [Command.create({
                'product_id': self.component.id,
                'quantity': 3,
                'product_uom_id': self.component.uom_id.id,
            })],
        })

        self.assertTrue(self.finished_product.is_bom)
        self.assertEqual(bom.product_id, self.finished_product)
        self.assertEqual(bom.quantity, 2)
        self.assertEqual(len(bom.bom_line_ids), 1)
        self.assertEqual(bom.bom_line_ids.product_id, self.component)
        self.assertEqual(bom.bom_line_ids.quantity, 3)

    def test_pos_picking_creates_done_component_move(self):
        self.env['pos.product.bom'].create({
            'product_id': self.finished_product.id,
            'quantity': 2,
            'product_uom_id': self.finished_product.uom_id.id,
            'bom_line_ids': [Command.create({
                'product_id': self.component.id,
                'quantity': 3,
                'product_uom_id': self.component.uom_id.id,
            })],
        })
        config = self.env['pos.config'].create({'name': 'POS BOM test'})
        session = self.env['pos.session'].create({'config_id': config.id})
        order = self.env['pos.order'].create({
            'session_id': session.id,
            'amount_total': 200,
            'amount_tax': 0,
            'amount_paid': 200,
            'amount_return': 0,
            'lines': [Command.create({
                'name': self.finished_product.name,
                'product_id': self.finished_product.product_variant_id.id,
                'qty': 2,
                'price_unit': 100,
                'price_subtotal': 200,
                'price_subtotal_incl': 200,
            })],
        })
        picking_type = config.picking_type_id
        picking = self.env['stock.picking'].create({
            'picking_type_id': picking_type.id,
            'location_id': picking_type.default_location_src_id.id,
            'location_dest_id': self.env.ref('stock.stock_location_customers').id,
        })

        picking._create_move_from_pos_order_lines(order.lines)
        component_move = picking.move_ids.filtered(
            lambda move: move.product_id == self.component
        )
        self.assertEqual(len(component_move), 1)
        self.assertEqual(component_move.product_uom_qty, 3)
        self.assertTrue(component_move.move_line_ids)

        picking._action_done()

        self.assertEqual(component_move.state, 'done')
        self.assertEqual(component_move.quantity, 3)
