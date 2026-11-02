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
from datetime import timedelta
from unittest.mock import patch

from odoo import Command, fields
from odoo.exceptions import LockError
from odoo.tests import tagged
from odoo.tools import mute_logger

from odoo.addons.account_payment.tests.common import AccountPaymentCommon
from odoo.addons.mail.models.mail_template import MailTemplate
from odoo.addons.show_booking_management.models.movie_screen import MovieScreen


@tagged('post_install', '-at_install')
class TestPaymentFulfilment(AccountPaymentCommon):
    """ The ticket is issued from `payment.transaction._post_process`, through
    the real payment / account_payment flow (transaction -> post-processing
    cron -> payment reconciled with the invoice). Nothing in the payment flow
    is mocked; only the outgoing email is observed. """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Fixtures and assertions are staff-side data; the code under test runs
        # in the payment cron / sudo environments, never as the buyer.
        cls.env = cls.env(su=True)
        today = fields.Date.today()
        cls.today = today
        cls.screen = cls.env['movie.screen'].create({
            'name': 'Screen 1', 'total_rows': 5, 'no_of_seat_row': 5})
        cls.time_slot = cls.env['time.slots'].create({'movie_time': '18:30'})
        cls.movie = cls.env['movie.movie'].create({
            'name': 'Payment Movie',
            'release_date': today - timedelta(days=5),
            'show_start_date': today,
            'show_end_date': today + timedelta(days=30),
            'price': 100.0,
            'available_screens_ids': [Command.link(cls.screen.id)],
            'available_time_slots_ids': [Command.link(cls.time_slot.id)],
        })
        cls.movie.action_prebooking()
        cls.movie.action_start_show()
        cls.admin_group = cls.env.ref('show_booking_management.show_booking_management_group_admin')
        cls.show_admin = cls.env['res.users'].create({
            'name': 'Show Admin', 'login': 'show_admin_fulfilment',
            'email': 'show.admin@example.com',
            'group_ids': [Command.link(cls.admin_group.id)],
        })
        cls.tx_count = 0

    def setUp(self):
        super().setUp()
        # The only administrator is the user created above, whatever the demo data says.
        self.admin_group.write({'user_ids': [Command.set(self.show_admin.ids)]})
        self.env.company.email = 'company@example.com'

    # -- helpers ---------------------------------------------------------------
    def _booking_data(self, seats=('R1C1', 'R1C2'), **overrides):
        return dict({
            'movie_id': self.movie.id,
            'screen_id': self.screen.id,
            'time_slot_id': self.time_slot.id,
            'booking_date': str(self.today),
            'selected_seats': list(seats),
            'registration_id': '',
        }, **overrides)

    def _make_invoice(self, **data_overrides):
        data = self._booking_data(**data_overrides)
        return self.env['account.move']._create_movie_booking_invoice(
            self.partner, self.movie, data)

    def _pay(self, invoice, amount=None, run=True):
        """ Confirm a transaction paying the invoice and post-process it the way
        the payment cron does. """
        type(self).tx_count += 1
        tx = self._create_transaction(
            'redirect', state='done',
            reference='movie-tx-%s' % self.tx_count,
            amount=invoice.amount_total if amount is None else amount,
            currency_id=invoice.currency_id.id,
            partner_id=invoice.partner_id.id,
            invoice_ids=[Command.set(invoice.ids)],
        )
        if run:
            self._run_post_processing()
        return tx

    def _tickets(self, invoice=None):
        return self.env['movie.registration'].search([('partner_id', '=', self.partner.id)])

    def _spy_send_mail(self):
        calls = []
        original = MailTemplate.send_mail

        def spy(template, res_id, *args, **kwargs):
            calls.append((res_id, kwargs))
            return original(template, res_id, *args, **kwargs)
        patcher = patch.object(MailTemplate, 'send_mail', spy)
        patcher.start()
        self.addCleanup(patcher.stop)
        return calls

    # -- the ticket ------------------------------------------------------------
    def test_paid_invoice_issues_exactly_one_ticket(self):
        invoice = self._make_invoice()
        self.assertEqual(invoice.state, 'posted')
        self.assertEqual(invoice.movie_booking_data['selected_seats'], ['R1C1', 'R1C2'])
        self.assertFalse(self._tickets(), "Nothing is booked before the payment")
        calls = self._spy_send_mail()

        self._pay(invoice)

        self.assertIn(invoice.payment_state, ('paid', 'in_payment'))
        ticket = self._tickets()
        self.assertEqual(len(ticket), 1)
        self.assertEqual(ticket.state, 'invoiced')
        self.assertEqual(ticket.partner_id, invoice.partner_id)
        self.assertEqual(ticket.no_of_tickets, 2)
        self.assertEqual(sorted(ticket.seat_ids.mapped('seat')), ['R1C1', 'R1C2'])
        self.assertTrue(all(ticket.seat_ids.mapped('is_booked')))
        self.assertEqual(invoice.movie_ticket_id, ticket)
        self.assertFalse(invoice.movie_booking_data, "The pending booking is closed")
        self.assertFalse(invoice.movie_booking_issue)
        self.assertTrue(ticket.qr_code)
        attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'movie.registration'), ('res_id', '=', ticket.id)])
        self.assertEqual(len(attachments), 1, "One QR attachment")
        self.assertTrue(attachments.raw.content.startswith(b'\x89PNG'), "The attachment carries the QR image")
        self.assertEqual(len(calls), 1, "One ticket email")
        self.assertEqual(calls[0][0], ticket.id)
        self.assertEqual(calls[0][1]['email_values']['attachment_ids'], [(6, 0, attachments.ids)])

    def test_post_process_twice_does_not_confirm_twice(self):
        invoice = self._make_invoice()
        tx = self._pay(invoice)
        self.assertEqual(len(self._tickets()), 1)
        calls = self._spy_send_mail()

        # Core flags the transaction: a second run of the cron does nothing...
        self._run_post_processing()
        # ...and calling the override directly is still guarded by the invoice:
        # an invoice whose pending booking was closed is not even picked up.
        with patch.object(self.env.registry['movie.registration'], '_fulfil_booking',
                          autospec=True) as fulfil:
            tx.with_context(payment_safe_write=True)._post_process()
            tx.with_context(payment_safe_write=True)._post_process()
        fulfil.assert_not_called()

        self.assertEqual(len(self._tickets()), 1)
        self.assertEqual(self.env['movie.seats'].search_count([('seat', '=', 'R1C1')]), 1)
        self.assertFalse(calls, "No second ticket email")
        self.assertFalse(invoice.movie_booking_issue, "A replay is a no-op, not a conflict with itself")

    def test_fulfil_booking_twice_is_a_noop(self):
        """ The guard of _fulfil_booking itself (not only the filter of
        _post_process): called again on a closed booking it does nothing. """
        invoice = self._make_invoice()
        self._pay(invoice)
        ticket = self._tickets()
        self.assertFalse(self.env['movie.registration']._fulfil_booking(invoice))
        self.assertEqual(self._tickets(), ticket)
        self.assertFalse(invoice.movie_booking_issue)

    def test_fulfil_booking_never_books_an_invoice_that_already_has_a_ticket(self):
        """ Even if the pending data is (wrongly) still there, an invoice that
        has a ticket is never booked a second time and never reported. """
        invoice = self._make_invoice()
        self._pay(invoice)
        ticket = self._tickets()
        invoice.movie_booking_data = self._booking_data()  # inconsistent state
        self.assertFalse(self.env['movie.registration']._fulfil_booking(invoice))
        self.assertEqual(self._tickets(), ticket)
        self.assertEqual(self.env['movie.seats'].search_count([('seat', '=', 'R1C1')]), 1)
        self.assertFalse(invoice.movie_booking_issue)

    def test_unconfirmed_transaction_does_not_reach_the_fulfilment(self):
        invoice = self._make_invoice()
        type(self).tx_count += 1
        self._create_transaction(
            'redirect', state='pending', reference='movie-tx-pend-%s' % self.tx_count,
            amount=invoice.amount_total, currency_id=invoice.currency_id.id,
            partner_id=invoice.partner_id.id, invoice_ids=[Command.set(invoice.ids)])
        with patch.object(self.env.registry['movie.registration'], '_fulfil_booking',
                          autospec=True) as fulfil:
            self._run_post_processing()
        fulfil.assert_not_called()

    def test_two_transactions_paying_one_invoice_confirm_once(self):
        invoice = self._make_invoice()
        self._pay(invoice, run=False)
        self._pay(invoice, run=False)
        self._run_post_processing()
        self.assertEqual(len(self._tickets()), 1)
        self.assertEqual(self.env['movie.seats'].search_count([('seat', '=', 'R1C1')]), 1)
        self.assertFalse(invoice.movie_booking_issue)

    def test_partial_payment_issues_no_ticket_until_fully_paid(self):
        invoice = self._make_invoice()
        total = invoice.amount_total
        self._pay(invoice, amount=total * 0.1)
        self.assertEqual(invoice.payment_state, 'partial')
        self.assertFalse(self._tickets(), "A partial payment does not buy the seats")
        self.assertTrue(invoice.movie_booking_data, "The booking waits for the rest")
        self.assertFalse(invoice.movie_booking_issue, "Waiting is not an issue")

        self._pay(invoice, amount=total - total * 0.1)
        self.assertEqual(len(self._tickets()), 1, "The rest of the payment completes it")

    def test_unconfirmed_transaction_issues_no_ticket(self):
        invoice = self._make_invoice()
        type(self).tx_count += 1
        self._create_transaction(
            'redirect', state='pending', reference='movie-tx-pending-%s' % self.tx_count,
            amount=invoice.amount_total, currency_id=invoice.currency_id.id,
            partner_id=invoice.partner_id.id, invoice_ids=[Command.set(invoice.ids)])
        self._run_post_processing()
        self.assertFalse(self._tickets())
        self.assertTrue(invoice.movie_booking_data)

    # -- seat taken after payment ----------------------------------------------
    def _book_seat_elsewhere(self, seat='R1C1'):
        other = self.env['res.partner'].create({'name': 'Faster Customer'})
        registration = self.env['movie.registration'].create({
            'partner_id': other.id, 'movie_id': self.movie.id, 'date': self.today,
            'time_slot_id': self.time_slot.id, 'screen_id': self.screen.id,
            'no_of_tickets': 1, 'state': 'invoiced'})
        self.env['movie.seats'].create({
            'screen_id': self.screen.id, 'time_slot_id': self.time_slot.id,
            'movie_registration_id': registration.id, 'date': self.today,
            'seat': seat, 'is_booked': True})
        return registration

    @mute_logger('odoo.addons.show_booking_management.models.movie_registration')
    def test_seat_taken_after_payment_flags_invoice_without_raising(self):
        invoice = self._make_invoice()
        self._book_seat_elsewhere('R1C1')

        self._pay(invoice)  # must not raise

        self.assertFalse(self._tickets(), "No ticket for the taken seat")
        self.assertFalse(invoice.movie_ticket_id)
        self.assertIn(invoice.payment_state, ('paid', 'in_payment'), "The payment itself is kept")
        self.assertTrue(invoice.movie_booking_issue, "Staff can find the invoice")
        self.assertTrue(invoice.movie_booking_data, "The booking data is kept for staff")
        self.assertIn('R1C1', ' '.join(invoice.message_ids.mapped(lambda m: m.body or '')))
        activity = self.env['mail.activity'].search([
            ('res_model', '=', 'account.move'), ('res_id', '=', invoice.id)])
        self.assertEqual(len(activity), 1)
        self.assertEqual(activity.user_id, self.show_admin)
        self.assertEqual(self.env['movie.seats'].search_count([('seat', '=', 'R1C2')]), 0,
                         "The other seat of the booking is not booked either")

    @mute_logger('odoo.addons.show_booking_management.models.movie_registration')
    def test_seat_issue_is_notified_once(self):
        invoice = self._make_invoice()
        self._book_seat_elsewhere('R1C1')
        self._pay(invoice)
        self._pay(invoice)  # a second transaction re-attempts the booking
        activity = self.env['mail.activity'].search([
            ('res_model', '=', 'account.move'), ('res_id', '=', invoice.id)])
        self.assertEqual(len(activity), 1)

    @mute_logger('odoo.addons.show_booking_management.models.movie_registration')
    def test_seat_issue_without_admin_emails_the_company(self):
        self.admin_group.write({'user_ids': [Command.clear()]})
        sent = []
        original = self.env.registry['mail.mail'].create

        def spy(model, vals):
            sent.append(vals)
            return original(model, vals)
        invoice = self._make_invoice()
        self._book_seat_elsewhere('R1C1')
        with patch.object(self.env.registry['mail.mail'], 'create', spy):
            self._pay(invoice)
        self.assertTrue(invoice.movie_booking_issue)
        self.assertTrue(any(v.get('email_to') == 'company@example.com' for v in sent))

    # -- stored data is re-validated ---------------------------------------------
    @mute_logger('odoo.addons.show_booking_management.models.movie_registration')
    def test_tampered_or_stale_booking_data_is_not_trusted(self):
        cases = {
            'seat outside the screen': dict(selected_seats=['R9C9']),
            'malformed seat': dict(selected_seats=['A1']),
            'duplicated seat': dict(selected_seats=['R2C1', 'R2C1']),
            'unknown screen': dict(screen_id=999999),
            'date outside the show period': dict(
                booking_date=str(self.today + timedelta(days=90))),
            'past date': dict(booking_date=str(self.today - timedelta(days=1))),
            'not a date': dict(booking_date='tomorrow'),
        }
        for label, overrides in cases.items():
            with self.subTest(label):
                invoice = self._make_invoice(**{
                    'selected_seats': ['R3C1'], **overrides})
                self._pay(invoice)
                self.assertFalse(self._tickets(), label)
                self.assertTrue(invoice.movie_booking_issue, label)

    @mute_logger('odoo.addons.show_booking_management.models.movie_registration')
    def test_price_is_recomputed_and_must_be_covered(self):
        invoice = self._make_invoice()
        self.movie.price = 150.0  # the price rose after the invoice was issued
        self._pay(invoice)
        self.assertFalse(self._tickets(), "The invoice no longer covers the seats")
        self.assertTrue(invoice.movie_booking_issue)

    @mute_logger('odoo.addons.show_booking_management.models.movie_registration')
    def test_cancelled_show_is_not_ticketed(self):
        invoice = self._make_invoice()
        self.movie.action_cancel_show()
        self._pay(invoice)
        self.assertFalse(self._tickets())
        self.assertTrue(invoice.movie_booking_issue)

    def test_completes_a_draft_registration(self):
        draft = self.env['movie.registration'].create({
            'partner_id': self.partner.id, 'movie_id': self.movie.id, 'date': self.today,
            'time_slot_id': self.time_slot.id, 'screen_id': self.screen.id})
        invoice = self._make_invoice(registration_id=str(draft.id))
        self._pay(invoice)
        self.assertEqual(self._tickets(), draft)
        self.assertEqual(draft.state, 'invoiced')
        self.assertEqual(len(draft.seat_ids), 2)
        self.assertEqual(invoice.movie_ticket_id, draft)

    @mute_logger('odoo.addons.show_booking_management.models.movie_registration')
    def test_registration_to_complete_must_still_be_a_draft(self):
        done = self._book_seat_elsewhere('R5C5')
        invoice = self._make_invoice(registration_id=str(done.id))
        self._pay(invoice)
        self.assertEqual(done.no_of_tickets, 1, "An invoiced registration is left untouched")
        self.assertEqual(len(done.seat_ids), 1)
        self.assertTrue(invoice.movie_booking_issue)

    # -- the row lock ------------------------------------------------------------
    def test_screen_row_lock_is_taken_before_the_seat_check(self):
        invoice = self._make_invoice()
        with patch.object(MovieScreen, 'lock_for_update', autospec=True) as lock:
            self._pay(invoice)
        lock.assert_called_once()
        self.assertEqual(lock.call_args.args[0], self.screen)
        self.assertEqual(lock.call_args.kwargs, {'allow_referencing': True})

    @mute_logger('odoo.addons.payment.models.payment_transaction')
    def test_lock_contention_defers_to_the_cron_instead_of_booking(self):
        invoice = self._make_invoice()
        tx = self._pay(invoice, run=False)
        # The production path: synchronous post-processing, deferred to the
        # cron when it fails, and rolled back to a savepoint.
        with patch.object(MovieScreen, 'lock_for_update', autospec=True,
                          side_effect=LockError("locked")):
            tx._try_post_process()
        self.assertFalse(self._tickets())
        self.assertFalse(tx.is_post_processed, "Rolled back: the payment cron retries it")
        self.assertFalse(invoice.movie_booking_issue, "Contention is retried, not reported")
        self.assertTrue(invoice.movie_booking_data)

        self._run_post_processing()  # the retry
        self.assertEqual(len(self._tickets()), 1)
        self.assertTrue(tx.is_post_processed)

    # -- email / QR must not undo the booking -------------------------------------
    @mute_logger('odoo.addons.show_booking_management.models.movie_registration')
    def test_email_failure_keeps_the_booking(self):
        invoice = self._make_invoice()
        with patch.object(MailTemplate, 'send_mail', side_effect=RuntimeError("SMTP down")):
            self._pay(invoice)
        ticket = self._tickets()
        self.assertEqual(len(ticket), 1)
        self.assertEqual(len(ticket.seat_ids), 2)
        self.assertEqual(invoice.movie_ticket_id, ticket)
        self.assertFalse(invoice.movie_booking_issue)

    @mute_logger('odoo.addons.show_booking_management.models.movie_registration')
    def test_qr_failure_keeps_the_booking_and_still_sends_the_email(self):
        invoice = self._make_invoice()
        calls = self._spy_send_mail()
        with patch.object(self.env.registry['movie.registration'], 'get_qr_code_image',
                          side_effect=RuntimeError("no qrcode")):
            self._pay(invoice)
        ticket = self._tickets()
        self.assertEqual(len(ticket), 1)
        self.assertFalse(ticket.qr_code)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][1]['email_values']['attachment_ids'], [(6, 0, [])])

    # -- sender ----------------------------------------------------------------------
    def test_ticket_is_sent_from_the_first_administrator(self):
        invoice = self._make_invoice()
        calls = self._spy_send_mail()
        self._pay(invoice)
        self.assertEqual(calls[0][1]['email_values']['email_from'], 'show.admin@example.com')

    def test_no_administrator_falls_back_to_the_company_email(self):
        self.admin_group.write({'user_ids': [Command.clear()]})
        invoice = self._make_invoice()
        calls = self._spy_send_mail()
        self._pay(invoice)  # v19 raised IndexError here
        self.assertEqual(len(self._tickets()), 1)
        self.assertEqual(calls[0][1]['email_values']['email_from'], 'company@example.com')

    def test_no_administrator_and_no_company_email_still_confirms(self):
        self.admin_group.write({'user_ids': [Command.clear()]})
        self.env.company.email = False
        invoice = self._make_invoice()
        calls = self._spy_send_mail()
        self._pay(invoice)
        self.assertEqual(len(self._tickets()), 1)
        self.assertNotIn('email_from', calls[0][1]['email_values'])
