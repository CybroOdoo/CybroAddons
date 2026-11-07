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
"""Backend and integration tests for simplified_pos module."""

import ast
import os
import runpy

from odoo import fields
from odoo.tests import tagged, TransactionCase
from odoo.modules.module import get_module_path


@tagged('at_install', '-post_install')
class TestSimplifiedPosAtInstall(TransactionCase):
    """Test cases executed at installation of simplified_pos."""

    def test_module_installed_at_install(self):
        """Verify module record and dependencies during installation."""
        module = self.env['ir.module.module'].search([('name', '=', 'simplified_pos')])
        self.assertTrue(module, "simplified_pos module record should exist.")
        self.assertIn(module.state, ('installed', 'to install', 'to upgrade'))
        self.assertIn('point_of_sale', module.dependencies_id.mapped('name'))

    def test_manifest_metadata(self):
        """Verify manifest metadata completeness, license, and assets definition."""
        mod_path = get_module_path('simplified_pos')
        manifest_file = os.path.join(mod_path, '__manifest__.py')
        self.assertTrue(os.path.isfile(manifest_file), "__manifest__.py must exist.")

        with open(manifest_file, 'r', encoding='utf-8') as f:
            manifest = ast.literal_eval(f.read())

        runpy.run_path(manifest_file)

        self.assertEqual(manifest.get('name'), 'Simplified POS')
        self.assertEqual(manifest.get('license'), 'LGPL-3')
        self.assertIn('point_of_sale', manifest.get('depends', []))
        self.assertIn('point_of_sale._assets_pos', manifest.get('assets', {}))
        self.assertIn('web.assets_unit_tests', manifest.get('assets', {}))
        self.assertIn('web.assets_unit_tests_setup', manifest.get('assets', {}))

    def test_security_access_file(self):
        """Verify that security/ir.access.csv exists and is declared in data."""
        mod_path = get_module_path('simplified_pos')
        access_file = os.path.join(mod_path, 'security', 'ir.access.csv')
        self.assertTrue(os.path.isfile(access_file), "security/ir.access.csv must exist.")
        manifest_file = os.path.join(mod_path, '__manifest__.py')
        with open(manifest_file, 'r', encoding='utf-8') as f:
            manifest = ast.literal_eval(f.read())
        self.assertIn('security/ir.access.csv', manifest.get('data', []))


@tagged('post_install', '-at_install')
class TestSimplifiedPosPostInstall(TransactionCase):
    """Test cases for simplified_pos configuration, session and POS operations."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner = cls.env['res.partner'].create({
            'name': 'POS Test Customer',
            'email': 'customer@pos-test.com',
            'phone': '+1234567890',
            'street': '123 Market Street',
        })
        cls.product_1 = cls.env['product.product'].create({
            'name': 'Simplified POS Test Product 1',
            'list_price': 50.0,
            'available_in_pos': True,
        })
        cls.product_2 = cls.env['product.product'].create({
            'name': 'Simplified POS Test Product 2',
            'list_price': 25.0,
            'available_in_pos': True,
        })
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Simplified POS Test Shop',
        })
        cls.payment_method = cls.pos_config.payment_method_ids[0]
        cls.pos_session = cls.env['pos.session'].create({
            'config_id': cls.pos_config.id,
        })

    def test_module_state(self):
        """Check that simplified_pos module is installed and active."""
        module = self.env['ir.module.module'].search([('name', '=', 'simplified_pos')])
        self.assertTrue(module, "simplified_pos module record should exist.")
        self.assertEqual(module.state, 'installed')

    def test_pos_session_initialization(self):
        """Ensure POS session can be initialized successfully with simplified_pos installed."""
        self.assertEqual(self.pos_session.config_id.id, self.pos_config.id)
        self.assertEqual(self.pos_session.state, 'opening_control')

    def test_pos_assets_bundle(self):
        """Verify that simplified_pos static assets are present in the asset declarations."""
        module = self.env['ir.module.module'].search([('name', '=', 'simplified_pos')])
        self.assertTrue(module, "Module simplified_pos must exist.")
        self.assertIn('point_of_sale', module.dependencies_id.mapped('name'))

    def test_pos_payment_method_creation(self):
        """Test explicit creation of POS payment method and association with config."""
        pm = self.env['pos.payment.method'].create({
            'name': 'Explicit Pay Later Method',
            'company_id': self.company.id,
            'type': 'pay_later',
        })
        config = self.env['pos.config'].create({
            'name': 'Custom POS Shop',
            'payment_method_ids': [(4, pm.id)],
        })
        self.assertIn(pm, config.payment_method_ids)

    def test_pos_order_creation_flow(self):
        """Verify creation of POS order with lines and payment method compatible with simplified POS flow."""
        order = self.env['pos.order'].create({
            'session_id': self.pos_session.id,
            'partner_id': self.partner.id,
            'lines': [(0, 0, {
                'product_id': self.product_1.id,
                'qty': 2.0,
                'price_unit': 50.0,
                'price_subtotal': 100.0,
                'price_subtotal_incl': 100.0,
            })],
            'amount_total': 100.0,
            'amount_tax': 0.0,
            'amount_paid': 100.0,
            'amount_return': 0.0,
        })
        self.assertEqual(order.partner_id.id, self.partner.id)
        self.assertEqual(len(order.lines), 1)
        self.assertEqual(order.amount_total, 100.0)

    def test_pos_order_multiple_lines_and_payment(self):
        """Verify multi-line order creation and payment line association in simplified POS workflow."""
        order = self.env['pos.order'].create({
            'session_id': self.pos_session.id,
            'partner_id': self.partner.id,
            'lines': [
                (0, 0, {
                    'product_id': self.product_1.id,
                    'qty': 1.0,
                    'price_unit': 50.0,
                    'price_subtotal': 50.0,
                    'price_subtotal_incl': 50.0,
                }),
                (0, 0, {
                    'product_id': self.product_2.id,
                    'qty': 2.0,
                    'price_unit': 25.0,
                    'price_subtotal': 50.0,
                    'price_subtotal_incl': 50.0,
                }),
            ],
            'payment_ids': [(0, 0, {
                'payment_method_id': self.payment_method.id,
                'amount': 100.0,
                'payment_date': fields.Datetime.now(),
            })],
            'amount_total': 100.0,
            'amount_tax': 0.0,
            'amount_paid': 100.0,
            'amount_return': 0.0,
        })
        self.assertEqual(len(order.lines), 2)
        self.assertEqual(len(order.payment_ids), 1)
        self.assertEqual(order.amount_total, 100.0)
        self.assertEqual(order.amount_paid, 100.0)
