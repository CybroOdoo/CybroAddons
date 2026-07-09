# -*- coding: utf-8 -*-
from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import tagged
from .common import AccountKitCommon


@tagged('post_install', '-at_install')
class TestFxRevaluation(AccountKitCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        company = cls.env.company
        company.fx_reval_journal_id = cls.misc_journal
        company.fx_reval_gain_account_id = cls.company_data['default_account_revenue']
        company.fx_reval_loss_account_id = cls.expense_account
        cls.receivable = cls.company_data['default_account_receivable']
        # A foreign currency that loses value against the company currency.
        cls.foreign = cls.env['res.currency'].create({
            'name': 'FXX', 'symbol': 'F', 'rounding': 0.01})
        cls.env['res.currency.rate'].create([
            {'currency_id': cls.foreign.id, 'name': '2020-01-01',
             'rate': 2.0, 'company_id': company.id},
            {'currency_id': cls.foreign.id, 'name': '2020-06-01',
             'rate': 4.0, 'company_id': company.id},
        ])

    def _wizard(self, **kw):
        vals = {
            'date': '2020-06-01',
            'journal_id': self.misc_journal.id,
            'gain_account_id': self.company_data['default_account_revenue'].id,
            'loss_account_id': self.expense_account.id,
            'account_ids': [Command.set(self.receivable.ids)],
        }
        vals.update(kw)
        return self.env['account.fx.revaluation'].create(vals)

    def test_revaluation_books_unrealized_loss_and_reverses(self):
        """A foreign receivable that lost value books a loss + a reversal."""
        # 100 FXX invoice at rate 2.0 => 50 in company currency.
        self.init_invoice('out_invoice', partner=self.partner_a,
                          invoice_date='2020-01-01', amounts=[100.0],
                          taxes=[], currency=self.foreign, post=True)
        action = self._wizard().action_revaluate()
        moves = self.env['account.move'].browse(action['domain'][0][2])
        self.assertEqual(len(moves), 2, "Adjustment + reversal are created")
        self.assertEqual(set(moves.mapped('state')), {'posted'})
        adjustment = moves.filtered(lambda m: 'Reversal' not in (m.ref or ''))
        self.assertAlmostEqual(sum(adjustment.line_ids.mapped('debit')),
                               sum(adjustment.line_ids.mapped('credit')), 2,
                               "The revaluation entry balances")
        # At 2020-06-01 the 100 FXX is worth 25 (rate 4.0) vs 50 booked -> loss 25.
        loss_line = adjustment.line_ids.filtered(
            lambda l: l.account_id == self.expense_account)
        self.assertTrue(loss_line, "An unrealized loss line is booked")
        self.assertAlmostEqual(loss_line.debit, 25.0, 2)

    def test_revaluation_without_config_or_balances(self):
        """No open foreign balances -> the wizard reports nothing to do."""
        with self.assertRaises(UserError):
            self._wizard().action_revaluate()

    def test_no_auto_reverse_single_move(self):
        """With auto-reverse off, only the adjustment entry is posted."""
        self.init_invoice('out_invoice', partner=self.partner_a,
                          invoice_date='2020-01-01', amounts=[100.0],
                          taxes=[], currency=self.foreign, post=True)
        action = self._wizard(auto_reverse=False).action_revaluate()
        moves = self.env['account.move'].browse(action['domain'][0][2])
        self.assertEqual(len(moves), 1)
