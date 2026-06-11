# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import base64
from unittest.mock import MagicMock, patch
from odoo.tests import tagged
from odoo.addons.point_of_sale.tests.common import TestPointOfSaleCommon


@tagged('post_install', '-at_install')
class TestPosOrder(TestPointOfSaleCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner1.write({'whatsapp_number': '971500000000'})
        cls.configuration = cls.env['configuration.manager'].sudo().create({
            'instance': 'instance-1',
            'token': 'token-1',
            'config_id': cls.pos_config.id,
            'state': 'verified',
        })

    def setUp(self):
        super().setUp()
        self.pos_config.open_ui()
        self.order = self.PosOrder.create({
            'company_id': self.env.company.id,
            'session_id': self.pos_config.current_session_id.id,
            'partner_id': self.partner1.id,
            'access_token': '1234567890',
            'lines': [(0, 0, {
                'name': 'OL/0001',
                'product_id': self.product3.id,
                'price_unit': 450,
                'discount': 0.0,
                'qty': 1.0,
                'tax_ids': False,
                'price_subtotal': 450,
                'price_subtotal_incl': 450,
            })],
            'amount_tax': 0,
            'amount_total': 450,
            'amount_paid': 450.0,
            'amount_return': 0.0,
        })
        self.order.action_pos_order_invoice()

    def test_action_send_invoice_without_whatsapp_number(self):
        self.partner1.write({'whatsapp_number': False})
        result = self.order.sudo().action_send_invoice(
            order_id=self.order.id,
            config_id=self.pos_config.id,
        )
        self.assertEqual(result['status'], 'error')
        self.assertIn('Whatsapp Number', result['message'])
        self.partner1.write({'whatsapp_number': '971500000000'})

    def test_action_send_receipt_without_whatsapp_number(self):
        partner_data = {
            'name': self.partner.name,
            'whatsapp': False,
            'config_id': self.pos_config.id,
        }
        ticket = base64.b64encode(b'fake-ticket')
        result = self.order.sudo().action_send_receipt(self.order.name, partner_data, ticket)
        self.assertEqual(result['status'], 'error')
        self.assertIn('Whatsapp Number', result['message'])

    def test_get_instance_returns_verified_configuration(self):
        result = self.order.sudo().get_instance(config_id=self.pos_config.id)
        self.assertEqual(result['instant_id'], self.configuration.id)

    def test_action_send_receipt_creates_message_on_success(self):
        partner_data = {
            'name': self.partner1.name,
            'whatsapp': self.partner1.whatsapp_number,
            'config_id': self.pos_config.id,
        }
        response = MagicMock()
        response.raise_for_status.return_value = None
        response.status_code = 200

        with patch('requests.post', return_value=response):
            result = self.order.sudo().action_send_receipt(
                self.order.name,
                partner_data,
                base64.b64encode(b'fake-ticket'),
            )

        self.assertIsNone(result)
        message = self.env['whatsapp.message'].sudo().search(
            [('to_user', '=', self.partner1.whatsapp_number)],
            limit=1,
        )
        self.assertTrue(message.exists())
