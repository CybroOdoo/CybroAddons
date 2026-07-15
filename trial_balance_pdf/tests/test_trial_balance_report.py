# -*- coding: utf-8 -*-

#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Chethana Ramachandran(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests.common import TransactionCase
from odoo import fields

class TestTrialBalanceReport(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company = cls.env.company

        cls.journal = cls.env['account.journal'].search(
            [('type', '=', 'general')],
            limit=1
        )

        cls.account = cls.env['account.account'].search(
            [('company_id', '=', cls.company.id)],
            limit=1
        )

        cls.move = cls.env['account.move'].create({
            'move_type': 'entry',
            'journal_id': cls.journal.id,
            'date': fields.Date.today(),
            'line_ids': [
                (0, 0, {
                    'name': 'Debit Line',
                    'account_id': cls.account.id,
                    'debit': 500.0,
                    'credit': 0.0,
                }),
                (0, 0, {
                    'name': 'Credit Line',
                    'account_id': cls.account.id,
                    'debit': 0.0,
                    'credit': 500.0,
                }),
            ]
        })

        cls.move.action_post()


    def test_trial_balance_pdf_report(self):
        """Test PDF report generation"""

        wizard = self.env['trial.balance.report'].create({
            'start_date': fields.Date.today(),
            'end_date': fields.Date.today(),
            'company_id': self.company.id,
            'state': 'posted',
            'journals_ids': [(6, 0, [self.journal.id])]
        })

        self.assertTrue(wizard)

        result = wizard.button_to_get_pdf()


        self.assertTrue(result)
        self.assertEqual(
            result.get('type'),
            'ir.actions.report'
        )
