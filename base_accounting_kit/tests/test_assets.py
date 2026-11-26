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
from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import AccountingKitTestCommon


@tagged('post_install', '-at_install')
class TestAssets(AccountingKitTestCommon):
    """Asset depreciation board (P1.8): entries posted when due with their
    amount, modify, revaluation, pause / resume, disposal, grouped entries,
    foreign currency, assets created from vendor bills."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        plan = cls.env['account.analytic.plan'].create({'name': 'Kit asset plan'})
        cls.analytic = cls.env['account.analytic.account'].create({'name': 'Kit asset analytic', 'plan_id': plan.id})
        cls.Asset = cls.env['account.asset.asset']
        cls.category = cls.make_category('Monthly', account_analytic_id=cls.analytic.id)

    @classmethod
    def make_category(cls, name, **vals):
        return cls.env['account.asset.category'].create(dict({
            'name': name, 'company_id': cls.company.id, 'price': 0,
            'account_asset_id': cls.kit_account('asset_fixed').id,
            'account_depreciation_id': cls.kit_account('asset_non_current').id,
            'account_depreciation_expense_id': cls.kit_account('expense_depreciation').id,
            'account_disposal_id': cls.kit_account('expense').id,
            'journal_id': cls.kit_journal('general').id,
            'method': 'linear', 'method_time': 'number', 'method_number': 12,
            'method_period': 1, 'type': 'purchase'}, **vals))

    def make_asset(self, category, value, start, **vals):
        values = {'name': 'Kit asset', 'category_id': category.id, 'value': value, 'date': start,
                  'company_id': self.company.id, 'currency_id': self.company.currency_id.id}
        values.update(self.Asset.onchange_category_id_values(category.id)['value'])
        values.update(vals)
        return self.Asset.create(values)

    def months_back(self, months):
        return (self.today - relativedelta(months=months)).replace(day=1)

    @staticmethod
    def posted(asset):
        return asset.depreciation_line_ids.filtered('move_posted_check')

    # ------------------------------------------------------------------
    def test_board_and_validate(self):
        """Validating posts only the due lines, with their amount and the
        analytic; no future draft entries; the books match the board;
        Generate Entries creates the next due line."""
        asset = self.make_asset(self.category, 1200, self.months_back(3))
        asset.compute_depreciation_board()
        self.assertEqual(len(asset.depreciation_line_ids), 12)
        self.assertFalse(asset.depreciation_line_ids.move_id)
        self.assertAmount(asset.value_residual, 1200)
        asset.validate()
        due = asset.depreciation_line_ids.filtered(lambda l: l.depreciation_date <= self.today)
        moves = asset.depreciation_line_ids.move_id
        self.assertEqual(set(moves.mapped('state')), {'posted'})
        self.assertEqual(len(moves), len(due))
        self.assertAmount(asset.value_residual, 1200 - 100 * len(due))
        expense = moves[:1].line_ids.filtered(lambda l: l.account_id == self.category.account_depreciation_expense_id)
        self.assertEqual(expense.analytic_distribution, {str(self.analytic.id): 100})
        self.assertAmount(expense.debit, 100)
        balance = sum(self.env['account.move.line'].search([
            ('account_id', '=', self.category.account_depreciation_id.id),
            ('parent_state', '=', 'posted')]).mapped('balance'))
        self.assertAmount(balance, -100 * len(due))
        self.Asset.compute_generated_entries(self.today + relativedelta(months=1))
        self.assertEqual(len(self.posted(asset)), len(due) + 1)

    def test_posted_message_html(self):
        """P1.15: "Depreciation line posted" renders as HTML in the asset's
        chatter (no escaped tags); the values stay escaped."""
        partner = self.env['res.partner'].create({'name': 'Kit <i>Vendor</i>'})
        asset = self.make_asset(self.category, 1200, self.months_back(1), partner_id=partner.id)
        asset.compute_depreciation_board()
        asset.validate()
        bodies = [str(m.body) for m in asset.message_ids if 'Depreciation line posted' in str(m.body)]
        self.assertTrue(bodies)
        for body in bodies:
            self.assertIn('<span>Depreciation line posted.</span>', body)
            self.assertIn('<b>Currency</b>: %s' % asset.currency_id.name, body)
            self.assertIn('Kit &lt;i&gt;Vendor&lt;/i&gt;', body)
            self.assertNotIn('&lt;span&gt;', body)
            self.assertNotIn('&lt;div&gt;', body)

    def test_old_posted_messages_rebuilt(self):
        """QA Q4: messages posted as escaped HTML before P1.15 are rebuilt
        by the 20.0.3.0.0 migration helper; values stay escaped; other
        messages are not touched."""
        asset = self.make_asset(self.category, 1200, self.months_back(1))
        old = ('<span>Depreciation line posted.</span><div> &nbsp; &nbsp; &bull; <b>Currency</b>: USD</div>'
               '<div> &nbsp; &nbsp; &bull; <b>Partner</b>: Kit <i>Vendor</i> & Co</div>')
        message = asset.message_post(body=old)
        other = asset.message_post(body='Kit plain note')
        self.assertIn('&lt;span&gt;', str(message.body))
        self.assertGreaterEqual(self.Asset._kit_fix_posted_messages(), 1)
        body = str(message.body)
        self.assertIn('<span>Depreciation line posted.</span>', body)
        self.assertIn('<b>Currency</b>: USD', body)
        self.assertIn('Kit &lt;i&gt;Vendor&lt;/i&gt; &amp; Co', body)
        self.assertNotIn('&lt;span&gt;', body)
        self.assertEqual(str(other.body), '<p>Kit plain note</p>')
        self.assertEqual(self.Asset._kit_fix_posted_messages(), 0)

    def test_modify_and_revalue(self):
        """Modify spreads the residual over the new duration; a revaluation
        adds to the residual and is spread on the board."""
        asset = self.make_asset(self.category, 1200, self.months_back(3))
        asset.validate()
        wizard = self.env['asset.modify'].with_context(active_id=asset.id, active_model=asset._name).create(
            {'name': 'longer', 'method_number': 18, 'method_period': 1})
        wizard.modify()
        rest = asset.depreciation_line_ids.filtered(lambda l: not l.move_id)
        self.assertAmount(sum(rest.mapped('amount')), asset.value_residual)
        residual = asset.value_residual
        asset._revaluate(650, self.today, self.kit_account('equity'))
        rest = asset.depreciation_line_ids.filtered(lambda l: not l.move_id)
        self.assertAmount(asset.value_residual, residual + 650)
        self.assertAmount(sum(rest.mapped('amount')), asset.value_residual)

    def test_pause_resume(self):
        """A paused asset gets no entries; resuming shifts the remaining
        lines by the pause."""
        asset = self.make_asset(self.category, 1200, self.months_back(3))
        asset.validate()
        asset.pause()
        before = len(self.posted(asset))
        self.Asset.compute_generated_entries(self.today + relativedelta(months=6))
        self.assertEqual(len(self.posted(asset)), before)
        first_rest = asset.depreciation_line_ids.filtered(lambda l: not l.move_id).sorted('depreciation_date')[:1]
        old_date = first_rest.depreciation_date
        asset.pause_date = self.today - relativedelta(days=10)
        asset.resume()
        self.assertEqual(first_rest.depreciation_date, old_date + relativedelta(days=10))

    def test_disposal(self):
        """Disposal posts the depreciation due up to its date and a balanced
        disposal entry; the asset is closed and gets nothing later."""
        asset = self.make_asset(self.category, 1200, self.months_back(3))
        asset.validate()
        due_before = len(self.posted(asset))
        move = asset._dispose(self.today + relativedelta(months=1), sale_value=0.0)
        self.assertEqual(asset.state, 'close')
        self.assertFalse(asset.depreciation_line_ids.filtered(lambda l: not l.move_id))
        self.assertEqual(len(self.posted(asset)), due_before + 1)
        self.assertEqual(move.state, 'posted')
        self.assertAmount(sum(move.line_ids.mapped('debit')), sum(move.line_ids.mapped('credit')))
        self.Asset.compute_generated_entries(self.today + relativedelta(years=2))
        self.assertEqual(len(self.posted(asset)), due_before + 1)

    def test_grouped_entries(self):
        """Grouped categories post one entry per category on the chosen
        date, with the analytic."""
        category = self.make_category('Grouped', group_entries=True, account_analytic_id=self.analytic.id)
        first = self.make_asset(category, 600, self.months_back(0))
        second = self.make_asset(category, 1200, self.months_back(0))
        for asset in first | second:
            asset.compute_depreciation_board()
        (first | second).state = 'open'
        ids = self.Asset.compute_generated_entries(self.months_back(0))
        move = self.env['account.move'].browse(ids).filtered(lambda m: m.ref == category.name)
        self.assertEqual(len(move), 1)
        self.assertEqual(move.state, 'posted')
        self.assertEqual(move.date, self.months_back(0))
        self.assertAmount(sum(move.line_ids.mapped('debit')), 150)
        self.assertEqual(move.line_ids.filtered('debit').analytic_distribution, {str(self.analytic.id): 100})

    def test_foreign_currency(self):
        """An asset in another currency posts the amount in that currency
        with a converted balance."""
        eur = self.env.ref('base.EUR')
        eur.active = True
        asset = self.make_asset(self.category, 1200, self.months_back(1), currency_id=eur.id)
        asset.validate()
        line = asset.depreciation_line_ids.move_id[:1].line_ids.filtered(
            lambda l: l.account_id == self.category.account_depreciation_expense_id)
        self.assertEqual(line.currency_id, eur)
        self.assertAmount(line.amount_currency, 100)
        self.assertGreater(line.balance, 0)

    def test_cancel_and_close(self):
        """Cancelling a depreciation entry frees its line; a fully
        depreciated asset is closed; prorata boards recompute."""
        asset = self.make_asset(self.category, 1200, self.months_back(3))
        asset.validate()
        line = self.posted(asset)[:1]
        move = line.move_id
        move.button_cancel()
        self.assertFalse(line.move_id)
        self.assertEqual(move.state, 'cancel')
        short = self.make_asset(self.make_category('Short', method_number=2), 200, self.months_back(3))
        short.validate()
        self.assertEqual(short.state, 'close')
        self.assertAmount(short.value_residual, 0)
        prorata = self.make_asset(self.make_category('Prorata', prorata=True, method_period=12, method_number=3),
                                  3000, date(self.year - 2, 3, 15))
        prorata.validate()
        prorata.compute_depreciation_board()

    def test_assets_from_bills(self):
        """Posting a bill creates one asset; reset to draft or cancel
        removes it; posting again does not duplicate; auto-confirmed
        assets post their due entries; reset is blocked once entries exist;
        the auto-post path creates the asset too."""
        category = self.make_category('Bill category', open_asset=False)
        product = self.env['product.product'].create({'name': 'Kit Machine'})
        product.product_tmpl_id.asset_category_id = category
        vendor = self.env['res.partner'].create({'name': 'Kit Asset Vendor'})

        def bill(cat=None, day=None):
            return self.env['account.move'].create({
                'move_type': 'in_invoice', 'partner_id': vendor.id, 'invoice_date': day or self.today,
                'invoice_line_ids': [Command.create({
                    'product_id': product.id, 'name': 'Machine', 'quantity': 1, 'price_unit': 2400,
                    'tax_ids': [Command.clear()], 'asset_category_id': (cat or category).id})]})

        def count(move):
            return self.Asset.with_context(active_test=False).search_count([('invoice_id', '=', move.id)])

        move = bill()
        move.action_post()
        self.assertEqual(count(move), 1)
        move.button_draft()
        self.assertEqual(count(move), 0)
        move.action_post()
        self.assertEqual(count(move), 1)
        move.button_cancel()
        self.assertEqual(count(move), 0)
        auto = bill(self.make_category('Auto', open_asset=True), self.months_back(3))
        auto.action_post()
        asset = self.Asset.search([('invoice_id', '=', auto.id)])
        self.assertEqual(asset.state, 'open')
        self.assertGreaterEqual(len(self.posted(asset)), 3)
        with self.assertRaises(UserError):
            auto.button_draft()
        cron_bill = bill()
        cron_bill._post(soft=False)
        self.assertEqual(count(cron_bill), 1)
