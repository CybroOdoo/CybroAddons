# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gee Paul Joby (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0(OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
################################################################################
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlsplit

from odoo.exceptions import UserError
from odoo.tests import HttpCase, tagged
from odoo.addons.account_payment.tests.common import AccountPaymentCommon
from odoo.addons.payment import utils as payment_utils


@tagged('post_install', '-at_install')
class TestPartnerConsolidatedPaymentLink(AccountPaymentCommon):
    """Test the consolidated payment link helpers, payment matching and wizard."""

    @classmethod
    def setUpClass(cls):
        """Create a customer with a child contact and some posted invoices."""
        super().setUpClass()
        cls.customer = cls.env['res.partner'].create({
            'name': 'Consolidated Customer',
            'email': 'consolidated.customer@example.com',
        })
        cls.child_contact = cls.env['res.partner'].create({
            'name': 'Consolidated Child Contact',
            'parent_id': cls.customer.id,
        })
        cls.other_customer = cls.env['res.partner'].create({
            'name': 'Other Customer',
        })
        cls.invoice_parent = cls.init_invoice(
            'out_invoice', partner=cls.customer, amounts=[100.0], post=True)
        cls.invoice_child = cls.init_invoice(
            'out_invoice', partner=cls.child_contact, amounts=[200.0], post=True)
        cls.invoice_other = cls.init_invoice(
            'out_invoice', partner=cls.other_customer, amounts=[50.0], post=True)
        cls.invoice_draft = cls.init_invoice(
            'out_invoice', partner=cls.customer, amounts=[75.0])
        cls.company = cls.env.company

    def _receivable_lines(self, invoices):
        """Return the receivable lines of the given invoices."""
        return invoices.line_ids.filtered(
            lambda line: line.account_id.account_type == 'asset_receivable')

    def test_get_overdue_amls_domain(self):
        """The domain filters on posted, unpaid customer invoices of the partner tree."""
        domain = self.customer._get_overdue_amls_domain()
        self.assertIn(('move_id.state', '=', 'posted'), domain)
        self.assertIn(('move_id.move_type', '=', 'out_invoice'), domain)
        self.assertIn(('reconciled', '=', False), domain)
        partner_leaf = next(leaf for leaf in domain if leaf[0] == 'move_id.partner_id')
        self.assertIn(self.customer.id, partner_leaf[2])
        self.assertIn(self.child_contact.id, partner_leaf[2])
        self.assertNotIn(self.other_customer.id, partner_leaf[2])

    def test_get_overdue_amls(self):
        """Only receivable lines of posted invoices of the partner and its children are returned."""
        amls = self.customer.get_overdue_amls()
        self.assertEqual(
            amls, self._receivable_lines(self.invoice_parent + self.invoice_child))
        self.assertFalse(amls & self._receivable_lines(self.invoice_other))
        self.assertFalse(amls.move_id & self.invoice_draft)

    def test_get_overdue_amls_excludes_paid_invoice(self):
        """A fully paid invoice is no longer part of the overdue lines."""
        self.env['account.payment.register'].with_context(
            active_model='account.move', active_ids=self.invoice_parent.ids,
        ).create({})._create_payments()
        amls = self.customer.get_overdue_amls()
        self.assertEqual(amls, self._receivable_lines(self.invoice_child))

    def test_get_total_due(self):
        """The total due sums the residual amounts for the given company only."""
        self.assertAlmostEqual(self.customer.get_total_due(self.company), 300.0)
        self.assertAlmostEqual(self.other_customer.get_total_due(self.company), 50.0)
        other_company = self.env['res.company'].create({'name': 'Other Company'})
        self.assertAlmostEqual(self.customer.get_total_due(other_company), 0.0)

    def test_get_total_due_in_company_currency(self):
        """Foreign currency invoices are converted into the company currency."""
        foreign_currency = self.setup_other_currency('EUR')
        foreign_invoice = self.init_invoice(
            'out_invoice', partner=self.customer, amounts=[200.0],
            currency=foreign_currency, post=True)
        expected = 300.0 + self._receivable_lines(foreign_invoice).amount_residual
        self.assertAlmostEqual(
            self.customer.get_total_due_in_company_currency(), expected)
        self.assertNotEqual(
            self._receivable_lines(foreign_invoice).amount_residual, 200.0)

    def test_get_access_token(self):
        """The access token matches the one generated by the payment utils."""
        currency = self.company.currency_id
        with patch.object(payment_utils, 'request', Mock(env=self.env)):
            token = self.customer.get_access_token(300.0, currency.id)
        self.assertTrue(token)
        self.assertEqual(
            token,
            self._generate_test_access_token(self.customer.id, 300.0, currency.id))

    def test_action_post_links_consolidated_invoices(self):
        """Posting a payment of a consolidated transaction links the tagged invoices."""
        invoices = self.invoice_parent + self.invoice_child
        reference = 'CONSOLIDATED-TEST-REF'
        invoices.write({'consolidated_payment_link_ref': reference})
        transaction = self._create_transaction(
            'redirect', reference=reference, amount=300.0,
            currency_id=self.company.currency_id.id, partner_id=self.customer.id)
        payment = self.env['account.payment'].create({
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'partner_id': self.customer.id,
            'amount': 300.0,
            'journal_id': self.company_data['default_journal_bank'].id,
            'payment_transaction_id': transaction.id,
        })
        payment.action_post()
        self.assertEqual(transaction.invoice_ids, invoices)
        for invoice in invoices:
            self.assertIn(payment, invoice.matched_payment_ids)
        self.assertNotIn(payment, self.invoice_other.matched_payment_ids)

    def test_action_post_without_transaction(self):
        """Posting a payment without transaction does not link any invoice."""
        self.invoice_parent.consolidated_payment_link_ref = 'CONSOLIDATED-TEST-REF'
        payment = self.env['account.payment'].create({
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'partner_id': self.customer.id,
            'amount': 100.0,
            'journal_id': self.company_data['default_journal_bank'].id,
        })
        payment.action_post()
        self.assertNotEqual(payment.state, 'draft')
        self.assertNotIn(payment, self.invoice_parent.matched_payment_ids)

    def test_action_post_matches_suffixed_reference(self):
        """A transaction whose reference got a numeric suffix still matches the invoices."""
        reference = 'CONSOLIDATED-TEST-REF'
        self.invoice_parent.consolidated_payment_link_ref = reference
        transaction = self._create_transaction(
            'redirect', reference=f'{reference}-1', amount=100.0,
            currency_id=self.company.currency_id.id, partner_id=self.customer.id)
        payment = self.env['account.payment'].create({
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'partner_id': self.customer.id,
            'amount': 100.0,
            'journal_id': self.company_data['default_journal_bank'].id,
            'payment_transaction_id': transaction.id,
        })
        payment.action_post()
        self.assertEqual(transaction.invoice_ids, self.invoice_parent)
        self.assertEqual(self.invoice_parent.matched_payment_ids, payment)

    def test_consolidated_payment_token(self):
        """The link token is only valid for its own partner."""
        token = self.customer._get_consolidated_payment_token()
        self.assertTrue(self.customer._check_consolidated_payment_token(token))
        self.assertFalse(self.customer._check_consolidated_payment_token(None))
        self.assertFalse(self.customer._check_consolidated_payment_token('wrong'))
        self.assertFalse(self.other_customer._check_consolidated_payment_token(token))
        url = self.customer._get_consolidated_payment_url()
        self.assertIn(f'/payment/balance/{self.customer.id}?access_token={token}', url)

    def test_consolidated_payment_reference_is_reused(self):
        """The reference is created once and reused while the invoices share it."""
        invoices = self.invoice_parent + self.invoice_child
        reference = self.customer._get_consolidated_payment_reference(invoices)
        self.assertTrue(reference)
        self.assertEqual(set(invoices.mapped('consolidated_payment_link_ref')), {reference})
        self.assertEqual(
            self.customer._get_consolidated_payment_reference(invoices), reference)
        new_invoice = self.init_invoice(
            'out_invoice', partner=self.customer, amounts=[10.0], post=True)
        new_reference = self.customer._get_consolidated_payment_reference(
            invoices + new_invoice)
        self.assertNotEqual(new_reference, reference)
        self.assertEqual(
            set((invoices + new_invoice).mapped('consolidated_payment_link_ref')),
            {new_reference})

    def test_prepare_consolidated_payment_values(self):
        """The payment values hold the total due, the currency and the reference."""
        values = self.customer._prepare_consolidated_payment_values(self.company)
        self.assertAlmostEqual(values['amount'], 300.0)
        self.assertEqual(values['currency'], self.company.currency_id)
        self.assertEqual(
            self.invoice_parent.consolidated_payment_link_ref, values['reference'])
        self.assertEqual(
            self.customer._prepare_consolidated_payment_values()['company'],
            self.invoice_parent.company_id)
        partner_without_due = self.env['res.partner'].create({'name': 'No Due'})
        self.assertIsNone(
            partner_without_due._prepare_consolidated_payment_values(self.company))

    def test_prepare_consolidated_payment_values_multi_currency(self):
        """With several currencies the amount is expressed in the company currency."""
        foreign_currency = self.setup_other_currency('EUR')
        foreign_invoice = self.init_invoice(
            'out_invoice', partner=self.customer, amounts=[200.0],
            currency=foreign_currency, post=True)
        values = self.customer._prepare_consolidated_payment_values(self.company)
        self.assertEqual(values['currency'], self.company.currency_id)
        self.assertAlmostEqual(
            values['amount'],
            300.0 + self._receivable_lines(foreign_invoice).amount_residual)

    def test_consolidated_payment_link_ref_not_copied(self):
        """The consolidated reference is not copied with the invoice."""
        self.invoice_parent.consolidated_payment_link_ref = 'REF-TO-NOT-COPY'
        self.assertFalse(self.invoice_parent.copy().consolidated_payment_link_ref)

    def test_wizard_send_mail(self):
        """The wizard sends the template with the partner payment link in context."""
        wizard = self.env['send.payment.link.wizard'].with_context(
            active_id=self.customer.id).create({})
        self.assertEqual(wizard.partner_id, self.customer)
        template_class = type(self.env['mail.template'])
        with patch.object(template_class, 'send_mail', autospec=True) as send_mail:
            action = wizard.action_send_mail()
        self.assertEqual(action, {'type': 'ir.actions.act_window_close'})
        send_mail.assert_called_once()
        template, res_id = send_mail.call_args.args
        self.assertEqual(res_id, self.customer.id)
        self.assertEqual(
            template, self.env.ref(
                'partner_consolidated_payment_link.email_template_payment_link'))
        self.assertEqual(
            template.env.context['payment_link'],
            self.customer._get_consolidated_payment_url())
        self.assertEqual(template.env.context['default_res_id'], self.customer.id)

    def test_wizard_send_mail_without_email(self):
        """The wizard refuses to send the link to a partner without email."""
        wizard = self.env['send.payment.link.wizard'].create({
            'partner_id': self.other_customer.id,
        })
        with self.assertRaises(UserError):
            wizard.action_send_mail()


