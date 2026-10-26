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
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestMobileBrand(TransactionCase):
    """Test suite for mobile.brand model (mobile_brand.py)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group_technician = cls.env.ref('mobile_service_shop.mobile_service_shop_group_user')
        cls.group_manager = cls.env.ref('mobile_service_shop.mobile_service_shop_group_manager')

        cls.tech_user = cls.env['res.users'].create({
            'name': 'Brand Tech User',
            'login': 'brand_tech_user',
            'email': 'brand_tech@example.com',
            'company_id': cls.env.company.id,
            'company_ids': [(6, 0, [cls.env.company.id])],
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id, cls.group_technician.id])],
        })

    def test_01_create_mobile_brand(self):
        """Test creating a mobile brand and verifying display name."""
        brand = self.env['mobile.brand'].create({'brand_name': 'Apple'})
        self.assertEqual(brand.brand_name, 'Apple')
        self.assertEqual(brand.display_name, 'Apple')

    def test_02_multiple_brands_listing(self):
        """Test listing multiple brands."""
        b1 = self.env['mobile.brand'].create({'brand_name': 'Samsung'})
        b2 = self.env['mobile.brand'].create({'brand_name': 'Google'})
        brands = self.env['mobile.brand'].search([('id', 'in', [b1.id, b2.id])])
        self.assertEqual(len(brands), 2)
        self.assertIn('Samsung', brands.mapped('brand_name'))
        self.assertIn('Google', brands.mapped('brand_name'))

    def test_03_technician_read_access(self):
        """Verify technician has read access to mobile.brand."""
        brand = self.env['mobile.brand'].create({'brand_name': 'OnePlus'})
        tech_brand = self.env['mobile.brand'].with_user(self.tech_user).browse(brand.id)
        self.assertEqual(tech_brand.brand_name, 'OnePlus')
