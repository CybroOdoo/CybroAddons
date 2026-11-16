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

import json

from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestWebsiteSaleOrderCancellation(HttpCase):
    """Test cancellation from the website portal endpoint."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Website Cancellation Customer',
            'email': 'website-cancel@example.com',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Website Cancellation Test Product',
            'list_price': 25.0,
        })
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'order_line': [(0, 0, {
                'product_id': cls.product.id,
                'product_uom_qty': 1,
                'price_unit': 25.0,
            })],
        })
        cls.sale_order.action_confirm()

    def test_website_cancellation_saves_reason_and_cancels_order(self):
        token = self.sale_order._portal_ensure_token()
        reason = 'Customer changed their mind.'
        response = self.url_open(
            '/cancel/reason/edit',
            data=json.dumps({
                'jsonrpc': '2.0',
                'method': 'call',
                'params': {
                    'sale_order_id': self.sale_order.id,
                    'reason': reason,
                    'access_token': token,
                },
                'id': 1,
            }),
            headers={'Content-Type': 'application/json'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get('result'), {
            'success': True,
            'sale_order_id': self.sale_order.id,
        })
        self.sale_order.invalidate_recordset()
        self.assertEqual(self.sale_order.state, 'cancel')
        self.assertTrue(self.sale_order.is_cancel)
        self.assertEqual(self.sale_order.cancellation_reason, reason)

    def test_website_cancellation_without_access_denied(self):
        """Unauthorized attempt to cancel without token or login should fail."""
        reason = 'Malicious cancellation attempt.'
        response = self.url_open(
            '/cancel/reason/edit',
            data=json.dumps({
                'jsonrpc': '2.0',
                'method': 'call',
                'params': {
                    'sale_order_id': self.sale_order.id,
                    'reason': reason,
                    'access_token': 'invalid_token',
                },
                'id': 1,
            }),
            headers={'Content-Type': 'application/json'},
        )

        self.assertEqual(response.status_code, 200)
        result = response.json().get('result', {})
        self.assertIn('error', result)
        self.sale_order.invalidate_recordset()
        self.assertNotEqual(self.sale_order.state, 'cancel')
