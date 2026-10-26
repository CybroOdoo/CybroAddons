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
"""Test suite for goods.type model."""
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestGoodsType(TransactionCase):
    """Test cases for the goods.type model."""

    def test_create_goods_type(self):
        """Test creating a goods type and verify defaults."""
        goods_type = self.env['goods.type'].create({
            'name': 'Household Furniture',
        })
        self.assertEqual(goods_type.name, 'Household Furniture')
        self.assertEqual(goods_type.company_id, self.env.company)

    def test_goods_type_custom_company(self):
        """Test creating a goods type with a specific company."""
        company = self.env['res.company'].create({'name': 'Test Logistics Co'})
        goods_type = self.env['goods.type'].create({
            'name': 'Electronics',
            'company_id': company.id,
        })
        self.assertEqual(goods_type.company_id, company)
