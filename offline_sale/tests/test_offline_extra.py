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

from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.fields import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


class OfflineSaleCommon(TransactionCase):
    """Shared fixtures for the offline sale tests."""

    def setUp(self):
        super().setUp()
        self.SaleOrder = self.env['sale.order']
        self.product = self.env['product.product'].create({
            'name': 'Offline Extra Product',
            'sale_ok': True,
            'lst_price': 100.0,
            'type': 'consu',
            'invoice_policy': 'order',
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Offline Extra Customer',
            'email': 'offline_extra_customer@test.com',
        })

    def _order_data(self, uid, state='draft', extra=None):
        data = {
            'uid': uid,
            'state': state,
            'partner_id': self.partner.id,
            'lines': [{
                'product_id': self.product.id,
                'qty': 2,
                'price_unit': 100.0,
                'discount': 0,
            }],
        }
        if extra:
            data.update(extra)
        return data


@tagged('post_install', '-at_install', 'offline_sale')
class TestOfflineSyncBranches(OfflineSaleCommon):
    """Tests for the error and update branches of the offline sync."""

    def test_backend_order_not_found(self):
        """A backend order id that does not exist returns an error entry."""
        data = self._order_data('OFF-EXTRA-NOBACKEND', 'confirmed', {
            'backend_order_id': 987654321,
        })
        result = self.SaleOrder.create_from_offline([data])
        self.assertEqual(result['orders'][0]['status'], 'error')

    def test_invalid_line_returns_error_and_does_not_block_others(self):
        """One broken order is reported and the next order is still created."""
        bad = self._order_data('OFF-EXTRA-BAD')
        bad['lines'][0]['product_id'] = 'not-a-number'
        good = self._order_data('OFF-EXTRA-GOOD')
        result = self.SaleOrder.create_from_offline([bad, good])
        statuses = {res['uid']: res['status'] for res in result['orders']}
        self.assertEqual(statuses['OFF-EXTRA-BAD'], 'error')
        self.assertEqual(statuses['OFF-EXTRA-GOOD'], 'created')
        self.assertFalse(self.SaleOrder.search([('offline_uid', '=', 'OFF-EXTRA-BAD')]))
        self.assertTrue(self.SaleOrder.search([('offline_uid', '=', 'OFF-EXTRA-GOOD')]))

    def test_unknown_offline_partner_is_created_from_order_data(self):
        """An OFF- partner missing from partners_data is created from the order."""
        data = self._order_data('OFF-EXTRA-FALLBACK', 'draft', {
            'partner_id': 'OFF-EXTRA-P1',
            'partner_name': 'Fallback Offline Partner',
            'partner_email': 'fallback_offline_partner@test.com',
        })
        result = self.SaleOrder.create_from_offline([data])
        self.assertEqual(result['orders'][0]['status'], 'created')
        order = self.SaleOrder.search([('offline_uid', '=', 'OFF-EXTRA-FALLBACK')])
        self.assertEqual(order.partner_id.name, 'Fallback Offline Partner')

    def test_partner_creation_failure_is_reported(self):
        """A failed partner creation is returned for the partner and the order."""
        data = self._order_data('OFF-EXTRA-PERR', 'draft', {'partner_id': 'OFF-EXTRA-P2'})
        partners_data = [{'id': 'OFF-EXTRA-P2', 'name': 'Broken Partner'}]
        with patch.object(
            type(self.SaleOrder),
            '_get_or_create_offline_partner',
            side_effect=ValueError('boom'),
        ):
            result = self.SaleOrder.create_from_offline([data], partners_data=partners_data)
        self.assertIn('error', result['partners'][0])
        self.assertEqual(result['orders'][0]['status'], 'error')
        self.assertIn('boom', result['orders'][0]['message'])

    def test_draft_order_can_be_confirmed_on_resync(self):
        """A synced draft order is confirmed when it is sent again as confirmed."""
        uid = 'OFF-EXTRA-DRAFT-CONFIRM'
        self.SaleOrder.create_from_offline([self._order_data(uid, 'draft')])
        result = self.SaleOrder.create_from_offline([
            self._order_data(uid, 'confirmed', {'amount_paid': 200.0}),
        ])
        self.assertEqual(result['orders'][0]['status'], 'updated')
        order = self.SaleOrder.search([('offline_uid', '=', uid)])
        self.assertEqual(order.state, 'sale')

    def test_confirmed_order_is_not_recreated_on_resync(self):
        """A confirmed order sent again as draft is reported as existing."""
        uid = 'OFF-EXTRA-EXISTING'
        self.SaleOrder.create_from_offline([
            self._order_data(uid, 'confirmed', {'amount_paid': 200.0}),
        ])
        result = self.SaleOrder.create_from_offline([self._order_data(uid, 'draft')])
        self.assertEqual(result['orders'][0]['status'], 'existing')
        self.assertEqual(self.SaleOrder.search_count([('offline_uid', '=', uid)]), 1)


