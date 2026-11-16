# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER GENERAL PUBLIC
#    LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from unittest.mock import MagicMock, patch
from odoo import Command
from odoo.api import Environment
from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestVeloraControllers(HttpCase):

    def test_newsletter_rejects_invalid_email(self):
        for email in (None, '', 'not-an-email'):
            with self.subTest(email=email):
                result = self.make_jsonrpc_request(
                    '/theme_velora/newsletter/subscribe', {'email': email})
                self.assertFalse(result['success'])

    def test_newsletter_accepts_valid_email(self):
        result = self.make_jsonrpc_request(
            '/theme_velora/newsletter/subscribe', {'email': 'velora.tester@example.com'})
        self.assertTrue(result['success'])
        contact = self.env['mailing.contact'].sudo().search(
            [('email', '=ilike', 'velora.tester@example.com')])
        self.assertEqual(len(contact), 1)
        self.assertIn(
            self.env.ref('theme_velora.mailing_list_velora_circle'), contact.list_ids)

        # subscribing twice must not duplicate the contact
        result = self.make_jsonrpc_request(
            '/theme_velora/newsletter/subscribe', {'email': 'VELORA.tester@example.com'})
        self.assertTrue(result['success'])
        contact = self.env['mailing.contact'].sudo().search(
            [('email', '=ilike', 'velora.tester@example.com')])
        self.assertEqual(len(contact), 1)

    def test_newsletter_reports_failure_on_contact_creation_error(self):
        """A failure while creating the contact must be reported, not hidden."""
        model_cls = type(self.env['mailing.contact'])
        with self.assertLogs('odoo.addons.theme_velora.controllers.main', level='ERROR'), \
                patch.object(model_cls, 'create', side_effect=Exception('boom')):
            result = self.make_jsonrpc_request(
                '/theme_velora/newsletter/subscribe', {'email': 'velora.fail@example.com'})
        self.assertFalse(result['success'])

    def _subscribe_with_fake_mailing(self, email, existing=None, create_error=None):
        """Call the subscribe endpoint with a fake ``mailing.contact`` model.

        Returns the JSON result and the fake model's ``sudo()`` recordset mock,
        so tests can assert on ``search`` and ``create`` calls.
        """
        fake_model = MagicMock()
        fake_model.sudo.return_value.search.return_value = existing or []
        if create_error:
            fake_model.sudo.return_value.create.side_effect = create_error
        original_getitem = Environment.__getitem__

        def fake_getitem(env, model_name):
            if model_name == 'mailing.contact':
                return fake_model
            return original_getitem(env, model_name)

        with patch.object(Environment, '__getitem__', fake_getitem):
            result = self.make_jsonrpc_request(
                '/theme_velora/newsletter/subscribe', {'email': email})
        return result, fake_model.sudo.return_value

    def test_newsletter_creates_new_contact(self):
        result, model = self._subscribe_with_fake_mailing(' new@example.com ')
        self.assertTrue(result['success'])
        mailing_list = self.env.ref('theme_velora.mailing_list_velora_circle')
        model.create.assert_called_once_with({
            'email': 'new@example.com',
            'name': 'new',
            'list_ids': [Command.link(mailing_list.id)],
        })

    def test_newsletter_does_not_duplicate_existing_contact(self):
        result, model = self._subscribe_with_fake_mailing(
            'old@example.com', existing=MagicMock())
        self.assertTrue(result['success'])
        model.create.assert_not_called()

    def test_newsletter_logs_and_reports_contact_error(self):
        with self.assertLogs('odoo.addons.theme_velora.controllers.main', level='ERROR'):
            result, _model = self._subscribe_with_fake_mailing(
                'fail@example.com', create_error=Exception('boom'))
        self.assertFalse(result['success'])

    def test_newsletter_existing_contact_when_list_is_missing(self):
        """Subscribing must still succeed if the default list was deleted."""
        self.env.ref('theme_velora.mailing_list_velora_circle').sudo().unlink()
        self.env['mailing.contact'].sudo().create(
            {'email': 'nolist@example.com', 'name': 'nolist'})
        result = self.make_jsonrpc_request(
            '/theme_velora/newsletter/subscribe', {'email': 'nolist@example.com'})
        self.assertTrue(result['success'])
        self.assertEqual(
            self.env['mailing.contact'].sudo().search_count(
                [('email', '=ilike', 'nolist@example.com')]), 1)

    def test_empty_cart_data(self):
        result = self.make_jsonrpc_request('/theme_velora/cart/data')
        self.assertEqual(result['items'], [])
        self.assertEqual(result['subtotal'], 0)
        self.assertEqual(result['cart_quantity'], 0)
        self.assertIn('currency_symbol', result)
        self.assertIn(result['currency_position'], ('before', 'after'))

    def test_cart_update_and_remove_without_cart(self):
        """Updating or removing a line when no cart exists must not crash."""
        result = self.make_jsonrpc_request(
            '/theme_velora/cart/update_qty', {'line_id': 999999, 'quantity': 2})
        self.assertEqual(result['items'], [])
        result = self.make_jsonrpc_request('/theme_velora/cart/remove', {'line_id': 999999})
        self.assertEqual(result['items'], [])

    def test_category_redirect_to_existing_category(self):
        category = self.env.ref('theme_velora.theme_velora_category_floral')
        response = self.url_open('/theme_velora/category/floral', allow_redirects=False)
        self.assertIn(response.status_code, (301, 302, 303))
        self.assertIn(f'/shop/category/{category.id}', response.headers['Location'])

    def test_category_redirect_unknown_falls_back_to_search(self):
        response = self.url_open('/theme_velora/category/does-not-exist', allow_redirects=False)
        self.assertIn(response.status_code, (301, 302, 303))
        self.assertIn('/shop?search=does-not-exist', response.headers['Location'])


