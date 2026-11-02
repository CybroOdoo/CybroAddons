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
class TestSaleTenderCreateAlternative(TransactionCase):
    """Test suite covering the sale.tender.create.alternative wizard."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner = cls.env['res.partner'].create({
            'name': 'Original Customer',
            'company_id': cls.company.id,
        })
        cls.alt_partner = cls.env['res.partner'].create({
            'name': 'Alternative Customer',
            'company_id': cls.company.id,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Alternative Test Product',
            'list_price': 80.0,
        })
        cls.origin_so = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'origin': 'Test Origin Quote',
            'order_line': [Command.create({
                'product_id': cls.product.id,
                'product_uom_qty': 3.0,
                'price_unit': 80.0,
            })],
        })

    def test_wizard_create_alternative_with_copy_products(self):
        """Test creating an alternative order copying products from the original order."""
        wizard = self.env['sale.tender.create.alternative'].create({
            'origin_so_id': self.origin_so.id,
            'partner_id': self.alt_partner.id,
            'copy_products': True,
        })

        action = wizard.action_create_alternative()
        self.assertEqual(action['res_model'], 'sale.order')
        self.assertEqual(action['view_mode'], 'form')

        alt_so = self.env['sale.order'].browse(action['res_id'])
        self.assertTrue(alt_so.exists())
        self.assertEqual(alt_so.partner_id, self.alt_partner)
        self.assertEqual(alt_so.origin, self.origin_so.origin)
        self.assertEqual(len(alt_so.order_line), 1)
        self.assertEqual(alt_so.order_line.product_id, self.product)
        self.assertEqual(alt_so.order_line.product_uom_qty, 3.0)

        # Check alternative grouping
        self.assertEqual(self.origin_so.sale_group_id, alt_so.sale_group_id)
        self.assertIn(alt_so, self.origin_so.alternative_so_ids)

    def test_wizard_create_alternative_without_copy_products(self):
        """Test creating an alternative order without copying products."""
        wizard = self.env['sale.tender.create.alternative'].create({
            'origin_so_id': self.origin_so.id,
            'partner_id': self.alt_partner.id,
            'copy_products': False,
        })

        action = wizard.action_create_alternative()
        alt_so = self.env['sale.order'].browse(action['res_id'])
        self.assertTrue(alt_so.exists())
        self.assertEqual(alt_so.partner_id, self.alt_partner)
        self.assertEqual(len(alt_so.order_line), 0, "Order lines should not be copied when copy_products=False")
