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
"""Test suite for res.partner model extension."""
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestResPartner(TransactionCase):
    """Test suite covering res.partner POS data fields and image/category assignment."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pos_config = cls.env['pos.config'].search([], limit=1)
        if not cls.pos_config:
            cls.pos_config = cls.env['pos.config'].create({'name': 'Test POS Config'})
        cls.category = cls.env['res.partner.category'].create({
            'name': 'VIP Partner',
        })
        # Standard 1x1 transparent GIF base64 string
        cls.sample_image = "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
        cls.partner = cls.env['res.partner'].create({
            'name': 'POS Test Customer',
            'email': 'pos_test@example.com',
            'image_1920': cls.sample_image,
            'category_id': [(6, 0, cls.category.ids)],
        })

    def test_load_pos_data_fields_contains_category_id(self):
        """Test that res.partner._load_pos_data_fields includes 'category_id'."""
        partner_fields = self.env['res.partner']._load_pos_data_fields(self.pos_config)
        self.assertIn(
            'category_id',
            partner_fields,
            "category_id must be included in the partner POS fields."
        )

    def test_load_pos_data_fields_preserves_base_fields(self):
        """Test that default partner fields are retained in _load_pos_data_fields."""
        partner_fields = self.env['res.partner']._load_pos_data_fields(self.pos_config)
        self.assertIn('name', partner_fields)
        self.assertIn('id', partner_fields)
        self.assertIn('email', partner_fields)
        self.assertIn('phone', partner_fields)

    def test_partner_image_and_category_assignment(self):
        """Test partner has image_1920 and category_id properly assigned."""
        self.assertTrue(self.partner.image_1920, "Customer image_1920 should be set.")
        self.assertIn(self.category, self.partner.category_id, "Customer should have the assigned category.")
