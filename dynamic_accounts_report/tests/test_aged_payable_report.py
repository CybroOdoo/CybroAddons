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
class TestAgedPayableReport(TransactionCase):

    def test_report_contains_partner_totals_section(self):
        report = self.env['age.payable.report'].view_report()

        self.assertIn('partner_totals', report)
        self.assertIsInstance(report['partner_totals'], dict)

    def test_filter_without_partner_returns_report_structure(self):
        report = self.env['age.payable.report'].get_filter_values(False, [])

        self.assertIn('partner_totals', report)
