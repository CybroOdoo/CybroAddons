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
import base64
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestWebsiteProductCustomization(TransactionCase):
    """Unit tests for the Website Product Customization module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # 1x1 transparent PNG image in base64 string
        cls.sample_image = (
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk'
            '+A8AAQUBAScY42YAAAAASUVORK5CYII='
        )

        cls.design = cls.env['product.design'].create({
            'name': 'Sample T-Shirt Design',
            'product_design': cls.sample_image,
        })

        cls.partner = cls.env['res.partner'].create({
            'name': 'Customization Test Customer',
        })

        cls.product = cls.env['product.product'].create({
            'name': 'Customizable T-Shirt',
            'list_price': 25.0,
            'image_1920': cls.sample_image,
        })

        # Internal user
        cls.internal_user = cls.env['res.users'].create({
            'name': 'Internal User',
            'login': 'custom_internal_user',
            'email': 'internal@example.com',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])],
        })

        # Portal user
        cls.portal_user = cls.env['res.users'].create({
            'name': 'Portal User',
            'login': 'custom_portal_user',
            'email': 'portal@example.com',
            'group_ids': [(6, 0, [cls.env.ref('base.group_portal').id])],
        })

        # Public user (anonymous shopper)
        cls.public_user = cls.env.ref('base.public_user')

    def test_product_design_creation(self):
        """Test that product.design records store name and image correctly."""
        self.assertEqual(self.design.name, 'Sample T-Shirt Design')
        self.assertTrue(self.design.product_design)

    def test_product_design_public_access(self):
        """Test that public (anonymous) shoppers have read access to designs."""
        designs = self.env['product.design'].with_user(self.public_user).search([])
        self.assertIn(self.design, designs)
        # Verify reading design fields does not raise AccessError
        design_data = designs.read(['name', 'product_design'])
        self.assertTrue(len(design_data) > 0)

    def test_product_design_portal_access(self):
        """Test that portal shoppers have read access to designs."""
        designs = self.env['product.design'].with_user(self.portal_user).search([])
        self.assertIn(self.design, designs)
        design_data = designs.read(['name', 'product_design'])
        self.assertTrue(len(design_data) > 0)

    def test_product_design_public_cannot_modify(self):
        """Test that public shoppers cannot create, write, or delete designs."""
        with self.assertRaises(AccessError):
            self.env['product.design'].with_user(self.public_user).create({
                'name': 'Unauthorized Design',
            })

        with self.assertRaises(AccessError):
            self.design.with_user(self.public_user).write({
                'name': 'Modified Design',
            })

        with self.assertRaises(AccessError):
            self.design.with_user(self.public_user).unlink()

    def test_product_design_internal_user_crud(self):
        """Test that internal users have full CRUD access on product.design."""
        design = self.env['product.design'].with_user(self.internal_user).create({
            'name': 'Internal Created Design',
            'product_design': self.sample_image,
        })
        self.assertEqual(design.name, 'Internal Created Design')

        design.write({'name': 'Updated Design'})
        self.assertEqual(design.name, 'Updated Design')

        design_id = design.id
        design.unlink()
        self.assertFalse(self.env['product.design'].browse(design_id).exists())

    def test_standard_sale_order_line_no_custom_design(self):
        """Test that standard sale order lines do not set product_design or is_customized_product."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        line = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product.id,
            'product_uom_qty': 1,
            'price_unit': 25.0,
        })

        # Ensure product_design is NOT copied from product image_1920
        self.assertFalse(line.product_design)
        self.assertFalse(line.is_customized_product)

    def test_customized_sale_order_line(self):
        """Test that customized sale order lines properly store the custom design."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        custom_design_data = base64.b64encode(b'custom_canvas_image_data').decode('utf-8')
        line = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product.id,
            'product_uom_qty': 1,
            'price_unit': 25.0,
            'product_design': custom_design_data,
            'is_customized_product': True,
        })

        self.assertTrue(line.is_customized_product)
        self.assertTrue(line.product_design)