@tagged('post_install', '-at_install')
class TestConsolidatedPaymentLinkController(AccountPaymentCommon, HttpCase):
    """Test the public consolidated payment link route."""

    @classmethod
    def setUpClass(cls):
        """Create a customer with a posted invoice."""
        super().setUpClass()
        cls.customer = cls.env['res.partner'].create({
            'name': 'Consolidated Customer',
            'email': 'consolidated.customer@example.com',
        })
        cls.invoice = cls.init_invoice(
            'out_invoice', partner=cls.customer, amounts=[100.0], post=True)

    def _open_link(self, partner_id, access_token):
        """Open the consolidated payment link without following redirections."""
        return self.url_open(
            f'/payment/balance/{partner_id}?access_token={access_token}',
            allow_redirects=False)

    def test_link_rejects_invalid_token(self):
        """The balance of a partner is not reachable without its token."""
        self.assertEqual(self._open_link(self.customer.id, 'wrong').status_code, 404)
        self.assertEqual(self.url_open(
            f'/payment/balance/{self.customer.id}', allow_redirects=False).status_code, 404)
        self.assertFalse(self.invoice.consolidated_payment_link_ref)

    def test_link_rejects_unknown_partner(self):
        """An unknown partner gives a not found page."""
        self.assertEqual(self._open_link(999999999, 'wrong').status_code, 404)

    def test_link_redirects_to_payment_page(self):
        """A valid link redirects to the payment page with the total due."""
        token = self.customer._get_consolidated_payment_token()
        response = self._open_link(self.customer.id, token)
        self.assertEqual(response.status_code, 303)
        url = urlsplit(response.headers['Location'])
        self.assertEqual(url.path, '/payment/pay')
        params = parse_qs(url.query)
        self.assertEqual(params['reference'], [self.invoice.consolidated_payment_link_ref])
        self.assertEqual(float(params['amount'][0]), 100.0)
        self.assertEqual(params['partner_id'], [str(self.customer.id)])
        self.assertEqual(params['company_id'], [str(self.invoice.company_id.id)])
        self.assertTrue(params['access_token'][0])
        reference = self.invoice.consolidated_payment_link_ref
        self._open_link(self.customer.id, token)
        self.assertEqual(self.invoice.consolidated_payment_link_ref, reference)

    def test_link_without_due(self):
        """A partner without overdue invoices gets an informative message."""
        partner = self.env['res.partner'].create({'name': 'No Due'})
        response = self._open_link(
            partner.id, partner._get_consolidated_payment_token())
        self.assertEqual(response.status_code, 200)
        self.assertIn('All outstanding invoices are settled.', response.text)
