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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestAccountReportPartnerLedger(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Wizard Partner'
        })
        cls.company = cls.env.company
        cls.wizard = cls.env['account.report.partner.ledger'].create({
            'company_id': cls.company.id,
            'partner_ids': [(6, 0, cls.partner.ids)],
            'include_initial_balance': True,
        })

    def test_print_report(self):
        """Test the _print_report method to ensure it updates data and returns an action."""
        data = {'form': {}}
        action = self.wizard._print_report(data)

        self.assertEqual(data['form'].get('partner_ids'), self.partner.ids)
        self.assertTrue(data['form'].get('initial_balance'))
        self.assertIn('reconciled', data['form'])
        self.assertIn('amount_currency', data['form'])
        self.assertIn(action.get('type'), ['ir.actions.report', 'ir.actions.act_window'])
