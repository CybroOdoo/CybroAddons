# -*- coding: utf-8 -*-
from datetime import date
from freezegun import freeze_time
from odoo.tests import tagged
from .common import AccountKitCommon


@tagged('post_install', '-at_install')
class TestRecurring(AccountKitCommon):

    def _template(self):
        return self.env['account.recurring.payments'].create({
            'name': 'Monthly Rent',
            'debit_account': self.expense_account.id,
            'credit_account': self.company_data['default_account_payable'].id,
            'journal_id': self.misc_journal.id,
            'date': '2020-01-01',
            'recurring_period': 'months',
            'recurring_interval': 1,
            'amount': 100.0,
            'state': 'running',
            'journal_state': 'posted',
            'pay_time': 'pay_now',
        })

    def test_next_date_computed(self):
        """next_date is computed ahead of today from the schedule."""
        with freeze_time('2020-04-15'):
            tmpl = self._template()
            self.assertTrue(tmpl.next_date)
            self.assertGreater(tmpl.next_date, date(2020, 4, 15))

    def test_cron_generates_posted_entries_in_template_company(self):
        """The cron generates recurring moves, posts them, and stamps the
        template's company (not env.company)."""
        with freeze_time('2020-04-15'):
            tmpl = self._template()
            self.env['account.recurring.payments']._cron_generate_entries()
            moves = self.env['account.move'].search(
                [('recurring_ref', 'like', '%s/' % tmpl.id)])
            self.assertTrue(moves, "Cron must generate recurring journal entries")
            self.assertEqual(moves.mapped('company_id'), tmpl.company_id,
                             "Entries must belong to the template's company")
            self.assertEqual(set(moves.mapped('state')), {'posted'},
                             "journal_state='posted' must post the entries")

    def test_cron_is_idempotent(self):
        """Re-running the cron does not duplicate already-generated entries."""
        with freeze_time('2020-04-15'):
            tmpl = self._template()
            RP = self.env['account.recurring.payments']
            RP._cron_generate_entries()
            count1 = self.env['account.move'].search_count(
                [('recurring_ref', 'like', '%s/' % tmpl.id)])
            RP._cron_generate_entries()
            count2 = self.env['account.move'].search_count(
                [('recurring_ref', 'like', '%s/' % tmpl.id)])
            self.assertEqual(count1, count2, "Cron must not duplicate entries")
