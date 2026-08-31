# -*- coding: utf-8 -*-

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestAccountMoveQuickbooksFields(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.journal = cls.env['account.journal'].search([
            ('type', '=', 'general'),
        ], limit=1)
        if not cls.journal:
            cls.journal = cls.env['account.journal'].create({
                'name': 'QuickBooks Test Journal',
                'code': 'QBT',
                'type': 'general',
            })
        cls.account = cls.env['account.account'].create({
            'name': 'QuickBooks Test Account',
            'code': 'QBT100',
            'account_type': 'asset_current',
        })

    def test_quickbooks_fields_can_be_written_and_read(self):
        move = self.env['account.move'].create({
            'move_type': 'entry',
            'journal_id': self.journal.id,
            'line_ids': [
                (0, 0, {
                    'name': 'Debit',
                    'account_id': self.account.id,
                    'debit': 10.0,
                    'credit': 0.0,
                }),
                (0, 0, {
                    'name': 'Credit',
                    'account_id': self.account.id,
                    'debit': 0.0,
                    'credit': 10.0,
                }),
            ],
        })

        move.write({
            'qbooks_invoice': 'INV-100',
            'qbooks_bill': 'BILL-200',
            'qbooks_credit': 'CR-300',
            'qbooks_refund': 'RF-400',
            'qbooks_sync_token': '9',
        })

        self.assertEqual(move.qbooks_invoice, 'INV-100')
        self.assertEqual(move.qbooks_bill, 'BILL-200')
        self.assertEqual(move.qbooks_credit, 'CR-300')
        self.assertEqual(move.qbooks_refund, 'RF-400')
        self.assertEqual(move.qbooks_sync_token, '9')