@tagged('post_install', '-at_install', 'offline_sale')
class TestOfflineReceiptMail(OfflineSaleCommon):
    """Tests for SaleOrder.send_offline_receipt_mail."""

    def setUp(self):
        super().setUp()
        self.offline_uid = 'OFF-EXTRA-RECEIPT'
        self.SaleOrder.create_from_offline([self._order_data(self.offline_uid, 'draft')])
        self.order = self.SaleOrder.search([('offline_uid', '=', self.offline_uid)])
        pdf_patch = patch.object(
            type(self.env['ir.actions.report']),
            '_run_pdf_engine_without_processing',
            return_value=b'%PDF-1.4 offline receipt',
        )
        send_patch = patch.object(type(self.env['mail.mail']), 'send')
        self.pdf_mock = pdf_patch.start()
        self.send_mock = send_patch.start()
        self.addCleanup(pdf_patch.stop)
        self.addCleanup(send_patch.stop)

    def _mails_to(self, email):
        return self.env['mail.mail'].sudo().search([('email_to', '=', email)])

    def test_receipt_is_attached_and_mailed(self):
        """The receipt PDF is attached to the order and an email is queued."""
        email = 'receipt_customer@test.com'
        result = self.SaleOrder.send_offline_receipt_mail(
            self.offline_uid, '<p>Receipt</p>', email)
        self.assertTrue(result)
        self.assertTrue(self.pdf_mock.called)
        call_args, _ = self.pdf_mock.call_args
        self.assertEqual(call_args[0], 'wkhtmltopdf')
        attachment = self.env['ir.attachment'].search([
            ('res_model', '=', 'sale.order'),
            ('res_id', '=', self.order.id),
            ('name', '=', 'Receipt_%s.pdf' % self.offline_uid),
        ])
        self.assertTrue(attachment)
        mail = self._mails_to(email)
        self.assertEqual(len(mail), 1)
        self.assertIn(self.offline_uid, mail.body_html)
        self.assertTrue(self.send_mock.called)

    def test_receipt_html_preserves_style(self):
        """Sanitization preserves <style> tags so the PDF layout is retained."""
        email = 'receipt_style@test.com'
        html_with_style = '<style>.header { color: red; }</style><p>Styled Receipt</p>'
        self.SaleOrder.send_offline_receipt_mail(self.offline_uid, html_with_style, email)
        call_args, _ = self.pdf_mock.call_args
        rendered_html = call_args[1][0]
        self.assertIn('<style>', rendered_html)
        self.assertIn('.header { color: red; }', rendered_html)

    def test_custom_body_is_escaped(self):
        """User supplied text is escaped and system receipt subject is enforced."""
        email = 'receipt_escape@test.com'
        self.SaleOrder.send_offline_receipt_mail(
            self.offline_uid, '<p>Receipt</p>', email,
            subject='Custom subject', body='<script>alert(1)</script>\nThanks')
        mail = self._mails_to(email)
        self.assertEqual(mail.subject, 'Transaction Receipt - %s' % self.offline_uid)
        self.assertNotIn('<script>', mail.body_html)

    def test_invalid_email_is_rejected(self):
        """An invalid email address raises a UserError and sends nothing."""
        with self.assertRaises(UserError):
            self.SaleOrder.send_offline_receipt_mail(
                self.offline_uid, '<p>Receipt</p>', 'not an email')
        self.assertFalse(self.send_mock.called)

    def test_receipt_without_email_is_only_attached(self):
        """Without an email address the receipt is attached but not mailed."""
        mails_before = self.env['mail.mail'].sudo().search_count([])
        self.SaleOrder.send_offline_receipt_mail(self.offline_uid, '<p>Receipt</p>', '')
        self.assertEqual(self.env['mail.mail'].sudo().search_count([]), mails_before)
        self.assertTrue(self.env['ir.attachment'].search([
            ('res_model', '=', 'sale.order'),
            ('res_id', '=', self.order.id),
        ]))

    def test_receipt_for_unsynced_order(self):
        """A receipt for an order that is not synced yet has no linked record."""
        uid = 'OFF-EXTRA-UNSYNCED'
        email = 'receipt_unsynced@test.com'
        self.SaleOrder.send_offline_receipt_mail(uid, '<p>Receipt</p>', email)
        attachment = self.env['ir.attachment'].search([('name', '=', 'Receipt_%s.pdf' % uid)])
        self.assertTrue(attachment)
        self.assertFalse(attachment.res_id)
        self.assertEqual(len(self._mails_to(email)), 1)

    def test_receipt_html_strips_scripts_and_unsafe_attributes(self):
        """Unsafe script tags and event handlers are eliminated while styles are kept."""
        email = 'receipt_security@test.com'
        html_unsafe = (
            '<style>.title { font-weight: bold; }</style>'
            '<script>alert("evil")</script>'
            '<p onclick="stealData()" onerror="bad()">Receipt Text</p>'
        )
        self.SaleOrder.send_offline_receipt_mail(self.offline_uid, html_unsafe, email)
        call_args, _ = self.pdf_mock.call_args
        rendered_html = call_args[1][0]
        self.assertIn('<style>', rendered_html)
        self.assertIn('.title { font-weight: bold; }', rendered_html)
        self.assertNotIn('<script>', rendered_html)
        self.assertNotIn('alert("evil")', rendered_html)
        self.assertNotIn('onclick', rendered_html)

    def test_receipt_send_by_sales_user_without_access_error(self):
        """Normal sales users can email receipts via mail.template without AccessError."""
        salesman_group = self.env.ref('sales_team.group_sale_salesman')
        sales_user = self.env['res.users'].create({
            'name': 'Test Salesman User',
            'login': 'test_salesman_user',
            'email': 'salesman@test.com',
            'group_ids': [Command.set([salesman_group.id, self.env.ref('base.group_user').id])],
        })
        email = 'customer_from_salesman@test.com'
        result = self.SaleOrder.with_user(sales_user).send_offline_receipt_mail(
            self.offline_uid, '<p>Receipt Content</p>', email)
        self.assertTrue(result)
        mail = self._mails_to(email)
        self.assertEqual(len(mail), 1)


