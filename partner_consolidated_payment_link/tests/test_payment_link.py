# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
import werkzeug.exceptions

from odoo.tests import TransactionCase, tagged
from odoo.exceptions import UserError

from odoo.addons.partner_consolidated_payment_link.controllers import (
    partner_consolidated_payment_link as pcpl_ctrl,
)


@tagged('post_install', '-at_install')
class TestPartnerConsolidatedPaymentLink(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env
        cls.company = cls.env.company

        # Create a test partner
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner',
            'email': 'test@example.com',
        })

        # Product and account setup
        cls.product = cls.env['product.product'].search([], limit=1)
        cls.account = cls.env['account.account'].search(
            [('account_type', '=', 'asset_receivable')], limit=1
        )
        if not cls.account:
            cls.account = cls.env['account.account'].create({
                'name': 'Receivable Test',
                'code': 'RECVTEST',
                'account_type': 'asset_receivable',
                'reconcile': True,
            })

        cls.income_account = cls.env['account.account'].search(
            [('account_type', '=', 'income')], limit=1
        )
        if not cls.income_account:
            cls.income_account = cls.env['account.account'].create({
                'name': 'Income Test',
                'code': 'INCOTEST',
                'account_type': 'income',
            })

        # Create an unpaid invoice
        unpaid_line_vals = {
            'name': 'Test Unpaid Line',
            'quantity': 1,
            'price_unit': 100.0,
            'account_id': cls.income_account.id,
        }
        if cls.product:
            unpaid_line_vals['product_id'] = cls.product.id

        cls.invoice_unpaid = cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': cls.partner.id,
            'invoice_date': '2023-01-01',
            'invoice_line_ids': [(0, 0, unpaid_line_vals)]
        })
        cls.invoice_unpaid.action_post()

        # Create a paid invoice
        paid_line_vals = {
            'name': 'Test Paid Line',
            'quantity': 1,
            'price_unit': 50.0,
            'account_id': cls.income_account.id,
        }
        if cls.product:
            paid_line_vals['product_id'] = cls.product.id

        cls.invoice_paid = cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': cls.partner.id,
            'invoice_date': '2023-01-02',
            'invoice_line_ids': [(0, 0, paid_line_vals)]
        })
        cls.invoice_paid.action_post()

        # Register payment for the paid invoice
        payment_register = cls.env['account.payment.register'].with_context(
            active_model='account.move',
            active_ids=cls.invoice_paid.ids
        ).create({})
        payment_register._create_payments()

    def test_01_get_overdue_amls(self):
        """Test fetching overdue account.move.line records"""
        overdue_amls = self.partner.get_overdue_amls()
        self.assertTrue(any(line.move_id == self.invoice_unpaid for line in overdue_amls))
        self.assertFalse(any(line.move_id == self.invoice_paid for line in overdue_amls))

    def test_02_get_total_due(self):
        """Test getting total due amount for a partner"""
        total_due = self.partner.get_total_due(self.company)
        self.assertTrue(total_due > 0)
        self.assertEqual(total_due, self.invoice_unpaid.amount_residual)

    def test_03_get_total_due_in_company_currency(self):
        """Test getting total due in company currency"""
        total_due_company_curr = self.partner.get_total_due_in_company_currency()
        self.assertTrue(total_due_company_curr > 0)
        self.assertEqual(total_due_company_curr, self.invoice_unpaid.amount_residual)

    def test_04_get_access_token(self):
        """Test getting and validating access tokens"""
        amount_residual = 100.0
        currency_id = self.company.currency_id.id
        token = self.partner.get_access_token(amount_residual, currency_id)
        self.assertTrue(isinstance(token, str) and len(token) > 0)

        consolidated_token = self.partner._get_consolidated_payment_token()
        self.assertTrue(isinstance(consolidated_token, str) and len(consolidated_token) > 0)
        self.assertTrue(self.partner._check_consolidated_payment_token(consolidated_token))
        self.assertFalse(self.partner._check_consolidated_payment_token('invalid_token'))
        self.assertFalse(self.partner._check_consolidated_payment_token(''))

    def test_05_wizard_action_send_mail(self):
        """Test the send payment link wizard"""
        partner_no_email = self.env['res.partner'].create({'name': 'No Email'})
        wizard = self.env['send.payment.link.wizard'].with_context(
            active_id=partner_no_email.id
        ).create({})
        with self.assertRaises(UserError):
            wizard.action_send_mail()

        wizard_valid = self.env['send.payment.link.wizard'].with_context(
            active_id=self.partner.id
        ).create({})
        result = wizard_valid.action_send_mail()
        self.assertEqual(result.get('type'), 'ir.actions.act_window_close')

    def test_06_account_payment_action_post(self):
        """Test account payment action post linking moves via payment transaction"""
        reference = 'test-consolidated-ref'
        self.invoice_unpaid.write({'consolidated_payment_link_ref': reference})

        provider = self.env['payment.provider'].search([], limit=1)
        if not provider:
            provider = self.env['payment.provider'].create({
                'name': 'Test Provider',
                'code': 'none',
                'state': 'test',
            })

        payment_method = self.env['payment.method'].search([], limit=1)
        if not payment_method:
            payment_method = self.env['payment.method'].create({
                'name': 'Test Payment Method',
                'code': 'test_method',
            })

        tx = self.env['payment.transaction'].create({
            'amount': 100.0,
            'currency_id': self.company.currency_id.id,
            'provider_id': provider.id,
            'payment_method_id': payment_method.id,
            'reference': reference,
            'partner_id': self.partner.id,
        })

        payment = self.env['account.payment'].create({
            'partner_id': self.partner.id,
            'amount': 100.0,
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'payment_transaction_id': tx.id,
        })
        payment.action_post()

        self.assertIn(payment, self.invoice_unpaid.matched_payment_ids)
        self.assertIn(self.invoice_unpaid, tx.invoice_ids)

    def test_07_account_payment_without_transaction(self):
        """Test payment post without payment transaction proceeds normally"""
        payment = self.env['account.payment'].create({
            'partner_id': self.partner.id,
            'amount': 50.0,
            'payment_type': 'inbound',
            'partner_type': 'customer',
        })
        payment.action_post()
        self.assertIn(payment.state, ('posted', 'in_process'))


