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
from datetime import date
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestTaxReport(TransactionCase):

    def test_month_name_is_abbreviated(self):
        month = self.env['tax.report'].get_month_name(date(2026, 11, 5))

        self.assertEqual(month, 'Nov')

    def test_report_returns_sales_and_purchase_sections(self):
        report = self.env['tax.report'].view_report()

        self.assertIn('sale', report)
        self.assertIn('purchase', report)
        self.assertIn('sale_total', report)
        self.assertIn('purchase_total', report)
