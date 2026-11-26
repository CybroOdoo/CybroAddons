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

from odoo import Command
from odoo.tests import Form, new_test_user, tagged

from .common import AccountingKitTestCommon


@tagged('post_install', '-at_install')
class TestFollowup(AccountingKitTestCommon):
    """Payment follow-up (P1.9): open invoices of the customer and its
    contacts, totals in company currency, status, escalation, reset on
    payment, letter and email with overdue invoices only, query count."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.eur = cls.env.ref('base.EUR')
        cls.eur.active = True
        cls.env['res.currency.rate'].create({
            'currency_id': cls.eur.id, 'rate': 0.5, 'name': cls.today - timedelta(days=400),
            'company_id': cls.company.id})
        followup = cls.env['account.followup'].search([('company_id', '=', cls.company.id)], limit=1) \
            or cls.env['account.followup'].create({'company_id': cls.company.id})
        followup.followup_line_ids.unlink()
        cls.level1 = cls.env['followup.line'].create(
            {'name': 'L1', 'delay': 10, 'followup_id': followup.id, 'send_email': False})
        cls.level2 = cls.env['followup.line'].create(
            {'name': 'L2', 'delay': 30, 'followup_id': followup.id, 'send_email': False})
        cls.acme = cls.env['res.partner'].create({'name': 'Kit Acme', 'is_company': True})
        cls.john = cls.env['res.partner'].create({'name': 'John', 'parent_id': cls.acme.id})

    def invoice(self, partner, amount, due_days, state='posted', currency=None):
        due = self.today - timedelta(days=due_days)
        move = self.env['account.move'].create({
            'move_type': 'out_invoice', 'partner_id': partner.id,
            'invoice_date': self.today - timedelta(days=max(due_days, 0) + 1),
            'currency_id': (currency or self.company.currency_id).id,
            'invoice_line_ids': [Command.create({'name': 'x', 'quantity': 1, 'price_unit': amount,
                                                 'tax_ids': [Command.clear()]})]})
        move.invoice_date_due = due
        if state in ('posted', 'cancel'):
            move.action_post()
            move.invoice_date_due = due
        if state == 'cancel':
            move.button_cancel()
        return move

    def pay(self, move, amount=None):
        values = {'payment_date': self.today}
        if amount:
            values['amount'] = amount
        self.env['account.payment.register'].with_context(
            active_model='account.move', active_ids=move.ids).create(values).action_create_payments()

    def render_letter(self, partner):
        report = self.env.ref('base_accounting_kit.action_report_followup_letter')
        html = report._render_qweb_html(report.report_name, partner.ids)[0].decode()
        return html[html.find('<tbody'):html.find('</tbody>')]

    def test_open_invoices_and_totals(self):
        """Posted open invoices of the customer and its contacts (partly
        paid included, drafts / cancelled / other companies out), totals in
        company currency, overdue list, letter and email with overdue only."""
        overdue = self.invoice(self.acme, 1000, 40)
        contact = self.invoice(self.john, 500, 5)
        draft = self.invoice(self.acme, 700, 50, 'draft')
        cancelled = self.invoice(self.acme, 300, 50, 'cancel')
        partial = self.invoice(self.acme, 400, 20)
        self.pay(partial, 100)
        future_eur = self.invoice(self.acme, 200, -10, currency=self.eur)
        acme = self.acme
        self.assertEqual(set(acme.invoice_list.ids), {overdue.id, contact.id, partial.id, future_eur.id})
        self.assertNotIn(draft, acme.invoice_list)
        self.assertNotIn(cancelled, acme.invoice_list)
        self.assertEqual(partial.payment_state, 'partial')
        self.assertAmount(acme.total_due, 2200)
        self.assertAmount(acme.total_overdue, 1800)
        self.assertEqual(acme.followup_status, 'in_need_of_action')
        self.assertEqual(acme.next_reminder_date, self.today - timedelta(days=30))
        self.assertEqual(set(acme.overdue_invoice_ids.ids), {overdue.id, contact.id, partial.id})
        letter = self.render_letter(acme)
        self.assertIn(overdue.name, letter)
        self.assertNotIn(future_eur.name, letter)
        mail = self.env.ref('base_accounting_kit.mail_template_followup')._render_field('body_html', acme.ids)[acme.id]
        self.assertIn(overdue.name, mail)
        self.assertNotIn(future_eur.name, mail)
        self.assertFalse(self.john.invoice_list)
        self.assertEqual(self.john.followup_status, 'no_action_needed')
        need = self.env['res.partner'].search([('followup_status', '=', 'in_need_of_action')])
        self.assertIn(acme, need)
        self.assertNotIn(self.john, need)

    def test_escalation_and_reset(self):
        """Levels escalate with the overdue days; paying everything resets
        the level; a new overdue invoice starts at the first level; the
        cron sends due levels and resets customers without open items."""
        invoice = self.invoice(self.acme, 1000, 40)
        acme = self.acme
        self.assertEqual(acme._get_next_followup_line(), self.level1)
        acme._send_followup()
        self.assertEqual(acme.followup_level_id, self.level1)
        self.assertEqual(acme._get_next_followup_line(), self.level2)
        acme._send_followup()
        acme.invalidate_recordset()
        self.assertFalse(acme._get_next_followup_line())
        self.assertEqual(acme.followup_status, 'with_overdue_invoices')
        self.pay(invoice)
        acme.invalidate_recordset()
        self.assertFalse(acme.invoice_list)
        self.assertFalse(acme.followup_level_id)
        self.invoice(self.acme, 250, 15)
        acme.invalidate_recordset()
        self.assertEqual(acme._get_next_followup_line(), self.level1)
        acme.followup_level_id = self.level2
        self.assertEqual(acme._get_next_followup_line(), self.level1)
        beta = self.env['res.partner'].create({'name': 'Kit Beta', 'is_company': True, 'followup_level_id': self.level1.id})
        acme.followup_level_id = False
        self.env['res.partner']._cron_send_followups()
        acme.invalidate_recordset()
        self.assertFalse(beta.followup_level_id)
        self.assertEqual(acme.followup_level_id, self.level1)

    def test_letter_excludes_drafts(self):
        """The letter lists open invoices, never drafts."""
        invoice = self.invoice(self.acme, 250, 15)
        self.invoice(self.acme, 777, 60, 'draft')
        body = self.render_letter(self.acme)
        self.assertIn(invoice.name, body)
        self.assertNotIn('777.00', body)

    def test_filters_for_accountants(self):
        """The follow-up filters of the contacts search show only to users
        who may read follow-up levels (billing users got an access error)."""
        view = self.env.ref('base.view_res_partner_filter').id
        billing = new_test_user(self.env, login='kit_fu_billing', groups='account.group_account_invoice')
        accountant = new_test_user(self.env, login='kit_fu_accountant', groups='account.group_account_user')
        for user, shown in ((billing, False), (accountant, True)):
            arch = self.env['res.partner'].with_user(user).get_view(view, 'search')['arch']
            self.assertEqual('filter_with_overdue_invoices' in arch, shown, user.login)
            self.assertEqual('filter_in_need_of_action' in arch, shown, user.login)

    def test_statement_lists_new_contact(self):
        """Open invoices / bills of the statement: empty for a contact not
        saved yet (no NewId in a search domain), filled once saved."""
        with self.assertNoLogs('odoo.domains', level='WARNING'):
            form = Form(self.env['res.partner'])
            form.name = 'Kit New Contact'
            self.assertFalse(form.customer_report_ids)
            self.assertFalse(form.vendor_statement_ids)
        invoice = self.invoice(self.acme, 120, 10)
        self.assertIn(invoice, self.acme.customer_report_ids)

    def test_query_count(self):
        """The follow-up list reads totals and status with a constant number
        of queries (5 or 50 customers)."""
        customers = self.env['res.partner'].create([{'name': 'Kit Perf %d' % k, 'is_company': True} for k in range(50)])
        moves = self.env['account.move'].create([{
            'move_type': 'out_invoice', 'partner_id': partner.id,
            'invoice_date': self.today - timedelta(days=20), 'invoice_date_due': self.today - timedelta(days=12),
            'invoice_line_ids': [Command.create({'name': 'x', 'quantity': 1, 'price_unit': 10, 'tax_ids': [Command.clear()]})]}
            for partner in customers])
        moves.action_post()
        self.env.flush_all()

        def count(n):
            records = customers[:n]
            self.env.invalidate_all()
            start = self.cr.sql_log_count
            records.read(['total_due', 'total_overdue', 'followup_status'])
            return self.cr.sql_log_count - start

        self.assertLessEqual(count(50), count(5) + 2)