@tagged('post_install', '-at_install')
class TestVeloraCart(HttpCase):
    """Cart drawer endpoints with a real cart in the session."""

    def setUp(self):
        super().setUp()
        self.website = self.env['website'].search([], limit=1)
        self.product = self.env['product.product'].create({
            'name': 'Velora Test Perfume',
            'list_price': 100.0,
            'sale_ok': True,
            'website_published': True,
        })
        self.authenticate('admin', 'admin')
        partner = self.env.user.partner_id
        self.order = self.env['sale.order'].create({
            'partner_id': partner.id,
            'website_id': self.website.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 2,
            })],
        })
        self.line = self.order.order_line
        self.update_session(sale_order_id=self.order.id)

    def test_cart_data_with_items(self):
        result = self.make_jsonrpc_request('/theme_velora/cart/data')
        self.assertEqual(len(result['items']), 1)
        item = result['items'][0]
        self.assertEqual(item['line_id'], self.line.id)
        self.assertEqual(item['product_id'], self.product.id)
        self.assertEqual(item['quantity'], 2)
        self.assertIn(f'/web/image/product.product/{self.product.id}/', item['image_url'])
        self.assertTrue(result['currency_symbol'])

    def test_update_qty(self):
        result = self.make_jsonrpc_request(
            '/theme_velora/cart/update_qty',
            {'line_id': self.line.id, 'quantity': 5})
        self.assertEqual(result['items'][0]['quantity'], 5)

    def test_update_qty_zero_removes_line(self):
        result = self.make_jsonrpc_request(
            '/theme_velora/cart/update_qty',
            {'line_id': self.line.id, 'quantity': 0})
        self.assertEqual(result['items'], [])

    def test_update_qty_unknown_line_is_ignored(self):
        result = self.make_jsonrpc_request(
            '/theme_velora/cart/update_qty',
            {'line_id': 999999, 'quantity': 3})
        self.assertEqual(result['items'][0]['quantity'], 2)

    def test_remove_item(self):
        result = self.make_jsonrpc_request(
            '/theme_velora/cart/remove', {'line_id': self.line.id})
        self.assertEqual(result['items'], [])

    def test_remove_unknown_line_is_ignored(self):
        result = self.make_jsonrpc_request(
            '/theme_velora/cart/remove', {'line_id': 999999})
        self.assertEqual(len(result['items']), 1)