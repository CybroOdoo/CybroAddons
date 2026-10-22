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
"""Test suite for res.partner.category model extension."""
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestResPartnerCategory(TransactionCase):
    """Test suite covering res.partner.category POS data fields and loading."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pos_config = cls.env['pos.config'].search([], limit=1)
        if not cls.pos_config:
            cls.pos_config = cls.env['pos.config'].create({'name': 'Test POS Config'})
        cls.tag_vip = cls.env['res.partner.category'].create({
            'name': 'VIP',
        })
        cls.tag_retail = cls.env['res.partner.category'].create({
            'name': 'Retail',
        })

    def test_load_pos_data_fields(self):
        """Test that res.partner.category._load_pos_data_fields returns ['id', 'name']."""
        fields = self.env['res.partner.category']._load_pos_data_fields(self.pos_config)
        self.assertIn('id', fields, "'id' must be in res.partner.category POS data fields.")
        self.assertIn('name', fields, "'name' must be in res.partner.category POS data fields.")

    def test_search_read_pos_fields(self):
        """Test searching and reading categories with fields specified for POS."""
        fields = self.env['res.partner.category']._load_pos_data_fields(self.pos_config)
        tags = self.env['res.partner.category'].search_read(
            [('id', 'in', [self.tag_vip.id, self.tag_retail.id])],
            fields,
        )
        self.assertEqual(len(tags), 2)
        tag_names = {tag['name'] for tag in tags}
        self.assertEqual(tag_names, {'VIP', 'Retail'})
        for tag in tags:
            self.assertIn('id', tag)
            self.assertIn('name', tag)
