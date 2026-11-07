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
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestMrpSubstituteProduct(TransactionCase):
    """ Test suite for MRP substitute products functionality. """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.stock_location = cls.env.ref('stock.stock_location_stock')

        # Create finished product
        cls.finished_product = cls.env['product.product'].create({
            'name': 'Finished Table',
            'is_storable': True,
        })

        # Create primary component (storable)
        cls.primary_component = cls.env['product.product'].create({
            'name': 'Wood Table Leg',
            'is_storable': True,
        })

        # Create substitute component (storable)
        cls.substitute_component = cls.env['product.product'].create({
            'name': 'Steel Table Leg',
            'is_storable': True,
        })

        # Create service substitute component
        cls.service_substitute = cls.env['product.product'].create({
            'name': 'Assembly Service Sub',
            'type': 'service',
        })

        # Create secondary component without substitute
        cls.secondary_component = cls.env['product.product'].create({
            'name': 'Screw Component',
            'is_storable': True,
        })

        # Create BOM
        cls.bom = cls.env['mrp.bom'].create({
            'product_tmpl_id': cls.finished_product.product_tmpl_id.id,
            'product_id': cls.finished_product.id,
            'product_qty': 1.0,
            'type': 'normal',
            'bom_line_ids': [
                (0, 0, {
                    'product_id': cls.primary_component.id,
                    'product_qty': 4.0,
                    'mrp_substitute_product_id': cls.substitute_component.id,
                }),
                (0, 0, {
                    'product_id': cls.secondary_component.id,
                    'product_qty': 8.0,
                }),
            ],
        })

    def test_substitute_when_primary_out_of_stock(self):
        """ Test that substitute product is used when primary component is out of stock. """
        self.assertEqual(self.primary_component.free_qty, 0)
        self.env['stock.quant']._update_available_quantity(
            self.substitute_component, self.stock_location, 20.0,
        )
        self.assertGreaterEqual(self.substitute_component.free_qty, 4.0)

        mo = self.env['mrp.production'].create({
            'product_id': self.finished_product.id,
            'product_qty': 1.0,
            'bom_id': self.bom.id,
        })
        mo.action_confirm()

        raw_products = mo.move_raw_ids.mapped('product_id')
        self.assertIn(self.substitute_component, raw_products,
                      "Substitute product should be used when primary component is out of stock")
        self.assertNotIn(self.primary_component, raw_products,
                         "Primary component should not be in raw moves when substituted")

    def test_no_substitute_when_primary_in_stock(self):
        """ Test that primary component is preserved when it has available stock. """
        self.env['stock.quant']._update_available_quantity(
            self.primary_component, self.stock_location, 10.0,
        )
        self.env['stock.quant']._update_available_quantity(
            self.substitute_component, self.stock_location, 20.0,
        )

        mo = self.env['mrp.production'].create({
            'product_id': self.finished_product.id,
            'product_qty': 1.0,
            'bom_id': self.bom.id,
        })
        mo.action_confirm()

        raw_products = mo.move_raw_ids.mapped('product_id')
        self.assertIn(self.primary_component, raw_products,
                      "Primary component should be preserved when stock is available")
        self.assertNotIn(self.substitute_component, raw_products,
                         "Substitute product should not be used when primary component is in stock")

    def test_service_substitute_skipped(self):
        """ Test that service-type substitute products are skipped. """
        bom_line = self.bom.bom_line_ids.filtered(lambda line: line.product_id == self.primary_component)
        bom_line.write({'mrp_substitute_product_id': self.service_substitute.id})

        mo = self.env['mrp.production'].create({
            'product_id': self.finished_product.id,
            'product_qty': 1.0,
            'bom_id': self.bom.id,
        })
        mo.action_confirm()

        raw_products = mo.move_raw_ids.mapped('product_id')
        self.assertIn(self.primary_component, raw_products,
                      "Service substitute should be skipped and primary component retained")
        self.assertNotIn(self.service_substitute, raw_products)

    def test_substitute_insufficient_stock(self):
        """ Test that substitution does not occur if substitute has insufficient quantity. """
        self.bom.bom_line_ids.filtered(
            lambda line: line.product_id == self.primary_component,
        ).write({'mrp_substitute_product_id': self.substitute_component.id})

        quant = self.env['stock.quant'].search([
            ('product_id', '=', self.substitute_component.id),
            ('location_id', '=', self.stock_location.id),
        ])
        if quant:
            quant.write({'quantity': 2.0})
        else:
            self.env['stock.quant']._update_available_quantity(
                self.substitute_component, self.stock_location, 2.0,
            )

        mo = self.env['mrp.production'].create({
            'product_id': self.finished_product.id,
            'product_qty': 1.0,
            'bom_id': self.bom.id,
        })
        mo.action_confirm()

        raw_products = mo.move_raw_ids.mapped('product_id')
        self.assertIn(self.primary_component, raw_products,
                      "Primary component should be retained when substitute has insufficient stock")

    def test_security_group_exists(self):
        """ Test that the substitute product security group is properly defined. """
        group = self.env.ref('substitute_product_in_mrp.mrp_substitute_product_group', raise_if_not_found=False)
        self.assertTrue(group, "Security group mrp_substitute_product_group must exist")
        self.assertIn(group.name, ['Allow Substitute Product (MRP)', 'Allow Substitute Product(MRP)'])

    def test_res_users_group_change_bus_notification(self):
        """ Test that modifying user group_ids triggers bus notification for cache clearing. """
        from odoo.fields import Command
        user = self.env['res.users'].create({
            'name': 'Test MRP User',
            'login': 'test_mrp_user_coverage_test',
            'email': 'test_mrp_user_cov@example.com',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])],
        })
        group = self.env.ref('substitute_product_in_mrp.mrp_substitute_product_group')
        # Grant the substitute group
        user.write({'group_ids': [Command.link(group.id)]})
        self.assertTrue(user.has_group('substitute_product_in_mrp.mrp_substitute_product_group'))
        # Revoke the substitute group
        user.write({'group_ids': [Command.unlink(group.id)]})
        self.assertFalse(user.has_group('substitute_product_in_mrp.mrp_substitute_product_group'))
