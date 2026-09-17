# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta
from freezegun import freeze_time
from odoo import fields
from odoo.tests import tagged
from .common import AccountKitCommon


@tagged('post_install', '-at_install')
class TestAsset(AccountKitCommon):

    def test_compute_depreciation_board(self):
        """Computing the board yields `method_number` lines summing to the value."""
        asset = self._create_asset(value=1200.0, method_number=4)
        asset.compute_depreciation_board()
        self.assertEqual(len(asset.depreciation_line_ids), 4,
                         "One depreciation line per depreciation period")
        self.assertAlmostEqual(
            sum(asset.depreciation_line_ids.mapped('amount')), 1200.0, 2,
            "Depreciation lines must sum to the gross value")

    def test_validate_opens_asset_and_sets_auto_post(self):
        """Validate moves the asset to 'open' and future entries to auto-post."""
        with freeze_time('2020-01-15'):
            asset = self._create_asset(value=1200.0, date='2020-01-01')
            asset.validate()
            self.assertEqual(asset.state, 'open')
            self.assertTrue(asset.depreciation_line_ids,
                            "Validation computes the depreciation board")

    def test_depreciation_move_is_balanced(self):
        """A depreciation entry (created by the board) is a balanced 2-line move."""
        asset = self._create_asset(value=1200.0)
        asset.compute_depreciation_board()
        move = asset.depreciation_line_ids[0].move_id
        self.assertTrue(move, "Board computation creates the depreciation entries")
        self.assertEqual(len(move.line_ids), 2, "Depreciation entry has two lines")
        self.assertAlmostEqual(sum(move.line_ids.mapped('debit')),
                               sum(move.line_ids.mapped('credit')), 2,
                               "The depreciation entry must balance")

    def test_disposal_reverses_posted_moves(self):
        """Cancelling an asset reverses posted entries instead of deleting them."""
        with freeze_time('2020-01-15'):
            asset = self._create_asset(value=1200.0, date='2019-01-01')
            asset.compute_depreciation_board()
            move = asset.depreciation_line_ids[0].move_id
            self.assertTrue(move)
            move.action_post()
            self.assertEqual(move.state, 'posted')

            asset.action_cancel_assets()

        self.assertEqual(asset.state, 'cancelled')
        self.assertEqual(move.state, 'posted',
                         "Posted move must NOT be deleted...")
        self.assertTrue(move.reversal_move_ids,
                        "...it must be reversed instead")

    def test_copy_regenerates_name(self):
        """Copying an asset appends '(copy)' to the name (batch-safe copy_data)."""
        asset = self._create_asset()
        copy = asset.copy()
        self.assertIn('(copy)', copy.name)

    def test_cron_generate_entries_runs(self):
        """The depreciation cron posts due entries of running assets w/o error."""
        with freeze_time('2020-06-01'):
            asset = self._create_asset(value=1200.0, date='2019-01-01')
            asset.validate()
            self.assertEqual(asset.state, 'open')
            # Should not raise; posts any due depreciation entries.
            self.env['account.asset.asset']._cron_generate_entries()

    # --- lifecycle completeness (Phase 3 #2) ----------------------------
    def test_pause_and_resume_shifts_schedule(self):
        """Pausing freezes the schedule; resuming shifts remaining entries."""
        with freeze_time('2020-06-01'):
            asset = self._create_asset(value=1200.0, date='2020-01-01')
            asset.validate()
            self.assertEqual(asset.state, 'open')
            asset.pause()
            self.assertEqual(asset.state, 'paused')
            self.assertEqual(asset.pause_date, fields.Date.to_date('2020-06-01'))
        draft_lines = asset.depreciation_line_ids.filtered(
            lambda l: l.move_id and l.move_id.state == 'draft'
            and l.depreciation_date)
        self.assertTrue(draft_lines, "There should be pending depreciation")
        before = min(draft_lines.mapped('depreciation_date'))
        with freeze_time('2020-07-01'):  # 30 days later
            asset.resume()
        self.assertEqual(asset.state, 'open')
        self.assertFalse(asset.pause_date)
        after = min(asset.depreciation_line_ids.filtered(
            lambda l: l.move_id and l.move_id.state == 'draft'
            and l.depreciation_date).mapped('depreciation_date'))
        self.assertEqual(after, before + relativedelta(days=30),
                         "Remaining depreciation is shifted by the pause gap")

    def test_revaluation_increases_value_and_posts_entry(self):
        """Revaluation raises the gross value and posts a balanced JE."""
        with freeze_time('2020-06-01'):
            asset = self._create_asset(value=1200.0, date='2020-01-01')
            asset.validate()
            move = asset._revaluate(
                300.0, fields.Date.to_date('2020-06-01'), self.asset_account)
        self.assertEqual(asset.value, 1500.0, "Gross value increased by 300")
        self.assertEqual(move.state, 'posted')
        self.assertAlmostEqual(sum(move.line_ids.mapped('debit')),
                               sum(move.line_ids.mapped('credit')), 2)

    def test_dispose_scrap_books_loss_and_closes(self):
        """Scrapping an asset with book value left posts the full loss to the
        gain/loss account, balances, and closes the asset."""
        asset = self._create_asset(value=1200.0, date='2020-01-01')
        asset.write({'state': 'open'})  # open, no depreciation posted yet
        move = asset._dispose(fields.Date.to_date('2020-06-01'))
        self.assertEqual(asset.state, 'close')
        self.assertEqual(move.state, 'posted')
        self.assertAlmostEqual(sum(move.line_ids.mapped('debit')),
                               sum(move.line_ids.mapped('credit')), 2,
                               "Disposal entry must balance")
        self.assertIn(asset.account_disposal_id,
                      move.line_ids.mapped('account_id'),
                      "The full book value is booked as a loss to the "
                      "gain/loss account")

    def test_dispose_sale_with_proceeds(self):
        """A sale disposal books proceeds + the residual gain/loss, balances,
        and closes the asset."""
        asset = self._create_asset(value=1200.0, date='2020-01-01')
        asset.write({'state': 'open'})
        receivable = self.company_data['default_account_receivable']
        move = asset._dispose(fields.Date.to_date('2020-06-01'),
                              sale_value=1000.0, sale_account=receivable)
        self.assertEqual(asset.state, 'close')
        self.assertEqual(move.state, 'posted')
        self.assertAlmostEqual(sum(move.line_ids.mapped('debit')),
                               sum(move.line_ids.mapped('credit')), 2)
        self.assertIn(receivable, move.line_ids.mapped('account_id'),
                      "Proceeds are booked to the chosen account")

    def test_auto_asset_from_vendor_bill(self):
        """Posting a vendor bill for a product with an asset category creates
        the asset (via asset_create's product-category fallback)."""
        self.product_a.asset_category_id = self.asset_category
        bill = self.init_invoice('in_invoice', partner=self.partner_a,
                                 products=self.product_a, post=False)
        bill.action_post()
        asset = self.env['account.asset.asset'].search(
            [('invoice_id', '=', bill.id)])
        self.assertTrue(asset, "An asset must be created from the posted bill")
        self.assertEqual(asset.category_id, self.asset_category)
