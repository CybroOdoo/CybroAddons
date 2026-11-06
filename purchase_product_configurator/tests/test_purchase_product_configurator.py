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
from odoo import Command, fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestPurchaseProductConfigurator(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.attribute = cls.env['product.attribute'].create({
            'name': 'Configurator test attribute',
            'value_ids': [
                Command.create({'name': 'Value A'}),
                Command.create({'name': 'Value B'}),
            ],
        })
        cls.template = cls.env['product.template'].create({
            'name': 'Configurable purchase product',
            'product_config_mode': 'matrix',
            'attribute_line_ids': [Command.create({
                'attribute_id': cls.attribute.id,
                'value_ids': [Command.set(cls.attribute.value_ids.ids)],
            })],
        })

    def test_configurable_template_uses_selected_mode(self):
        result = self.template.get_single_product_variant()

        self.assertTrue(self.template.has_configurable_attributes)
        self.assertEqual(result['mode'], 'matrix')

    def test_non_configurable_template_always_uses_configurator_mode(self):
        template = self.env['product.template'].create({
            'name': 'Single purchase product',
            'product_config_mode': 'matrix',
        })

        result = template.get_single_product_variant()

        self.assertFalse(template.has_configurable_attributes)
        self.assertEqual(result['mode'], 'configurator')

    def test_variant_reports_available_optional_product(self):
        main = self.env['product.template'].create({
            'name': 'Main purchase product',
        })
        optional = self.env['product.template'].create({
            'name': 'Optional purchase product',
        })
        main.optional_product_ids = [Command.set(optional.ids)]

        result = main.get_single_product_variant()

        self.assertTrue(result.get('product_id'))
        self.assertTrue(result['has_optional_products'])

    def test_custom_attribute_value_is_kept_for_matching_template(self):
        custom_attribute = self.env['product.attribute'].create({
            'name': 'Custom purchase attribute',
            'create_variant': 'no_variant',
            'value_ids': [Command.create({
                'name': 'Custom value',
                'is_custom': True,
            })],
        })
        custom_template = self.env['product.template'].create({
            'name': 'Custom attribute product',
            'attribute_line_ids': [Command.create({
                'attribute_id': custom_attribute.id,
                'value_ids': [Command.set(custom_attribute.value_ids.ids)],
            })],
        })
        ptav = custom_template.attribute_line_ids.product_template_value_ids
        order = self.env['purchase.order'].create({
            'partner_id': self.env['res.partner'].create({
                'name': 'Configurator test vendor',
            }).id,
        })
        uom_id = (
            custom_template.uom_po_id.id
            if hasattr(custom_template, 'uom_po_id')
            else custom_template.uom_id.id
        )
        line_vals = {
            'order_id': order.id,
            'product_id': custom_template.product_variant_id.id,
            'name': custom_template.name,
            'product_qty': 1,
            'date_planned': fields.Datetime.now(),
            'purchase_product_custom_attribute_value_ids': [Command.create({
                'custom_product_template_attribute_value_id': ptav.id,
                'custom_value': 'Requested finish',
            })],
        }
        if 'product_uom_id' in self.env['purchase.order.line']._fields:
            line_vals['product_uom_id'] = uom_id
        elif 'product_uom' in self.env['purchase.order.line']._fields:
            line_vals['product_uom'] = uom_id
        line = self.env['purchase.order.line'].create(line_vals)

        self.assertEqual(len(line.purchase_product_custom_attribute_value_ids), 1)
        self.assertEqual(
            line.purchase_product_custom_attribute_value_ids.custom_value,
            'Requested finish',
        )

    def test_custom_attribute_value_is_removed_for_other_template(self):
        custom_attribute = self.env['product.attribute'].create({
            'name': 'Another custom attribute',
            'create_variant': 'no_variant',
            'value_ids': [Command.create({
                'name': 'Custom value',
                'is_custom': True,
            })],
        })
        custom_template = self.env['product.template'].create({
            'name': 'Custom attribute product for cleanup',
            'attribute_line_ids': [Command.create({
                'attribute_id': custom_attribute.id,
                'value_ids': [Command.set(custom_attribute.value_ids.ids)],
            })],
        })
        ptav = custom_template.attribute_line_ids.product_template_value_ids
        order = self.env['purchase.order'].create({
            'partner_id': self.env['res.partner'].create({
                'name': 'Another configurator test vendor',
            }).id,
        })
        uom_id = (
            custom_template.uom_po_id.id
            if hasattr(custom_template, 'uom_po_id')
            else custom_template.uom_id.id
        )
        line_vals = {
            'order_id': order.id,
            'product_id': custom_template.product_variant_id.id,
            'name': custom_template.name,
            'product_qty': 1,
            'date_planned': fields.Datetime.now(),
            'purchase_product_custom_attribute_value_ids': [Command.create({
                'custom_product_template_attribute_value_id': ptav.id,
                'custom_value': 'Requested finish',
            })],
        }
        if 'product_uom_id' in self.env['purchase.order.line']._fields:
            line_vals['product_uom_id'] = uom_id
        elif 'product_uom' in self.env['purchase.order.line']._fields:
            line_vals['product_uom'] = uom_id
        line = self.env['purchase.order.line'].create(line_vals)

        line.product_id = self.template.product_variant_id

        self.assertFalse(line.purchase_product_custom_attribute_value_ids)