@tagged('post_install', '-at_install', 'offline_sale')
class TestOfflineEmployees(OfflineSaleCommon):
    """Tests for the employee data sent to the terminal."""

    def test_employees_are_returned_as_a_list(self):
        """get_offline_data always returns the employees as a list."""
        data = self.SaleOrder.get_offline_data()
        self.assertIsInstance(data['employees'], list)

    def test_employee_pin_is_never_returned(self):
        """Employees are sent with a boolean flag, never raw PIN or hashes."""
        if 'hr.employee' not in self.env:
            self.skipTest('hr is not installed')
        emp = self.env['hr.employee'].create({'name': 'Offline Pin Employee', 'pin': '4321'})
        employees = self.SaleOrder._get_offline_employees()
        employee = next(e for e in employees if e['id'] == emp.id)
        self.assertIsInstance(employee['pin'], bool)
        self.assertTrue(employee['pin'])
        self.assertNotIn('pin_salt', employee)
        self.assertNotIn('pin_hash', employee)

    def test_check_offline_employee_pin(self):
        """Server-side PIN verification accurately checks PIN without exposing it."""
        if 'hr.employee' not in self.env:
            self.skipTest('hr is not installed')
        emp = self.env['hr.employee'].create({'name': 'Offline Pin Employee 2', 'pin': '5678'})
        self.assertTrue(self.SaleOrder.check_offline_employee_pin(emp.id, '5678'))
        self.assertFalse(self.SaleOrder.check_offline_employee_pin(emp.id, '0000'))
        self.assertFalse(self.SaleOrder.check_offline_employee_pin(emp.id, ''))

    def test_check_offline_employee_pin_rate_limiting(self):
        """After 5 consecutive failed attempts, rate limit raises UserError."""
        if 'hr.employee' not in self.env:
            self.skipTest('hr is not installed')
        emp = self.env['hr.employee'].create({'name': 'Rate Limit Employee', 'pin': '9999'})
        # 5 failed attempts
        for _ in range(5):
            self.assertFalse(self.SaleOrder.check_offline_employee_pin(emp.id, '1111'))
        # 6th attempt triggers rate limit
        with self.assertRaises(UserError):
            self.SaleOrder.check_offline_employee_pin(emp.id, '1111')