@tagged('post_install', '-at_install')
class TestConsolidatedPaymentLinkController(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.controller = pcpl_ctrl.PartnerConsolidatedPaymentLinkController()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Controller Test Partner',
            'email': 'controller@example.com',
        })
        cls.income_account = cls.env['account.account'].search(
            [('account_type', '=', 'income')], limit=1
        )
        if not cls.income_account:
            cls.income_account = cls.env['account.account'].create({
                'name': 'Controller Income',
                'code': 'CINCO',
                'account_type': 'income',
            })
        cls.invoice = cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': cls.partner.id,
            'invoice_date': '2023-01-01',
            'invoice_line_ids': [(0, 0, {
                'name': 'Service Fee',
                'quantity': 1,
                'price_unit': 200.0,
                'account_id': cls.income_account.id,
            })]
        })
        cls.invoice.action_post()

    def test_01_unknown_partner(self):
        """Unknown partner id raises 404 NotFound"""
        with self.assertRaises(werkzeug.exceptions.NotFound):
            self.controller.create_payment_link(
                999999999,
                access_token='dummy',
                env=self.env
            )

    def test_02_invalid_token(self):
        """Invalid access token raises 404 NotFound"""
        with self.assertRaises(werkzeug.exceptions.NotFound):
            self.controller.create_payment_link(
                self.partner.id,
                access_token='invalid_token_123',
                env=self.env
            )

    def test_03_valid_token_redirect_and_reference_reuse(self):
        """Valid token redirects to /payment/pay and reuses reference on subsequent calls"""
        token = self.partner._get_consolidated_payment_token()
        response = self.controller.create_payment_link(
            self.partner.id,
            access_token=token,
            env=self.env
        )
        self.assertEqual(response.status_code, 302)
        redirect_location = response.headers.get('Location')
        self.assertIn('/payment/pay?', redirect_location)
        self.assertIn(f'partner_id={self.partner.id}', redirect_location)

        initial_ref = self.invoice.consolidated_payment_link_ref
        self.assertTrue(initial_ref)
        self.assertIn(f'reference={initial_ref}', redirect_location)

        # Second call should reuse the same reference
        response_second = self.controller.create_payment_link(
            self.partner.id,
            access_token=token,
            env=self.env
        )
        self.assertEqual(response_second.status_code, 302)
        second_location = response_second.headers.get('Location')
        self.assertIn(f'reference={initial_ref}', second_location)
        self.assertEqual(self.invoice.consolidated_payment_link_ref, initial_ref)

    def test_04_no_due_settled(self):
        """Partner with no unpaid invoices returns settled message"""
        partner_no_dues = self.env['res.partner'].create({
            'name': 'Settled Partner',
            'email': 'settled@example.com',
        })
        token = partner_no_dues._get_consolidated_payment_token()
        result = self.controller.create_payment_link(
            partner_no_dues.id,
            access_token=token,
            env=self.env
        )
        data = result.get_data(as_text=True) if hasattr(result, 'get_data') else result
        self.assertEqual(data, 'All outstanding invoices are settled.')
