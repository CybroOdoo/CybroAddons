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

from odoo.tests.common import TransactionCase, tagged


@tagged('analytic_accounts_on_stock_picking', 'account_move')
class TestAccountMove(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company = cls.env.company

        # ── Analytic ──────────────────────────────────────────────────
        cls.analytic_plan = cls.env['account.analytic.plan'].search([], limit=1)
        if not cls.analytic_plan:
            cls.analytic_plan = cls.env['account.analytic.plan'].create(
                {'name': 'Test Plan'}
            )
        cls.analytic_account = cls.env['account.analytic.account'].create({
            'name': 'Test Analytic Acct',
            'plan_id': cls.analytic_plan.id,
        })

        # ── Journal (sale) — no company_id filter needed; env scopes it ──
        cls.sale_journal = cls.env['account.journal'].search(
            [('type', '=', 'sale')], limit=1,
        )

        # ── Accounts — Odoo 19: no company_id field on account.account ──
        cls.revenue_account = cls.env['account.account'].search(
            [('account_type', '=', 'income')], limit=1,
        )
        cls.receivable_account = cls.env['account.account'].search(
            [('account_type', '=', 'asset_receivable')], limit=1,
        )

        # ── Partner ───────────────────────────────────────────────────
        cls.partner = cls.env['res.partner'].create({'name': 'Test Customer'})

        # ── Warehouse ─────────────────────────────────────────────────
        cls.warehouse = cls.env['stock.warehouse'].search([], limit=1)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _create_invoice(self, origin=None, with_analytic=False):
        """Minimal draft customer invoice."""
        analytic_distribution = (
            {str(self.analytic_account.id): 100} if with_analytic else False
        )
        line_vals = {
            'display_type': 'product',
            'name': 'Service Line',
            'quantity': 1.0,
            'price_unit': 100.0,
            'account_id': self.revenue_account.id,
        }
        if analytic_distribution:
            line_vals['analytic_distribution'] = analytic_distribution

        return self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'journal_id': self.sale_journal.id,
            'invoice_origin': origin,
            'invoice_line_ids': [(0, 0, line_vals)],
        })

    def _create_picking(self, origin):
        """Minimal stock picking with the given origin."""
        picking_type = self.env['stock.picking.type'].search(
            [('code', '=', 'outgoing'),
             ('warehouse_id', '=', self.warehouse.id)],
            limit=1,
        )
        return self.env['stock.picking'].create({
            'picking_type_id': picking_type.id,
            'location_id': picking_type.default_location_src_id.id,
            'location_dest_id': picking_type.default_location_dest_id.id,
            'origin': origin,
        })

    # ------------------------------------------------------------------
    # 1. super() still posts the invoice
    # ------------------------------------------------------------------

    def test_action_post_posts_the_invoice(self):
        """action_post() must post the invoice (state → 'posted')."""
        invoice = self._create_invoice(origin='S00001')
        invoice.action_post()
        self.assertEqual(invoice.state, 'posted')

    # ------------------------------------------------------------------
    # 2. transfer_reference set when matching picking exists
    # ------------------------------------------------------------------

    def test_transfer_reference_set_when_picking_found(self):
        """Analytic lines get transfer_reference = picking.name when origin matches."""
        origin = 'SO-ANALYTIC-001'
        picking = self._create_picking(origin)
        invoice = self._create_invoice(origin=origin, with_analytic=True)
        invoice.action_post()

        product_lines = invoice.line_ids.filtered(
            lambda l: l.display_type == 'product'
        )
        analytic_lines = self.env['account.analytic.line'].search(
            [('move_line_id', 'in', product_lines.ids)]
        )
        for al in analytic_lines:
            self.assertEqual(
                al.transfer_reference, picking.name,
                f"Expected '{picking.name}', got '{al.transfer_reference}'",
            )

    # ------------------------------------------------------------------
    # 3. transfer_reference NOT set when no matching picking
    # ------------------------------------------------------------------

    def test_transfer_reference_not_set_without_matching_picking(self):
        """transfer_reference must be False when no picking matches origin."""
        invoice = self._create_invoice(origin='NO-PICKING-ORIGIN', with_analytic=True)
        invoice.action_post()

        product_lines = invoice.line_ids.filtered(
            lambda l: l.display_type == 'product'
        )
        analytic_lines = self.env['account.analytic.line'].search(
            [('move_line_id', 'in', product_lines.ids)]
        )
        for al in analytic_lines:
            self.assertFalse(al.transfer_reference)

    # ------------------------------------------------------------------
    # 4. Most-recent picking is used
    # ------------------------------------------------------------------

    def test_most_recent_picking_used(self):
        """
        The picking with the highest create_date (limit=1 desc) is used.

        Both pickings are created inside the same transaction, so their
        create_date timestamps are often identical (sub-millisecond apart).
        We force a clear gap by back-dating the older picking to yesterday
        via sudo() write on create_date, making the ordering deterministic.
        """
        from datetime import datetime, timedelta
        origin = 'SO-MULTI-PICK'

        old_pick = self._create_picking(origin)
        # Force create_date to yesterday so it is unambiguously older
        old_pick.sudo().write({'create_date': datetime.now() - timedelta(days=1)})

        recent = self._create_picking(origin)

        invoice = self._create_invoice(origin=origin, with_analytic=True)
        invoice.action_post()

        product_lines = invoice.line_ids.filtered(
            lambda l: l.display_type == 'product'
        )
        analytic_lines = self.env['account.analytic.line'].search(
            [('move_line_id', 'in', product_lines.ids)]
        )
        for al in analytic_lines:
            if al.transfer_reference:
                self.assertEqual(
                    al.transfer_reference, recent.name,
                    f"Expected most-recent picking '{recent.name}', "
                    f"got '{al.transfer_reference}' (old: '{old_pick.name}')",
                )

    # ------------------------------------------------------------------
    # 5. Non-product lines are ignored
    # ------------------------------------------------------------------

    def test_non_product_lines_not_targeted(self):
        """Note/section lines must not cause errors; invoice still posts."""
        origin = 'SO-NOTE-TEST'
        self._create_picking(origin)

        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'journal_id': self.sale_journal.id,
            'invoice_origin': origin,
            'invoice_line_ids': [
                (0, 0, {
                    'display_type': 'product',
                    'name': 'Product Line',
                    'quantity': 1.0,
                    'price_unit': 50.0,
                    'account_id': self.revenue_account.id,
                }),
                (0, 0, {
                    'display_type': 'line_note',
                    'name': 'Just a note',
                }),
            ],
        })
        invoice.action_post()
        self.assertEqual(invoice.state, 'posted')

    # ------------------------------------------------------------------
    # 6. No analytic lines → no crash
    # ------------------------------------------------------------------

    def test_action_post_no_analytic_lines_no_crash(self):
        """action_post() must not crash when no analytic distribution is set."""
        origin = 'SO-NO-ANALYTIC'
        self._create_picking(origin)
        invoice = self._create_invoice(origin=origin, with_analytic=False)
        invoice.action_post()
        self.assertEqual(invoice.state, 'posted')

    # ------------------------------------------------------------------
    # 7. None origin → no crash
    # ------------------------------------------------------------------

    def test_action_post_none_origin_no_crash(self):
        """Invoice with no invoice_origin must not crash."""
        invoice = self._create_invoice(origin=None, with_analytic=False)
        invoice.action_post()
        self.assertEqual(invoice.state, 'posted')