# -*- coding: utf-8 -*-
from odoo.tests import tagged
from .common import AccountKitCommon


@tagged('post_install', '-at_install')
class TestFollowup(AccountKitCommon):

    def test_followup_data_loaded(self):
        """The default follow-up level data is installed."""
        self.assertTrue(
            self.env['account.followup'].search([], limit=1),
            "An account.followup record should exist from data")
        self.assertTrue(
            self.env['followup.line'].search([], limit=1),
            "A followup.line record should exist from data")

    def test_partner_followup_totals(self):
        """An unpaid posted customer invoice feeds the partner's due totals."""
        self.init_invoice('out_invoice', partner=self.partner_a,
                          invoice_date='2020-01-01', amounts=[500.0],
                          taxes=[], post=True)
        self.partner_a.invalidate_recordset(
            ['total_due', 'total_overdue', 'followup_status'])
        self.assertAlmostEqual(self.partner_a.total_due, 500.0, 2)
        # 2020 invoice is long overdue relative to "today".
        self.assertAlmostEqual(self.partner_a.total_overdue, 500.0, 2)

    def test_followup_status_is_valid(self):
        """followup_status computes to one of its selection values w/o error."""
        self.partner_a.invalidate_recordset(['followup_status'])
        self.assertIn(
            self.partner_a.followup_status,
            (False, 'in_need_of_action', 'with_overdue_invoices',
             'no_action_needed'))

    # --- follow-up automation (Phase 3) ---------------------------------
    def _overdue_invoice(self):
        return self.init_invoice(
            'out_invoice', partner=self.partner_a, invoice_date='2020-01-01',
            amounts=[500.0], taxes=[], post=True)

    def _setup_levels(self):
        """Deterministic follow-up levels on the *current* test company."""
        followup = self.env['account.followup'].search(
            [('company_id', '=', self.env.company.id)], limit=1)
        if not followup:
            followup = self.env['account.followup'].create(
                {'company_id': self.env.company.id})
        followup.followup_line_ids.unlink()
        level1 = self.env['followup.line'].create({
            'name': 'Reminder', 'delay': 5, 'followup_id': followup.id})
        level2 = self.env['followup.line'].create({
            'name': 'Second Reminder', 'delay': 15, 'followup_id': followup.id})
        return level1, level2

    def test_escalation_advances_through_levels(self):
        """_get_next_followup_line walks the levels (multi-level escalation)."""
        self._overdue_invoice()
        level1, level2 = self._setup_levels()
        self.partner_a.invalidate_recordset()
        # No level reached yet -> first due level.
        self.assertEqual(self.partner_a._get_next_followup_line(), level1)
        self.partner_a.followup_level_id = level1
        # Then it escalates to the next level.
        self.assertEqual(self.partner_a._get_next_followup_line(), level2)
        self.partner_a.followup_level_id = level2
        # Highest reached -> nothing more to send.
        self.assertFalse(self.partner_a._get_next_followup_line())

    def test_send_followup_advances_level_and_logs(self):
        """_send_followup records the level, stamps the date and logs it."""
        self._overdue_invoice()
        level1, _level2 = self._setup_levels()
        self.partner_a.email = 'customer@example.com'
        msgs_before = len(self.partner_a.message_ids)
        self.partner_a._send_followup()
        self.assertEqual(self.partner_a.followup_level_id, level1)
        self.assertTrue(self.partner_a.latest_followup_date)
        self.assertGreater(len(self.partner_a.message_ids), msgs_before,
                           "Sending a follow-up logs a chatter message")

    def test_cron_sends_due_followups(self):
        """The (inactive) cron method sends follow-ups to overdue customers."""
        self._overdue_invoice()
        self._setup_levels()
        self.partner_a.email = 'customer@example.com'
        self.env['res.partner']._cron_send_followups()
        self.assertTrue(self.partner_a.followup_level_id,
                        "Cron advances the overdue customer's follow-up level")

    def test_cron_is_inactive_by_default(self):
        """The follow-up cron ships disabled so it never emails on install."""
        cron = self.env.ref('base_accounting_kit.ir_cron_send_followups')
        self.assertFalse(cron.active)
