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
from unittest.mock import patch
from uuid import uuid4

from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestPosAutomatedManufacturing(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.component = cls.env['product.product'].create({
            'name': 'Automated MRP component',
            'type': 'consu',
            'is_storable': True,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Automated MRP product',
            'type': 'consu',
            'is_storable': True,
        })
        cls.bom = cls.env['mrp.bom'].create({
            'product_tmpl_id': cls.product.product_tmpl_id.id,
            'product_qty': 1,
            'type': 'normal',
            'bom_line_ids': [Command.create({
                'product_id': cls.component.id,
                'product_qty': 1,
            })],
        })
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Automated MRP POS',
            'company_id': cls.company.id,
        })
        cls.pos_session = cls.env['pos.session'].create({
            'config_id': cls.pos_config.id,
        })

    def _create_order(self, lines):
        return self.env['pos.order'].create({
            # Orders created directly in tests do not receive the frontend's
            # session sequence name, so assign unique origins for MO searches.
            'name': f'Test POS {uuid4().hex}',
            'session_id': self.pos_session.id,
            'amount_total': sum(line[2]['price_subtotal'] for line in lines),
            'amount_tax': 0,
            'amount_paid': 0,
            'amount_return': 0,
            'lines': lines,
        })

    def _line(self, product, quantity=1, price=100):
        return Command.create({
            'name': product.display_name,
            'product_id': product.id,
            'qty': quantity,
            'price_unit': price,
            'price_subtotal': quantity * price,
            'price_subtotal_incl': quantity * price,
        })

    def test_to_create_mrp_requires_a_bom(self):
        product = self.env['product.product'].create({
            'name': 'Product without BoM',
            'type': 'consu',
            'is_storable': True,
        })

        with self.assertRaisesRegex(ValidationError, 'Bill of Materials'):
            product.to_create_mrp = True

    def test_template_bom_satisfies_constraint(self):
        self.assertTrue(self.bom)
        self.product.to_create_mrp = True
        self.assertTrue(self.product.to_create_mrp)

    def test_variant_bom_satisfies_constraint(self):
        product_template = self.env['product.template'].create({
            'name': 'Variant BoM product',
            'type': 'consu',
            'is_storable': True,
        })
        variant = product_template.product_variant_id
        self.env['mrp.bom'].create({
            'product_tmpl_id': product_template.id,
            'product_id': variant.id,
            'product_qty': 1,
            'type': 'normal',
            'bom_line_ids': [Command.create({
                'product_id': self.component.id,
                'product_qty': 1,
            })],
        })

        product_template.to_create_mrp = True

        self.assertTrue(product_template.to_create_mrp)

    def test_disabling_automation_does_not_require_a_bom(self):
        self.product.to_create_mrp = True
        self.product.to_create_mrp = False
        self.assertFalse(self.product.to_create_mrp)

    def test_pos_product_data_includes_automation_fields(self):
        fields = self.env['product.product']._load_pos_data_fields(self.pos_config)

        self.assertIn('to_create_mrp', fields)
        self.assertIn('create_mrp_done', fields)

    def test_creates_confirmed_mrp_with_order_values(self):
        self.product.to_create_mrp = True
        order = self._create_order([self._line(self.product, quantity=2)])

        order.create_mrp_orders()

        production = self.env['mrp.production'].search([
            ('origin', '=', order.name),
        ])
        self.assertEqual(len(production), 1)
        self.assertEqual(production.product_id, self.product)
        self.assertEqual(production.product_qty, 2)
        self.assertEqual(production.bom_id, self.bom)
        self.assertEqual(production.company_id, order.company_id)
        self.assertEqual(production.date_start, order.date_order)
        self.assertEqual(production.state, 'confirmed')

    def test_creates_mrp_only_for_automated_lines(self):
        self.product.to_create_mrp = True
        manual_product = self.env['product.product'].create({
            'name': 'Manual product on POS',
            'type': 'consu',
            'is_storable': True,
        })
        order = self._create_order([
            self._line(self.product, quantity=2),
            self._line(manual_product, quantity=3),
        ])

        order.create_mrp_orders()

        productions = self.env['mrp.production'].search([
            ('origin', '=', order.name),
        ])
        self.assertEqual(len(productions), 1)
        self.assertEqual(productions.product_id, self.product)

    def test_missing_bom_does_not_create_mrp(self):
        self.product.to_create_mrp = True
        order = self._create_order([self._line(self.product)])
        bom_model = type(self.env['mrp.bom'])

        with patch.object(bom_model, '_bom_find', return_value={self.product: False}):
            order.create_mrp_orders()

        self.assertFalse(self.env['mrp.production'].search([
            ('origin', '=', order.name),
        ]))

    def test_done_option_completes_manufacturing_order(self):
        self.product.to_create_mrp = True
        self.product.create_mrp_done = True
        warehouse = self.env['stock.warehouse'].search([
            ('company_id', '=', self.company.id),
        ], limit=1)
        self.env['stock.quant']._update_available_quantity(
            self.component, warehouse.lot_stock_id, 10,
        )
        order = self._create_order([self._line(self.product)])

        order.create_mrp_orders()

        production = self.env['mrp.production'].search([
            ('origin', '=', order.name),
        ])
        self.assertEqual(len(production), 1)
        self.assertEqual(production.state, 'done')

    def test_create_order_without_lines_creates_no_mrp(self):
        order = self._create_order([])

        order.create_mrp_orders()

        self.assertFalse(self.env['mrp.production'].search([
            ('origin', '=', order.name),
        ]))

    def test_multi_record_batch_creation(self):
        self.product.to_create_mrp = True
        order1 = self._create_order([self._line(self.product, quantity=1)])
        order2 = self._create_order([self._line(self.product, quantity=2)])
        orders = order1 | order2

        mrp_orders = orders.create_mrp_orders()

        self.assertEqual(len(mrp_orders), 2)
        prod1 = self.env['mrp.production'].search([
            ('origin', '=', order1.name),
        ])
        prod2 = self.env['mrp.production'].search([
            ('origin', '=', order2.name),
        ])
        self.assertEqual(len(prod1), 1)
        self.assertEqual(len(prod2), 1)
        self.assertEqual(prod1.product_qty, 1)
        self.assertEqual(prod2.product_qty, 2)

    def test_negative_quantity_return_creates_no_mrp(self):
        self.product.to_create_mrp = True
        return_order = self._create_order([
            self._line(self.product, quantity=-1),
        ])

        mrp_orders = return_order.create_mrp_orders()

        self.assertFalse(mrp_orders)
        self.assertFalse(self.env['mrp.production'].search([
            ('origin', '=', return_order.name),
        ]))
