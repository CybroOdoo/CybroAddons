# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from datetime import timedelta

from dateutil.relativedelta import relativedelta

from odoo import Command
from odoo.tests import tagged

from .common import AccountingKitTestCommon


@tagged('post_install', '-at_install')
class TestFxRightsReconcile(AccountingKitTestCommon):
    """FX revaluation, access rights and the reconciliation widget (P1.11)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.eur = cls.env.ref('base.EUR')
        cls.eur.active = True
        cls.d1, cls.d2 = cls.ymd(1, 10), cls.ymd(2, 28)
        cls.env['res.currency.rate'].create([
            {'currency_id': cls.eur.id, 'rate': 0.5, 'name': cls.d1 - timedelta(days=30), 'company_id': cls.company.id},
            {'currency_id': cls.eur.id, 'rate': 0.4, 'name': cls.d2 - timedelta(days=1), 'company_id': cls.company.id}])
        cls.customer = cls.env['res.partner'].create({'name': 'Kit FX Customer'})
        cls.eur_bank = cls.env['account.journal'].create({
            'name': 'Kit Bank EUR', 'type': 'bank', 'code': 'KBEUR', 'currency_id': cls.eur.id})

    def eur_invoice(self, partner, amount, day, move_type='out_invoice'):
        move = self.env['account.move'].create({
            'move_type': move_type, 'partner_id': partner.id, 'currency_id': self.eur.id, 'invoice_date': day,
            'invoice_line_ids': [Command.create({'name': 'x', 'quantity': 1, 'price_unit': amount,
                                                 'tax_ids': [Command.clear()]})]})
        move.action_post()
        return move

    def make_user(self, login, group):
        return self.env['res.users'].create({
            'name': login, 'login': login, 'group_ids': [(6, 0, [self.env.ref(group).id])],
            'company_id': self.company.id, 'company_ids': [(6, 0, self.company.ids)]})

    def statement_line(self, amount, partner=None, journal=None):
        return self.env['account.bank.statement.line'].create({
            'journal_id': (journal or self.kit_journal('bank')).id, 'date': self.d2,
            'payment_ref': 'L%s' % amount, 'amount': amount, 'partner_id': partner.id if partner else False})

    # ------------------------------------------------------------------ FX
    def test_fx_revaluation(self):
        """Receivables are revalued per partner, foreign-currency bank
        accounts too, later invoices are left out; the entry carries the
        partner and is reversed the next day."""
        income = self.kit_account('income')
        invoice = self.eur_invoice(self.customer, 100, self.d1)
        receivable = invoice.line_ids.filtered(lambda l: l.account_id.account_type == 'asset_receivable').account_id
        self.eur_invoice(self.customer, 40, self.d2 + timedelta(days=5))
        bank_account = self.eur_bank.default_account_id
        self.env['account.move'].create({
            'move_type': 'entry', 'date': self.d1, 'journal_id': self.kit_journal('general').id,
            'line_ids': [Command.create({'account_id': bank_account.id, 'currency_id': self.eur.id,
                                         'amount_currency': 100, 'balance': 200, 'name': 'in'}),
                         Command.create({'account_id': income.id, 'currency_id': self.eur.id,
                                         'amount_currency': -100, 'balance': -200, 'name': 'in'})]}).action_post()
        gain = self.env['account.account'].create({'name': 'Kit FX gain', 'code': 'KFXG', 'account_type': 'income_other'})
        loss = self.env['account.account'].create({'name': 'Kit FX loss', 'code': 'KFXL', 'account_type': 'expense'})
        wizard = self.env['account.fx.revaluation'].create({
            'date': self.d2, 'journal_id': self.kit_journal('general').id,
            'gain_account_id': gain.id, 'loss_account_id': loss.id, 'auto_reverse': True})
        self.env.flush_all()
        adjustments = wizard._get_revaluation_lines()
        self.assertTrue(any(k[0] == receivable and k[1] == self.customer and abs(v - 50) < 0.005
                            for k, v in adjustments.items()))
        self.assertTrue(any(k[0] == bank_account and abs(v - 50) < 0.005 for k, v in adjustments.items()))
        self.assertFalse(any(k[0] == receivable and abs(v - 70) < 0.005 for k, v in adjustments.items()))
        moves = self.env['account.move'].search(wizard.action_revaluate()['domain'], order='date')
        line = moves[0].line_ids.filtered(lambda l: l.account_id == receivable)
        self.assertEqual((line.partner_id, line.currency_id, line.amount_currency), (self.customer, self.eur, 0))
        self.assertAmount(line.balance, 50)
        self.assertAmount(moves[0].line_ids.filtered(lambda l: l.account_id == gain).balance, -100)
        self.assertEqual(moves[0].state, 'posted')
        self.assertEqual(moves[1].date, self.d2 + timedelta(days=1))

    # ------------------------------------------------------------------ Rights
    def test_access_rights(self):
        """Invoicing users print invoice copies; accountants manage assets;
        Chief Accountant no longer implies Administrator."""
        invoice = self.eur_invoice(self.customer, 100, self.d1)
        invoicing = self.make_user('kit_inv', 'account.group_account_invoice')
        self.kit_journal('sale').with_user(invoicing).multiple_invoice_ids.read(['id'])
        report = self.env.ref('base_accounting_kit.report_multiple_invoice_copies')
        report.with_user(invoicing)._render_qweb_html(report.report_name, invoice.ids)
        accountant = self.make_user('kit_accu', 'account.group_account_user')
        category = self.env['account.asset.category'].create({
            'name': 'Kit rights', 'company_id': self.company.id, 'price': 0,
            'account_asset_id': self.kit_account('asset_fixed').id,
            'account_depreciation_id': self.kit_account('asset_non_current').id,
            'account_depreciation_expense_id': self.kit_account('expense_depreciation').id,
            'journal_id': self.kit_journal('general').id, 'method_number': 12, 'method_period': 1})
        Asset = self.env['account.asset.asset']
        values = {'name': 'Kit rights asset', 'category_id': category.id, 'value': 1200,
                  'date': (self.today - relativedelta(months=2)).replace(day=1)}
        values.update(Asset.onchange_category_id_values(category.id)['value'])
        asset = Asset.create(values).with_user(accountant)
        asset.compute_depreciation_board()
        asset.validate()
        self.env['asset.modify'].with_user(accountant).with_context(active_id=asset.id).create(
            {'name': 'x', 'method_number': 18, 'method_period': 1}).modify()
        asset.pause()
        self.assertEqual(asset.state, 'paused')
        chief = self.env.ref('base_accounting_kit.group_account_chief')
        self.assertNotIn(self.env.ref('account.group_account_manager'), chief.implied_ids)
        chief_user = self.make_user('kit_chief', 'base_accounting_kit.group_account_chief')
        self.assertFalse(chief_user.has_group('account.group_account_manager'))
        self.assertTrue(chief_user.has_group('account.group_account_user'))

    # ------------------------------------------------------------------ Widget
    def test_manual_operation(self):
        """A manual operation applies its tax and analytic and reconciles."""
        expense = self.kit_account('expense')
        plan = self.env['account.analytic.plan'].create({'name': 'Kit rec plan'})
        analytic = self.env['account.analytic.account'].create({'name': 'Dept', 'plan_id': plan.id})
        line = self.statement_line(-115)
        line.write({'account_id': expense.id, 'tax_ids': [Command.set(self.tax_purchase_a.ids)],
                    'analytic_distribution': {str(analytic.id): 100}})
        line.button_validation()
        items = line.move_id.line_ids
        base = items.filtered(lambda l: l.account_id == expense)
        self.assertAmount(base.balance, 100)
        self.assertEqual(base.analytic_distribution, {str(analytic.id): 100})
        self.assertEqual(len(items.filtered('tax_repartition_line_id')), 1)
        self.assertAmount(sum(items.mapped('balance')), 0)
        self.assertTrue(line.is_reconciled)

    def test_reconcile_models(self):
        """Reconcile models apply all their lines (percentages, fixed fee,
        analytic, label); a partial model leaves the rest open."""
        acc_a = self.env['account.account'].create({'name': 'Kit A', 'code': 'KRA', 'account_type': 'income'})
        acc_b = self.env['account.account'].create({'name': 'Kit B', 'code': 'KRB', 'account_type': 'income_other'})
        fees = self.env['account.account'].create({'name': 'Kit fees', 'code': 'KRF', 'account_type': 'expense'})
        Model = self.env['account.reconcile.model']
        split = Model.create({'name': 'Kit split', 'line_ids': [
            Command.create({'account_id': acc_a.id, 'amount_type': 'percentage', 'amount_string': '80'}),
            Command.create({'account_id': acc_b.id, 'amount_type': 'percentage', 'amount_string': '100', 'label': 'Rest'})]})
        line = self.statement_line(1000)
        line.action_apply_reconcile_model(split.id)
        items = line.move_id.line_ids
        self.assertAmount(items.filtered(lambda l: l.account_id == acc_a).balance, -800)
        rest = items.filtered(lambda l: l.account_id == acc_b)
        self.assertAmount(rest.balance, -200)
        self.assertEqual(rest.name, 'Rest')
        self.assertTrue(line.is_reconciled)
        fee = Model.create({'name': 'Kit fee', 'line_ids': [
            Command.create({'account_id': fees.id, 'amount_type': 'fixed', 'amount_string': '-10'}),
            Command.create({'account_id': acc_a.id, 'amount_type': 'percentage', 'amount_string': '100'})]})
        line = self.statement_line(990)
        line.action_apply_reconcile_model(fee.id)
        self.assertAmount(line.move_id.line_ids.filtered(lambda l: l.account_id == fees).balance, 10)
        half = Model.create({'name': 'Kit half', 'line_ids': [
            Command.create({'account_id': acc_a.id, 'amount_type': 'percentage', 'amount_string': '50'})]})
        line = self.statement_line(300)
        line.action_apply_reconcile_model(half.id)
        self.assertFalse(line.is_reconciled)

    def test_auto_reconcile_foreign_currency(self):
        """A 100 EUR payment is matched with the 100 EUR invoice."""
        partner = self.env['res.partner'].create({'name': 'Kit EUR Customer'})
        invoice = self.eur_invoice(partner, 100, self.d2)
        self.eur_invoice(partner, 100, self.d2, move_type='out_refund')
        line = self.statement_line(100, partner, self.eur_bank)
        proposal = line._get_reconcile_proposal()
        self.assertEqual([line for line, _amount in proposal.get('items', [])],
                         [*invoice.line_ids.filtered(lambda l: l.account_id.account_type == 'asset_receivable')])
