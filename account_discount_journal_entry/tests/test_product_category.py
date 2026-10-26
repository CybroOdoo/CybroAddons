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
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests.common import tagged


@tagged('post_install', '-at_install')
class TestProductCategory(AccountTestInvoicingCommon):
    """Unit tests for product.category discount account fields."""

    def test_product_category_discount_accounts(self):
        """Test setting and getting vendor and customer discount accounts."""
        company = self.env.company
        cust_acc = self.env['account.account'].create({
            'code': '999003',
            'name': 'Category Customer Discount',
            'account_type': 'expense',
            'company_ids': [Command.link(company.id)],
        })
        vend_acc = self.env['account.account'].create({
            'code': '999004',
            'name': 'Category Vendor Discount',
            'account_type': 'income_other',
            'company_ids': [Command.link(company.id)],
        })

        category = self.env['product.category'].create({
            'name': 'Test Discount Category',
            'customer_account_discount_id': cust_acc.id,
            'vendor_account_discount_id': vend_acc.id,
        })
        self.assertEqual(category.customer_account_discount_id, cust_acc)
        self.assertEqual(category.vendor_account_discount_id, vend_acc)

    def test_discount_accounts_are_company_dependent(self):
        """Test that discount accounts on product categories are company dependent."""
        other_company = self.setup_other_company()['company']
        account = self.env['account.account'].create({
            'code': '999005',
            'name': 'Company 1 Discount Account',
            'account_type': 'expense',
            'company_ids': [Command.link(self.company.id)],
        })
        category = self.env['product.category'].create({
            'name': 'Company Dependent Category',
            'customer_account_discount_id': account.id,
        })
        self.assertEqual(category.customer_account_discount_id, account)
        self.assertFalse(category.with_company(other_company).customer_account_discount_id)

