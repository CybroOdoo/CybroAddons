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
#############################################################################
from datetime import timedelta

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.fields import Command
from odoo.tests import Form, TransactionCase, new_test_user, tagged

PARAM = 'sale_invoice_due_date_reminder.'


@tagged('post_install', '-at_install')
class TestDueDateReminder(TransactionCase):
    """Test the due date reminders of the sale orders and invoices."""

    @classmethod
    def setUpClass(cls):
        """Enable the reminders 3 days before the due date."""
        super().setUpClass()
        params = cls.env['ir.config_parameter'].sudo()
        params.set_bool(PARAM + 'reminder_sale', True)
        params.set_int(PARAM + 'set_date_sales', 3)
        params.set_bool(PARAM + 'reminder_invoicing', True)
        params.set_int(PARAM + 'set_date_invoicing', 3)
        cls.today = fields.Date.context_today(cls.env.user)
        cls.partner = cls.env['res.partner'].create({
            'name': 'Anna Smith', 'email': 'anna@example.com'})
        cls.product = cls.env['product.product'].create({
            'name': 'Consulting', 'type': 'service', 'invoice_policy': 'order',
            'list_price': 100.0})

    def _invoice(self, due_in, post=True):
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_date': self.today,
            'invoice_date_due': self.today + timedelta(days=due_in),
            'invoice_line_ids': [Command.create({
                'product_id': self.product.id, 'quantity': 1, 'price_unit': 100})],
        })
        if post:
            invoice.action_post()
            invoice.invoice_date_due = self.today + timedelta(days=due_in)
        return invoice

    def _order(self, due_in, confirm=True):
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'due_date_order': self.today + timedelta(days=due_in),
            'order_line': [Command.create({
                'product_id': self.product.id, 'product_uom_qty': 1})],
        })
        if confirm:
            order.action_confirm()
        return order

    def _mails(self, record):
        return self.env['mail.mail'].search(
            [('model', '=', record._name), ('res_id', '=', record.id)])

    def test_01_invoice_reminder(self):
        """An unpaid invoice due within the days gets one reminder, logged in
        the chatter of the invoice, with the right amounts."""
        invoice = self._invoice(due_in=2)
        self.env['account.move'].action_send_mail_invoice()
        mail = self._mails(invoice)
        self.assertEqual(len(mail), 1)
        self.assertEqual(mail.recipient_ids, self.partner)
        self.assertIn(invoice.name, mail.subject)
        self.assertIn('Amount Due', mail.body_html)
        self.assertEqual(invoice.due_reminder_date, invoice.invoice_date_due)
        self.assertIn(mail.mail_message_id, invoice.message_ids,
                      "The reminder is logged in the chatter")
        self.assertFalse(mail.auto_delete,
                         "The reminder stays in the chatter once sent")
        self.env['account.move'].action_send_mail_invoice()
        self.assertEqual(len(self._mails(invoice)), 1, "Sent once per due date")

    def test_02_invoice_not_reminded(self):
        """Invoices due later, draft or paid get no reminder."""
        later = self._invoice(due_in=10)
        draft = self._invoice(due_in=2, post=False)
        paid = self._invoice(due_in=2)
        self.env['account.payment.register'].with_context(
            active_model='account.move', active_ids=paid.ids,
        ).create({})._create_payments()
        self.assertIn(paid.payment_state, ('paid', 'in_payment'))
        self.env['account.move'].action_send_mail_invoice()
        for invoice in (later, draft, paid):
            self.assertFalse(self._mails(invoice), invoice.name)

    def test_03_missed_day_and_new_due_date(self):
        """A reminder missed on the exact day is still sent while the due
        date is close, and a new due date gets a new reminder."""
        invoice = self._invoice(due_in=1)
        self.env['account.move'].action_send_mail_invoice()
        self.assertEqual(len(self._mails(invoice)), 1)
        invoice.invoice_date_due = self.today + timedelta(days=2)
        self.env['account.move'].action_send_mail_invoice()
        self.assertEqual(len(self._mails(invoice)), 2)

    def test_04_disabled(self):
        """No reminder when the settings are disabled."""
        self.env['ir.config_parameter'].sudo().set_bool(PARAM + 'reminder_invoicing', False)
        self.env['ir.config_parameter'].sudo().set_bool(PARAM + 'reminder_sale', False)
        invoice, order = self._invoice(due_in=2), self._order(due_in=2)
        self.env['account.move'].action_send_mail_invoice()
        self.env['sale.order'].action_send_mail_sale_order()
        self.assertFalse(self._mails(invoice))
        self.assertFalse(self._mails(order))

    def test_05_sale_order_reminder(self):
        """An order to invoice or a quotation due within the days gets one
        reminder; cancelled and fully invoiced orders get none."""
        to_invoice = self._order(due_in=2)
        quotation = self._order(due_in=3, confirm=False)
        cancelled = self._order(due_in=2, confirm=False)
        cancelled.action_cancel()
        invoiced = self._order(due_in=2)
        invoiced._create_invoices().action_post()
        later = self._order(due_in=10)
        self.env['sale.order'].action_send_mail_sale_order()
        for order in (to_invoice, quotation):
            mail = self._mails(order)
            self.assertEqual(len(mail), 1, order.name)
            self.assertIn(order.name, mail.subject)
            self.assertEqual(order.due_reminder_date, order.due_date_order)
        for order in (cancelled, invoiced, later):
            self.assertFalse(self._mails(order), order.name)
        self.env['sale.order'].action_send_mail_sale_order()
        self.assertEqual(len(self._mails(to_invoice)), 1, "Sent once per due date")

    def test_06_settings(self):
        """The settings store the reminders, and the days cannot be
        negative."""
        settings = self.env['res.config.settings'].create({
            'reminder_sales': True, 'set_date_sales': 5,
            'reminder_invoicing': True, 'set_date_invoicing': 7})
        settings.execute()
        params = self.env['ir.config_parameter'].sudo()
        self.assertEqual(params.get_int(PARAM + 'set_date_sales'), 5)
        self.assertEqual(params.get_int(PARAM + 'set_date_invoicing'), 7)
        with self.assertRaises(ValidationError):
            self.env['res.config.settings'].create({'set_date_sales': -1})

    def test_07_salesperson(self):
        """A salesperson sets the due date on the order form, and the
        scheduled action reminds the customer."""
        user = new_test_user(
            self.env, login='due_salesman',
            groups='base.group_user,sales_team.group_sale_salesman')
        with Form(self.env['sale.order'].with_user(user)) as order_form:
            order_form.partner_id = self.partner
            order_form.due_date_order = self.today + timedelta(days=1)
            with order_form.order_line.new() as line:
                line.product_id = self.product
        order = order_form.save()
        order.action_confirm()
        self.env['sale.order'].action_send_mail_sale_order()
        self.assertEqual(len(self._mails(order)), 1)
