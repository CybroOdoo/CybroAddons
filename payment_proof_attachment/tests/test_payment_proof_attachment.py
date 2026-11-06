# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import base64

from odoo.tests import HttpCase, new_test_user, tagged

from odoo.addons.payment_proof_attachment.controllers.payment_proof_attachment \
    import PAYMENT_PROOF_DESCRIPTION

SUBMIT_URL = '/payment_proof/submit'
SHOW_URL = '/my_account_screen/show_updated'
PDF_CONTENT = b'%PDF-1.4 payment proof'


@tagged('post_install', '-at_install')
class TestPaymentProofAttachment(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env['website'].search([], limit=1)
        cls.portal_user = new_test_user(
            cls.env, login='proof_portal', password='proof_portal',
            groups='base.group_portal', email='proof_portal@example.com')
        cls.other_partner = cls.env['res.partner'].create({
            'name': 'Other Customer',
            'email': 'other@example.com',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Proof Product',
            'list_price': 100.0,
            'sale_ok': True,
        })
        cls.order = cls._create_order(cls.portal_user.partner_id)
        cls.foreign_order = cls._create_order(cls.other_partner)
        cls.b64_content = base64.b64encode(PDF_CONTENT).decode()

    @classmethod
    def _create_order(cls, partner):
        return cls.env['sale.order'].create({
            'partner_id': partner.id,
            'website_id': cls.website.id,
            'order_line': [(0, 0, {
                'product_id': cls.product.id,
                'product_uom_qty': 1,
            })],
        })

    def _proofs(self, order):
        return self.env['ir.attachment'].search([
            ('res_model', '=', 'sale.order'),
            ('res_id', '=', order.id),
            ('description', '=', PAYMENT_PROOF_DESCRIPTION),
        ])

    def test_submit_with_access_token(self):
        """Public visitor with the order token uploads proofs (plain and
        data URL base64), a chatter message and an email are created."""
        token = self.order._portal_ensure_token()
        result = self.make_jsonrpc_request(SUBMIT_URL, {
            'sale_id': self.order.id,
            'access_token': token,
            'attachments': [
                {'name': 'proof.pdf', 'content': self.b64_content},
                {'content': 'data:application/pdf;base64,%s'
                            % self.b64_content},
            ],
        })
        self.assertTrue(result['success'])
        proofs = self._proofs(self.order)
        self.assertEqual(
            sorted(proofs.mapped('name')), ['payment_proof', 'proof.pdf'])
        for proof in proofs:
            self.assertEqual(bytes(proof.raw), PDF_CONTENT)
            self.assertFalse(proof.public)
        message = self.order.message_ids.filtered(
            lambda m: 'uploaded as payment proof' in (m.body or ''))
        self.assertEqual(len(message), 1)
        self.assertEqual(message.attachment_ids, proofs)
        mail = self.env['mail.mail'].search([
            ('model', '=', 'sale.order'),
            ('res_id', '=', self.order.id),
            ('subject', '=', 'Payment Proof Attachment'),
        ])
        self.assertTrue(mail)

    def test_submit_without_mail_template(self):
        """Upload still works when the email template has been deleted."""
        self.env.ref(
            'payment_proof_attachment.payment_proof_attachment_email_template'
        ).unlink()
        token = self.order._portal_ensure_token()
        result = self.make_jsonrpc_request(SUBMIT_URL, {
            'sale_id': self.order.id,
            'access_token': token,
            'attachments': [{'name': 'a.pdf', 'content': self.b64_content}],
        })
        self.assertTrue(result['success'])
        self.assertEqual(len(self._proofs(self.order)), 1)

    def test_submit_invalid_content(self):
        """Content that is not base64 is ignored and reported as an error."""
        token = self.order._portal_ensure_token()
        result = self.make_jsonrpc_request(SUBMIT_URL, {
            'sale_id': self.order.id,
            'access_token': token,
            'attachments': [{'name': 'bad.pdf', 'content': 'not base64!!'}],
        })
        self.assertIn('error', result)
        self.assertFalse(self._proofs(self.order))

    def test_submit_without_attachments(self):
        token = self.order._portal_ensure_token()
        result = self.make_jsonrpc_request(SUBMIT_URL, {
            'sale_id': self.order.id,
            'access_token': token,
        })
        self.assertIn('error', result)

    def test_submit_wrong_token_denied(self):
        """A visitor without access to the order cannot attach files."""
        self.foreign_order._portal_ensure_token()
        result = self.make_jsonrpc_request(SUBMIT_URL, {
            'sale_id': self.foreign_order.id,
            'access_token': 'wrong-token',
            'attachments': [{'name': 'x.pdf', 'content': self.b64_content}],
        })
        self.assertIn('error', result)
        self.assertFalse(self._proofs(self.foreign_order))

    def test_submit_missing_order(self):
        result = self.make_jsonrpc_request(SUBMIT_URL, {
            'sale_id': 999999999,
            'attachments': [{'name': 'x.pdf', 'content': self.b64_content}],
        })
        self.assertIn('error', result)

    def test_submit_invalid_id_without_cart(self):
        """An id that is not a number falls back to the cart; a public
        visitor has none."""
        result = self.make_jsonrpc_request(SUBMIT_URL, {
            'sale_id': 'abc',
            'attachments': [{'name': 'x.pdf', 'content': self.b64_content}],
        })
        self.assertIn('error', result)

    def test_submit_and_show_with_cart(self):
        """A logged-in customer without id uses the current cart, and as the
        order owner can list the proofs without a token."""
        self.authenticate('proof_portal', 'proof_portal')
        result = self.make_jsonrpc_request(SUBMIT_URL, {
            'attachments': [{'name': 'cart.pdf', 'content': self.b64_content}],
        })
        self.assertTrue(result['success'])
        self.assertEqual(self._proofs(self.order).name, 'cart.pdf')
        receipts = self.make_jsonrpc_request(SHOW_URL, {
            'data': str(self.order.id),
        })
        self.assertEqual([r['name'] for r in receipts], ['cart.pdf'])

    def test_show_receipts(self):
        """Only the payment proofs are listed, with a working download url."""
        proof = self.env['ir.attachment'].create({
            'name': 'proof.pdf',
            'res_model': 'sale.order',
            'res_id': self.order.id,
            'description': PAYMENT_PROOF_DESCRIPTION,
            'raw': PDF_CONTENT,
        })
        self.env['ir.attachment'].create({
            'name': 'internal.pdf',
            'res_model': 'sale.order',
            'res_id': self.order.id,
            'raw': b'internal',
        })
        token = self.order._portal_ensure_token()
        receipts = self.make_jsonrpc_request(SHOW_URL, {
            'data': str(self.order.id),
            'access_token': token,
        })
        self.assertEqual(len(receipts), 1)
        self.assertEqual(receipts[0]['id'], proof.id)
        self.assertEqual(receipts[0]['name'], 'proof.pdf')
        response = self.url_open(receipts[0]['url'])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, PDF_CONTENT)

    def test_show_receipts_denied(self):
        result = self.make_jsonrpc_request(SHOW_URL, {
            'data': str(self.foreign_order.id),
        })
        self.assertIn('error', result)

    def test_portal_page_renders_upload_buttons(self):
        """The portal page of a quotation shows the upload buttons with
        the order token."""
        token = self.order._portal_ensure_token()
        response = self.url_open(
            '/my/orders/%s?access_token=%s' % (self.order.id, token))
        self.assertEqual(response.status_code, 200)
        self.assertIn('id="btnShowModal"', response.text)
        self.assertIn('data-access-token="%s"' % token, response.text)
