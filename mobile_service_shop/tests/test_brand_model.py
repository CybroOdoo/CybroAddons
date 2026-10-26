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
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestBrandModel(TransactionCase):
    """Test suite for brand.model model (brand_model.py)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.brand = cls.env['mobile.brand'].create({'brand_name': 'Xiaomi'})
        cls.group_technician = cls.env.ref('mobile_service_shop.mobile_service_shop_group_user')

        cls.tech_user = cls.env['res.users'].create({
            'name': 'Model Tech User',
            'login': 'model_tech_user',
            'email': 'model_tech@example.com',
            'company_id': cls.env.company.id,
            'company_ids': [(6, 0, [cls.env.company.id])],
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id, cls.group_technician.id])],
        })

    def test_01_create_brand_model(self):
        """Test creating a brand model and verifying relationships."""
        model = self.env['brand.model'].create({
            'mobile_brand_name': self.brand.id,
            'mobile_brand_models': 'Redmi Note 13 Pro',
        })
        self.assertEqual(model.mobile_brand_name.id, self.brand.id)
        self.assertEqual(model.mobile_brand_models, 'Redmi Note 13 Pro')
        self.assertEqual(model.display_name, 'Redmi Note 13 Pro')

    def test_02_model_filtering_by_brand(self):
        """Test filtering models belonging to a specific brand."""
        brand_sony = self.env['mobile.brand'].create({'brand_name': 'Sony'})
        m1 = self.env['brand.model'].create({
            'mobile_brand_name': self.brand.id,
            'mobile_brand_models': 'Poco X6',
        })
        m2 = self.env['brand.model'].create({
            'mobile_brand_name': brand_sony.id,
            'mobile_brand_models': 'Xperia 1 VI',
        })

        xiaomi_models = self.env['brand.model'].search([('mobile_brand_name', '=', self.brand.id)])
        self.assertIn(m1.id, xiaomi_models.ids)
        self.assertNotIn(m2.id, xiaomi_models.ids)

    def test_03_technician_read_access(self):
        """Verify technician has read access to brand models."""
        model = self.env['brand.model'].create({
            'mobile_brand_name': self.brand.id,
            'mobile_brand_models': 'Mi 14 Ultra',
        })
        tech_model = self.env['brand.model'].with_user(self.tech_user).browse(model.id)
        self.assertEqual(tech_model.mobile_brand_models, 'Mi 14 Ultra')
