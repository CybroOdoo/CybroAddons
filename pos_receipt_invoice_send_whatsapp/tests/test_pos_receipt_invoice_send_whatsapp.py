###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring,protected-access,too-many-statements,too-many-lines
import json
from unittest.mock import MagicMock, patch

import requests

from odoo.exceptions import UserError, ValidationError
from odoo.fields import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'pos_receipt_invoice_send_whatsapp')
class TestPosReceiptInvoiceSendWhatsapp(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner = cls.env['res.partner'].create({
            'name': 'WhatsApp Test Customer',
            'whatsapp_number': '+1234567890',
        })
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'WhatsApp Shop',
            'pos_whatsapp_enabled': True,
            'apply_send_receipt_or_invoice': 'both',
        })
        cls.config_manager = cls.env['configuration.manager'].create({
            'instance': 'instance12345',
            'token': 'token12345',
            'config_id': cls.pos_config.id,
            'state': 'draft',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'WhatsApp Test Product',
            'type': 'consu',
            'list_price': 100.0,
        })

    def test_01_configuration_manager_authenticate(self):
        """Test configuration.manager authentication and QR retrieval."""
        manager = self.config_manager

        # Test request exception during authentication
        with patch('requests.request', side_effect=requests.RequestException("Network Error")):
            with self.assertRaises(ValidationError):
                manager.action_authenticate()

        # Test invalid token HTTP status != 200
        mock_bad_resp = MagicMock()
        mock_bad_resp.status_code = 401
        with patch('requests.request', return_value=mock_bad_resp):
            with self.assertRaises(ValidationError):
                manager.action_authenticate()

        # Test Client not found text
        mock_client_not_found = MagicMock()
        mock_client_not_found.status_code = 200
        mock_client_not_found.text = "Client not found."
        with patch('requests.request', return_value=mock_client_not_found):
            action = manager.action_authenticate()
            self.assertEqual(action.get('type'), 'ir.actions.client')
            self.assertEqual(action.get('tag'), 'display_notification')

        # Test connected substatus
        mock_connected = MagicMock()
        mock_connected.status_code = 200
        mock_connected.text = "OK"
        mock_connected.json.return_value = {
            'status': {
                'accountStatus': {
                    'substatus': 'connected',
                },
            },
        }
        with patch('requests.request', return_value=mock_connected):
            action = manager.action_authenticate()
            self.assertEqual(manager.state, 'verified')
            self.assertEqual(action.get('tag'), 'display_notification')

        # Test normal substatus opening wizard
        mock_normal = MagicMock()
        mock_normal.status_code = 200
        mock_normal.text = "OK"
        mock_normal.json.return_value = {
            'status': {
                'accountStatus': {
                    'substatus': 'normal',
                },
            },
        }
        get_qr_mock = patch(
            'odoo.addons.pos_receipt_invoice_send_whatsapp.models.configuration_manager.'
            'ConfigurationManager.get_qr_code',
            return_value='data:image/png;base64,ABC',
        )
        with patch('requests.request', return_value=mock_normal):
            with get_qr_mock:
                action = manager.action_authenticate()
                self.assertEqual(action.get('res_model'), 'whatsapp.authenticate')

        # Test get_qr_code error and success
        with patch('requests.get', side_effect=requests.RequestException("Timeout")):
            self.assertIsNone(manager.get_qr_code())

        mock_qr_resp = MagicMock()
        mock_qr_resp.status_code = 200
        mock_qr_resp.text = json.dumps({'qrCode': 'my_qr_code_data'})
        with patch('requests.get', return_value=mock_qr_resp):
            self.assertEqual(manager.get_qr_code(), json.dumps({'qrCode': 'my_qr_code_data'}))

        # Test open_authenticate_wizard parsing variations
        err_action = manager.open_authenticate_wizard(json.dumps({'error': 'Device disconnected'}))
        self.assertEqual(err_action.get('tag'), 'display_notification')

        direct_qr_action = manager.open_authenticate_wizard('raw_qr_code_data')
        self.assertEqual(direct_qr_action.get('res_model'), 'whatsapp.authenticate')

    def test_02_whatsapp_authenticate_wizard(self):
        """Test whatsapp.authenticate wizard save action."""
        wizard = self.env['whatsapp.authenticate'].create({
            'configuration_manager_id': self.config_manager.id,
            'qrcode': (
                'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+'
                'M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
            ),
        })
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "OK"
        mock_resp.json.return_value = {
            'status': {
                'accountStatus': {
                    'substatus': 'connected',
                },
            },
        }
        with patch('requests.request', return_value=mock_resp):
            wizard.action_save()
            self.assertEqual(self.config_manager.state, 'verified')

    def test_03_res_config_and_partner_user_extensions(self):
        """Test settings, res.partner, and res.users POS field loading."""
        # Test settings
        settings = self.env['res.config.settings'].create({
            'pos_config_id': self.pos_config.id,
            'pos_whatsapp_enabled': True,
            'apply_send_receipt_or_invoice': 'send_receipt',
        })
        self.assertEqual(self.pos_config.apply_send_receipt_or_invoice, 'send_receipt')
        self.assertTrue(settings.pos_whatsapp_enabled)

        # Test partner _load_pos_data_fields
        partner_fields = self.env['res.partner']._load_pos_data_fields(self.pos_config)
        self.assertIn('whatsapp_number', partner_fields)

        # Test users _load_pos_data_fields and whatsapp_groups_checks
        user = self.env.user
        user._compute_pos_receipt_invoice_send_whatsapp_group_user()
        user_fields = self.env['res.users']._load_pos_data_fields(self.pos_config)
        self.assertIn('whatsapp_groups_checks', user_fields)

        # Test whatsapp.message record creation
        msg = self.env['whatsapp.message'].create({
            'from_user_id': user.id,
            'to_user': '+1234567890',
            'user_name': 'Test User',
            'body': 'Test WhatsApp Message',
            'status': 'sent',
        })
        self.assertEqual(msg.status, 'sent')
        self.assertEqual(msg.to_user, '+1234567890')

    def test_04_pos_order_send_receipt_and_invoice(self):
        """Test pos.order action_send_receipt_whatsapp and action_send_invoice_whatsapp."""
        pos_session = self.env['pos.session'].create({
            'config_id': self.pos_config.id,
        })
        order = self.env['pos.order'].create({
            'company_id': self.company.id,
            'session_id': pos_session.id,
            'partner_id': self.partner.id,
            'lines': [
                Command.create({
                    'product_id': self.product.id,
                    'qty': 1.0,
                    'price_unit': self.product.lst_price,
                    'price_subtotal': self.product.lst_price,
                    'price_subtotal_incl': self.product.lst_price,
                }),
            ],
            'amount_tax': 0.0,
            'amount_total': self.product.lst_price,
            'amount_paid': self.product.lst_price,
            'amount_return': 0.0,
        })

        # 1. Test receipt sending without phone
        with self.assertRaises(UserError):
            order.action_send_receipt_whatsapp(False)

        # 2. Test receipt sending without verified config
        self.config_manager.state = 'draft'
        with self.assertRaises(UserError):
            order.action_send_receipt_whatsapp('+1234567890')

        # 3. Test receipt sending success with verified config
        self.config_manager.state = 'verified'
        mock_post_ok = MagicMock()
        mock_post_ok.status_code = 200
        gen_img_mock = patch(
            'odoo.addons.point_of_sale.receipt.pos_order_receipt.'
            'PosOrderReceipt.order_receipt_generate_image',
            return_value=b'fake_img',
        )
        with gen_img_mock:
            with patch('requests.post', return_value=mock_post_ok):
                order.action_send_receipt_whatsapp('+1234567890')

        # Verify whatsapp.message was logged
        messages = self.env['whatsapp.message'].search([
            ('to_user', '=', '+1234567890'),
        ])
        self.assertTrue(messages)

        # 4. Test receipt sending network failure
        with gen_img_mock:
            with patch(
                'requests.post',
                side_effect=requests.RequestException("Connection Failed"),
            ):
                with self.assertRaises(UserError):
                    order.action_send_receipt_whatsapp('+1234567890')

        # 5. Test invoice sending without verified config
        self.config_manager.state = 'draft'
        with self.assertRaises(UserError):
            order.action_send_invoice_whatsapp('+1234567890')

        # Test invoice sending when invoice cannot be generated
        self.config_manager.state = 'verified'
        pos_inv_noop = patch(
            'odoo.addons.point_of_sale.models.pos_order.PosOrder.action_pos_order_invoice',
            MagicMock(),
        )
        with pos_inv_noop:
            with self.assertRaises(UserError):
                order.action_send_invoice_whatsapp('+1234567890')

        # 6. Test invoice sending success
        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
        })
        order.account_move = move
        pdf_render_mock = patch.object(
            type(self.env['ir.actions.report']),
            '_render_qweb_pdf',
            return_value=[b'fake_pdf', 'pdf'],
        )
        with pdf_render_mock:
            with patch('requests.post', return_value=mock_post_ok):
                order.action_send_invoice_whatsapp('+1234567890')

        # Test branch where attachment already exists on mail.message
        mail_msg = self.env['mail.message'].create({
            'model': 'account.move',
            'res_id': move.id,
            'body': 'Invoice Mail',
        })
        self.env['ir.attachment'].create({
            'name': f'Invoice-{order.name}.pdf',
            'type': 'binary',
            'raw': b'fake_cached_pdf',
            'mimetype': 'application/pdf',
            'res_model': 'mail.message',
            'res_id': mail_msg.id,
        })
        with patch('requests.post', return_value=mock_post_ok):
            order.action_send_invoice_whatsapp('+1234567890')

        # 7. Test invoice sending network failure
        with pdf_render_mock:
            with patch(
                'requests.post',
                side_effect=requests.RequestException("Invoice Send Failed"),
            ):
                with self.assertRaises(UserError):
                    order.action_send_invoice_whatsapp('+1234567890')

        # 8. Test action_send_invoice helper
        with patch(
            'odoo.addons.pos_receipt_invoice_send_whatsapp.models.pos_order.'
            'PosOrder.action_send_invoice_whatsapp',
        ) as mock_inv:
            order.action_send_invoice(number='+1234567890', order_id=order.id)
            mock_inv.assert_called_once_with('+1234567890')

        # 9. Test action_send_receipt email fallback
        core_receipt_path = (
            'odoo.addons.point_of_sale.models.pos_order.PosOrder.action_send_receipt'
        )
        with patch(core_receipt_path) as mock_core:
            order.action_send_receipt('customer@example.com')
            mock_core.assert_called_once_with('customer@example.com')
