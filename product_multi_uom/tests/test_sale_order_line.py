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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
"""Test suite for sale.order.line extension in product_multi_uom."""
from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestSaleOrderLine(TransactionCase):
    """Test cases for sale.order.line extension with secondary UoM logic."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Test Customer'})
        cls.uom_unit = cls.env.ref('uom.product_uom_unit', raise_if_not_found=False)
        if not cls.uom_unit:
            cls.uom_unit = cls.env['uom.uom'].create({
                'name': 'Test Base Unit Sale',
                'relative_factor': 1.0,
            })
        cls.uom_box = cls.env['uom.uom'].create({
            'name': 'Test Box of 12',
            'relative_uom_id': cls.uom_unit.id,
            'relative_factor': 12.0,
        })
        cls.uom_carton = cls.env['uom.uom'].create({
            'name': 'Test Carton of 24',
            'relative_uom_id': cls.uom_unit.id,
            'relative_factor': 24.0,
        })

        # Template with secondary UOMs
        cls.template = cls.env['product.template'].create({
            'name': 'Sale Test Multi UoM Template',
            'uom_id': cls.uom_unit.id,
            'is_need_secondary_uom': True,
            'secondary_uom_ids': [
                fields.Command.create({
                    'secondary_uom_id': cls.uom_box.id,
                    'secondary_uom_ratio': 12.0,
                }),
                fields.Command.create({
                    'secondary_uom_id': cls.uom_carton.id,
                    'secondary_uom_ratio': 24.0,
                }),
            ],
        })
        cls.product = cls.template.product_variant_ids[0]

        # Template without secondary UOMs
        cls.template_standard = cls.env['product.template'].create({
            'name': 'Sale Test Standard Template',
            'uom_id': cls.uom_unit.id,
            'is_need_secondary_uom': False,
        })
        cls.product_standard = cls.template_standard.product_variant_ids[0]

        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
        })

    def test_compute_is_secondary_readonly(self):
        """Test is_secondary_readonly is automatically computed when template or variant requires secondary UoM."""
        line_multi = self.env['sale.order.line'].create({
            'order_id': self.sale_order.id,
            'product_id': self.product.id,
        })
        self.assertTrue(line_multi.is_secondary_readonly)

        line_std = self.env['sale.order.line'].create({
            'order_id': self.sale_order.id,
            'product_id': self.product_standard.id,
        })
        self.assertFalse(line_std.is_secondary_readonly)

    def test_compute_secondary_uom_ids_from_template(self):
        """Test secondary_uom_ids fallback to template when variant has no explicit lines."""
        self.product.secondary_uom_ids = [fields.Command.clear()]
        line = self.env['sale.order.line'].create({
            'order_id': self.sale_order.id,
            'product_id': self.product.id,
        })
        line._compute_secondary_uom_ids()
        self.assertIn(self.uom_box, line.secondary_uom_ids)
        self.assertIn(self.uom_carton, line.secondary_uom_ids)

    def test_compute_secondary_uom_ids_from_variant_priority(self):
        """Test secondary_uom_ids prioritize variant-level secondary UoMs when present."""
        self.product.secondary_uom_ids = [
            fields.Command.clear(),
            fields.Command.create({
                'secondary_uom_id': self.uom_box.id,
                'secondary_uom_ratio': 12.0,
            }),
        ]
        line = self.env['sale.order.line'].create({
            'order_id': self.sale_order.id,
            'product_id': self.product.id,
        })
        line._compute_secondary_uom_ids()
        self.assertIn(self.uom_box, line.secondary_uom_ids)
        self.assertNotIn(self.uom_carton, line.secondary_uom_ids)

    def test_compute_secondary_uom_ids_empty(self):
        """Test secondary_uom_ids is empty for products without secondary UoM configuration."""
        line = self.env['sale.order.line'].create({
            'order_id': self.sale_order.id,
            'product_id': self.product_standard.id,
        })
        line._compute_secondary_uom_ids()
        self.assertEqual(len(line.secondary_uom_ids), 0)

    def test_compute_secondary_product_uom(self):
        """Test default secondary_product_uom_id computation."""
        # 1. Variant priority
        self.product.secondary_uom_ids = [
            fields.Command.clear(),
            fields.Command.create({
                'secondary_uom_id': self.uom_box.id,
                'secondary_uom_ratio': 12.0,
            }),
        ]
        line = self.env['sale.order.line'].create({
            'order_id': self.sale_order.id,
            'product_id': self.product.id,
        })
        line._compute_secondary_product_uom()
        self.assertEqual(line.secondary_product_uom_id, self.product.uom_id)

        # 2. Template fallback
        self.product.secondary_uom_ids = [fields.Command.clear()]
        line._compute_secondary_product_uom()
        self.assertEqual(line.secondary_product_uom_id, self.template.uom_id)

        # 3. Standard product without secondary UOMs
        line_std = self.env['sale.order.line'].create({
            'order_id': self.sale_order.id,
            'product_id': self.product_standard.id,
        })
        line_std._compute_secondary_product_uom()
        self.assertFalse(line_std.secondary_product_uom_id)

    def test_onchange_secondary_product_uom_id_template(self):
        """Test _onchange_secondary_product_uom_id recalculates product_uom_qty correctly."""
        line = self.env['sale.order.line'].create({
            'order_id': self.sale_order.id,
            'product_id': self.product.id,
        })
        line.secondary_product_uom_id = self.uom_box
        line.secondary_product_uom_qty = 3.0
        line._onchange_secondary_product_uom_id()
        # 3.0 boxes * 12.0 ratio = 36.0 units
        self.assertEqual(line.product_uom_qty, 36.0)

        # Switch to carton
        line.secondary_product_uom_id = self.uom_carton
        line.secondary_product_uom_qty = 2.0
        line._onchange_secondary_product_uom_id()
        # 2.0 cartons * 24.0 ratio = 48.0 units
        self.assertEqual(line.product_uom_qty, 48.0)

    def test_onchange_secondary_product_uom_id_variant_with_attributes(self):
        """Test _onchange_secondary_product_uom_id for product variant with attribute lines."""
        # Create an attribute and assign to template
        attribute = self.env['product.attribute'].create({'name': 'Size'})
        val_small = self.env['product.attribute.value'].create({
            'name': 'Small',
            'attribute_id': attribute.id,
        })
        template_attr = self.env['product.template'].create({
            'name': 'Template with Attributes',
            'uom_id': self.uom_unit.id,
            'is_need_secondary_uom': True,
            'attribute_line_ids': [
                fields.Command.create({
                    'attribute_id': attribute.id,
                    'value_ids': [fields.Command.set([val_small.id])],
                }),
            ],
        })
        variant = template_attr.product_variant_ids[0]
        variant.is_need_secondary_uom = True
        self.env['secondary.uom.line'].create({
            'product_id': variant.id,
            'secondary_uom_id': self.uom_box.id,
            'secondary_uom_ratio': 12.0,
        })

        line = self.env['sale.order.line'].create({
            'order_id': self.sale_order.id,
            'product_id': variant.id,
        })
        line.secondary_product_uom_id = self.uom_box
        line.secondary_product_uom_qty = 4.0
        line._onchange_secondary_product_uom_id()
        # 4.0 * 12.0 = 48.0
        self.assertEqual(line.product_uom_qty, 48.0)

    def test_onchange_secondary_product_uom_id_empty(self):
        """Test _onchange_secondary_product_uom_id handles empty secondary_product_uom_id gracefully."""
        line = self.env['sale.order.line'].create({
            'order_id': self.sale_order.id,
            'product_id': self.product.id,
        })
        line.secondary_product_uom_id = False
        line._onchange_secondary_product_uom_id()
        # Should not raise any error
        self.assertFalse(line.secondary_product_uom_id)
