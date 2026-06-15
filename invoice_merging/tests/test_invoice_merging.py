# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Akhil Ashok(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo.tests.common import TransactionCase


class TestInvoiceMerging(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner = cls.env['res.partner'].create({
            'name': 'Merge Customer',
        })
        cls.income_account = cls.env['account.account'].search([
            ('company_id', '=', cls.env.company.id),
            ('account_type', '=', 'income'),
        ], limit=1)
        if not cls.income_account:
            cls.income_account = cls.env['account.account'].search([
                ('company_id', '=', cls.env.company.id),
                ('deprecated', '=', False),
            ], limit=1)

        cls.invoice_1 = cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': cls.partner.id,
            'invoice_line_ids': [(0, 0, {
                'name': 'Invoice Line 1',
                'quantity': 1,
                'price_unit': 100.0,
                'account_id': cls.income_account.id,
            })],
        })
        cls.invoice_2 = cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': cls.partner.id,
            'invoice_line_ids': [(0, 0, {
                'name': 'Invoice Line 2',
                'quantity': 1,
                'price_unit': 200.0,
                'account_id': cls.income_account.id,
            })],
        })

    def test_action_merge_invoice_opens_wizard(self):
        action = self.invoice_1.action_merge_invoice()

        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'merge.invoice')
        self.assertEqual(action['target'], 'new')
        self.assertEqual(action['view_mode'], 'form')

        wizard = self.env['merge.invoice'].browse(action['res_id'])
        self.assertEqual(wizard.invoice_ids, self.invoice_1)

    def test_merge_invoice_cancels_source_and_updates_target_reference(self):
        wizard = self.env['merge.invoice'].create({
            'invoice_ids': [(6, 0, [self.invoice_1.id, self.invoice_2.id])],
            'target_invoice_id': self.invoice_1.id,
            'merge_type': 'cancel',
        })

        wizard.action_merge_invoice()

        self.assertEqual(
            self.invoice_1.payment_reference,
            f'Merged (Draft {self.invoice_1.id}, Draft {self.invoice_2.id})'
        )
        self.assertEqual(self.invoice_2.state, 'cancel')
