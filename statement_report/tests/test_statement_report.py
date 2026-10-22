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
#############################################################################
import json
from unittest.mock import MagicMock, patch

from odoo import Command, fields
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import ValidationError
from odoo.tests import tagged

MAIL_SEND = 'odoo.addons.mail.models.mail_mail.MailMail.send'


@tagged('post_install', '-at_install')
class TestStatementReport(AccountTestInvoicingCommon):
    """ Tests for the customer/vendor payment statement report """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company.external_report_layout_id = cls.env.ref(
            'web.external_layout_standard')
        cls.customer = cls.env['res.partner'].create({
            'name': 'Statement Customer',
            'email': 'customer@example.com',
            'street': '1 Main Street',
            'street2': 'Block B',
            'city': 'Kochi',
            'zip': '682001',
        })
        cls.vendor = cls.env['res.partner'].create({
            'name': 'Statement Vendor',
            'email': 'vendor@example.com',
            'street': '2 Market Road',
            'city': 'Kochi',
        })
        cls.empty_partner = cls.env['res.partner'].create({
            'name': 'Partner Without Statement',
            'email': 'empty@example.com',
        })
        cls.invoice = cls._create_move(cls.customer, 'out_invoice', 100.0)
        cls.bill = cls._create_move(cls.vendor, 'in_invoice', 60.0)

    @classmethod
    def _create_move(cls, partner, move_type, amount):
        move = cls.env['account.move'].create({
            'move_type': move_type,
            'partner_id': partner.id,
            'invoice_date': fields.Date.today(),
            'invoice_date_due': fields.Date.today(),
            'invoice_line_ids': [Command.create({
                'name': 'Statement test line',
                'quantity': 1,
                'price_unit': amount,
                'tax_ids': [Command.clear()],
            })],
        })
        move.action_post()
        return move

    # ------------------------------------------------------------------
    # Computed fields and query helpers
    # ------------------------------------------------------------------
    def test_compute_statement_ids(self):
        """ Only unpaid posted invoices/bills of the partner are listed """
        self.assertEqual(self.customer.customer_report_ids, self.invoice)
        self.assertFalse(self.customer.vendor_statement_ids)
        self.assertEqual(self.vendor.vendor_statement_ids, self.bill)
        self.assertFalse(self.vendor.customer_report_ids)
        self.assertFalse(self.empty_partner.customer_report_ids)
        self.assertFalse(self.empty_partner.vendor_statement_ids)

    def test_query_helpers(self):
        """ The query helpers are built for the right partner and company """
        self.env.cr.execute(self.customer.main_query())
        rows = self.env.cr.dictfetchall()
        self.assertEqual([row['name'] for row in rows], [self.invoice.name])
        self.env.cr.execute(self.customer.amount_query())
        self.assertAlmostEqual(
            float(self.env.cr.dictfetchall()[0]['total']), 100.0)
        self.env.cr.execute(
            self.env['res.partner'].amount_query(partner_id=self.vendor.id))
        self.assertAlmostEqual(
            float(self.env.cr.dictfetchall()[0]['total']), -60.0)

    # ------------------------------------------------------------------
    # Customer actions
    # ------------------------------------------------------------------
    def test_action_print_pdf(self):
        action = self.customer.action_print_pdf()
        self.assertEqual(action['type'], 'ir.actions.report')
        self.assertEqual(action['data']['customer'], self.customer.display_name)
        self.assertAlmostEqual(float(action['data']['total']), 100.0)
        self.assertEqual(len(action['data']['my_data']), 1)
        self.assertEqual(action['data']['my_data'][0]['name'], self.invoice.name)

    def test_action_print_xlsx(self):
        action = self.customer.action_print_xlsx()
        self.assertEqual(action['report_type'], 'xlsx')
        options = json.loads(action['data']['options'])
        self.assertEqual(options['customer'], self.customer.display_name)
        self.assertAlmostEqual(float(options['balance']), 100.0)

    def test_action_share_pdf(self):
        with patch(MAIL_SEND):
            result = self.customer.action_share_pdf()
        self.assertEqual(result['tag'], 'display_notification')
        mail = self.env['mail.mail'].search([
            ('email_to', '=', 'customer@example.com'),
            ('subject', '=', 'Payment Statement Report')])
        self.assertEqual(len(mail), 1)
        self.assertEqual(len(mail.attachment_ids), 1)
        self.assertEqual(mail.attachment_ids.mimetype, 'application/pdf')

    def test_action_share_xlsx(self):
        with patch(MAIL_SEND):
            result = self.customer.action_share_xlsx()
        self.assertEqual(result['tag'], 'display_notification')
        mail = self.env['mail.mail'].search([
            ('email_to', '=', 'customer@example.com'),
            ('subject', '=', 'Payment Statement Report')])
        self.assertEqual(len(mail), 1)
        self.assertTrue(mail.attachment_ids)

    # ------------------------------------------------------------------
    # Vendor actions
    # ------------------------------------------------------------------
    def test_vendor_actions(self):
        action = self.vendor.action_vendor_print_pdf()
        self.assertEqual(action['type'], 'ir.actions.report')
        self.assertAlmostEqual(float(action['data']['total']), -60.0)
        action = self.vendor.action_vendor_print_xlsx()
        self.assertEqual(action['report_type'], 'xlsx')
        with patch(MAIL_SEND):
            result = self.vendor.action_vendor_share_pdf()
            self.assertEqual(result['tag'], 'display_notification')
            result = self.vendor.action_vendor_share_xlsx()
            self.assertEqual(result['tag'], 'display_notification')
        mails = self.env['mail.mail'].search([
            ('email_to', '=', 'vendor@example.com')])
        self.assertEqual(len(mails), 2)

    # ------------------------------------------------------------------
    # Errors when there is nothing to report
    # ------------------------------------------------------------------
    def test_no_statement_raises(self):
        partner = self.empty_partner
        for method in (
                'action_share_pdf', 'action_print_pdf', 'action_print_xlsx',
                'action_share_xlsx', 'action_vendor_print_pdf',
                'action_vendor_share_pdf', 'action_vendor_print_xlsx',
                'action_vendor_share_xlsx'):
            with self.subTest(method=method):
                with self.assertRaises(ValidationError):
                    getattr(partner, method)()

    # ------------------------------------------------------------------
    # XLSX rendering
    # ------------------------------------------------------------------
    def test_get_xlsx_report(self):
        options = json.loads(self.customer.action_print_xlsx()['data']['options'])
        response = MagicMock()
        self.customer.get_xlsx_report(options, response)
        content = response.stream.write.call_args[0][0]
        self.assertTrue(content.startswith(b'PK'))

    def test_get_xlsx_report_without_address(self):
        """ Optional address lines are skipped when empty """
        data = {
            'customer': 'No Address Partner',
            'street': False, 'street2': False, 'city': False,
            'state': False, 'zip': False,
            'my_data': [{
                'name': 'INV/0001',
                'invoice_date': '2026-09-17',
                'invoice_date_due': '2026-09-17',
                'sub_total': 100.0, 'amount_due': 100.0, 'balance': 100.0,
            }],
            'total': 100.0, 'balance': 100.0,
            'currency': '$',
        }
        response = MagicMock()
        self.env['res.partner'].get_xlsx_report(data, response)
        self.assertTrue(response.stream.write.called)

    # ------------------------------------------------------------------
    # Scheduled actions
    # ------------------------------------------------------------------
    def test_auto_week_statement_report(self):
        with patch(MAIL_SEND):
            self.env['res.partner'].auto_week_statement_report()
        mail = self.env['mail.mail'].search([
            ('email_to', '=', 'customer@example.com'),
            ('subject', '=', 'Weekly Payment Statement Report')])
        self.assertEqual(len(mail), 1)
        self.assertEqual(len(mail.attachment_ids), 2)

    def test_auto_month_statement_report(self):
        with patch(MAIL_SEND):
            self.env['res.partner'].auto_month_statement_report()
        mail = self.env['mail.mail'].search([
            ('email_to', '=', 'vendor@example.com'),
            ('subject', '=', 'Monthly Payment Statement Report')])
        self.assertEqual(len(mail), 1)
        self.assertEqual(len(mail.attachment_ids), 2)
