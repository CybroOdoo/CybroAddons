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
class TestAccountPartnerLedger(TransactionCase):

    def test_report_groups_lines_by_partner_and_returns_totals(self):
        company = self.env.company
        if not company.account_opening_date:
            company.account_opening_date = '2026-01-01'

        report = self.env['account.partner.ledger'].view_report(False, False)

        self.assertIn('partner_totals', report)
        self.assertIsInstance(report['partner_totals'], dict)
