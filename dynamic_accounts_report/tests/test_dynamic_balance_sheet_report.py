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
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestDynamicBalanceSheetReport(TransactionCase):

    def test_month_filter_sets_current_month_dates(self):
        report = self.env['dynamic.balance.sheet.report'].create({})

        filters = report.filter('month')

        self.assertEqual(len(filters), 0)
        self.assertTrue(report.date_from)
        self.assertTrue(report.date_to)
        self.assertLessEqual(report.date_from, report.date_to)

    def test_create_applies_default_company_and_posted_target(self):
        report = self.env['dynamic.balance.sheet.report'].create({})

        self.assertEqual(report.company_id, self.env.company)
        self.assertEqual(report.target_move, 'posted')
