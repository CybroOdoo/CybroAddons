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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import json
from unittest.mock import patch, MagicMock
from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged
from ..controllers import telegram_chatbox as tc_module
from ..controllers.telegram_chatbox import TelegramWebhookController


@tagged('post_install', '-at_install')
class TestTelegramChatbox(TransactionCase):
    """Automated unit tests for telegram_chatbox module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.bot = cls.env['telegram.bot'].create({
            'name': 'Test Bot',
            'token': '123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11',
            'webhook_url': 'https://example.com/telegram/webhook/123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11',
            'status': 'active',
            'active': True,
        })

        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Telegram Customer',
            'email': 'customer@test.com',
            'telegram_chat_id': '11223344',
            'telegram_username': 'test_customer',
            'telegram_bot_id': cls.bot.id,
        })

        partner_model = cls.env['ir.model'].search([('model', '=', 'res.partner')], limit=1)
        name_field = cls.env['ir.model.fields'].search([
            ('model_id', '=', partner_model.id),
            ('name', '=', 'name')
        ], limit=1)

        cls.template = cls.env['telegram.template'].create({
            'name': 'Customer Greeting',
            'model_id': partner_model.id,
            'message': 'Hello {{customer_name}}, welcome to our service!',
            'dynamic_variable_ids': [Command.create({
                'name': 'customer_name',
                'model_id': partner_model.id,
                'field_id': name_field.id,
            })],
        })

        cls.product = cls.env['product.product'].create({
            'name': 'Telegram Test Product',
            'type': 'consu',
            'list_price': 100.0,
        })

        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'order_line': [Command.create({
                'product_id': cls.product.id,
                'product_uom_qty': 1,
                'price_unit': 100.0,
            })],
        })

        cls.purchase_order = cls.env['purchase.order'].create({
            'partner_id': cls.partner.id,
            'order_line': [Command.create({
                'product_id': cls.product.id,
                'product_qty': 2,
                'price_unit': 50.0,
            })],
        })

        main_company = cls.env.company
        sale_journal = cls.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', '=', main_company.id)
        ], limit=1)
        if not sale_journal:
            sale_journal = cls.env['account.journal'].create({
                'name': 'Customer Invoices - Test',
                'code': 'TJINV',
                'type': 'sale',
                'company_id': main_company.id,
            })
        cls.sale_journal = sale_journal

        purchase_journal = cls.env['account.journal'].search([
            ('type', '=', 'purchase'),
            ('company_id', '=', main_company.id)
        ], limit=1)
        if not purchase_journal:
            purchase_journal = cls.env['account.journal'].create({
                'name': 'Vendor Bills - Test',
                'code': 'TJBIL',
                'type': 'purchase',
                'company_id': main_company.id,
            })
        cls.purchase_journal = purchase_journal

    # -------------------------------------------------------------------------
    # 1. Telegram Bot Tests
    # -------------------------------------------------------------------------

    def test_01_bot_crud_and_lookup(self):
        """Test Telegram Bot creation, retrieval and token lookup."""
        found_bot = self.env['telegram.bot'].get_by_token(self.bot.token)
        self.assertEqual(found_bot, self.bot)

        # Test write
        self.bot.write({'timeout': 20})
        self.assertEqual(self.bot.timeout, 20)

    @patch('requests.post')
    def test_02_bot_action_set_webhook(self, mock_post):
        """Test setting webhook on Telegram Bot."""
        mock_post_resp = MagicMock()
        mock_post_resp.status_code = 200
        mock_post_resp.json.return_value = {'ok': True, 'description': 'Webhook was set'}
        mock_post.return_value = mock_post_resp

        action = self.bot.action_set_webhook()
        self.assertEqual(action.get('type'), 'ir.actions.client')
        self.assertEqual(self.bot.status, 'active')
        self.assertFalse(self.bot.last_error_message)
        self.assertTrue(self.bot.webhook_secret)
        self.assertTrue(self.bot.webhook_url.endswith('/telegram/webhook'))
        mock_post.assert_called_once()
        call_json = mock_post.call_args[1].get('json', {})
        self.assertEqual(call_json.get('secret_token'), self.bot.webhook_secret)

    # -------------------------------------------------------------------------
    # 2. Telegram Template Tests
    # -------------------------------------------------------------------------

    def test_03_template_rendering(self):
        """Test rendering a template with dynamic record values."""
        rendered = self.template.render_template(self.template.message, record=self.partner)
        self.assertIn('Test Telegram Customer', rendered)

        # Direct values dictionary override
        custom_rendered = self.template.render_template(
            "Hi {{name}}!", values={'name': 'Custom User'}
        )
        self.assertEqual(custom_rendered, "Hi Custom User!")

    def test_04_template_onchange_message(self):
        """Test template onchange placeholder synchronization."""
        template = self.env['telegram.template'].new({
            'name': 'New Dynamic Template',
            'model_id': self.template.model_id.id,
            'message': 'Greetings {{first_name}} and {{order_ref}}',
        })
        template._onchange_message()
        var_names = [v.name for v in template.dynamic_variable_ids]
        self.assertIn('first_name', var_names)
        self.assertIn('order_ref', var_names)

    # -------------------------------------------------------------------------
    # 3. Incoming Webhook Message Handling
    # -------------------------------------------------------------------------

    def test_05_create_incoming_message_new_partner(self):
        """Test creating an incoming message from a brand new Telegram user."""
        payload = {
            'message': {
                'message_id': 9001,
                'chat': {
                    'id': 99887766,
                    'first_name': 'Alice',
                    'last_name': 'Wonder',
                    'username': 'alicew',
                },
                'text': 'Hello from Telegram Alice!',
            }
        }
        msg = self.env['telegram.message'].create_incoming(self.bot, payload)
        self.assertTrue(msg)
        self.assertEqual(msg.direction, 'incoming')
        self.assertEqual(msg.chat_id, '99887766')
        self.assertEqual(msg.message_text, 'Hello from Telegram Alice!')
        self.assertEqual(msg.partner_id.name, 'Alice Wonder')
        self.assertEqual(msg.partner_id.telegram_chat_id, '99887766')

    def test_06_create_incoming_message_existing_partner(self):
        """Test receiving a message from an already known partner."""
        payload = {
            'message': {
                'message_id': 9002,
                'chat': {
                    'id': int(self.partner.telegram_chat_id),
                    'first_name': 'Test',
                    'username': 'test_customer',
                },
                'text': 'Reply from known customer',
            }
        }
        msg = self.env['telegram.message'].create_incoming(self.bot, payload)
        self.assertTrue(msg)
        self.assertEqual(msg.partner_id, self.partner)

    @patch('requests.post')
    def test_07_create_incoming_callback_query(self, mock_post):
        """Test handling callback query payload."""
        mock_post_resp = MagicMock()
        mock_post_resp.status_code = 200
        mock_post_resp.json.return_value = {'ok': True}
        mock_post.return_value = mock_post_resp

        payload = {
            'callback_query': {
                'id': 'cb_12345',
                'data': 'button_clicked_yes',
                'message': {
                    'message_id': 9003,
                    'chat': {'id': int(self.partner.telegram_chat_id)},
                }
            }
        }
        msg = self.env['telegram.message'].create_incoming(self.bot, payload)
        self.assertTrue(msg)
        self.assertEqual(msg.message_text, 'button_clicked_yes')

    def test_08_incoming_reply_to_sale_order(self):
        """Test incoming message replying to a document message."""
        # Create an outgoing message record simulating sent quote
        out_msg = self.env['telegram.message'].create({
            'name': 'tg_555',
            'direction': 'outgoing',
            'chat_id': self.partner.telegram_chat_id,
            'partner_id': self.partner.id,
            'bot_id': self.bot.id,
            'res_model': 'sale.order',
            'res_id': self.sale_order.id,
            'message_text': 'Here is your quote S0001',
            'state': 'sent',
        })
        self.assertTrue(out_msg)

        payload = {
            'message': {
                'message_id': 9004,
                'chat': {'id': int(self.partner.telegram_chat_id)},
                'text': 'Approved!',
                'reply_to_message': {
                    'message_id': 555
                }
            }
        }
        in_msg = self.env['telegram.message'].create_incoming(self.bot, payload)
        self.assertTrue(in_msg)
        self.assertEqual(in_msg.res_model, 'sale.order')
        self.assertEqual(in_msg.res_id, self.sale_order.id)

    # -------------------------------------------------------------------------
    # 4. Outgoing Message Dispatch Tests
    # -------------------------------------------------------------------------

    @patch('requests.post')
    def test_09_send_via_bot(self, mock_post):
        """Test sending an outgoing telegram message via bot API."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {'ok': True, 'result': {'message_id': 8888}}
        mock_post.return_value = mock_resp

        msg = self.env['telegram.message'].create({
            'direction': 'outgoing',
            'chat_id': self.partner.telegram_chat_id,
            'partner_id': self.partner.id,
            'bot_id': self.bot.id,
            'message_text': 'Outgoing test message',
            'state': 'new',
        })
        msg.send_via_bot(text=msg.message_text, bot=self.bot)
        self.assertEqual(msg.state, 'sent')
        self.assertEqual(msg.name, 'tg_8888')

    @patch('requests.post')
    def test_10_partner_send_telegram_message(self, mock_post):
        """Test sending a Telegram message directly from res.partner."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {'ok': True, 'result': {'message_id': 8889}}
        mock_post.return_value = mock_resp

        res = self.partner.send_telegram_message('Hello from contact card')
        self.assertTrue(res)

    @patch('requests.post')
    def test_11_documents_action_send_telegram(self, mock_post):
        """Test opening wizard from Sales, Purchase, Invoice, and Picking."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {'ok': True, 'result': {'message_id': 8890}}
        mock_post.return_value = mock_resp

        # 1. Sale Order (Quotation -> Confirmed)
        act_so = self.sale_order.action_send_telegram()
        self.assertEqual(act_so.get('res_model'), 'telegram.test')
        self.assertEqual(act_so.get('context', {}).get('default_sale_order_id'), self.sale_order.id)
        att_so_1 = act_so.get('context', {}).get('default_attachment_ids')

        self.sale_order.action_confirm()
        act_so_confirmed = self.sale_order.action_send_telegram()
        att_so_2 = act_so_confirmed.get('context', {}).get('default_attachment_ids')
        if att_so_1 and att_so_2:
            self.assertNotEqual(att_so_1, att_so_2)

        # 2. Purchase Order (RFQ -> Confirmed)
        act_po = self.purchase_order.action_send_telegram()
        self.assertEqual(act_po.get('res_model'), 'telegram.test')
        self.assertEqual(act_po.get('context', {}).get('default_purchase_order_id'), self.purchase_order.id)
        att_po_1 = act_po.get('context', {}).get('default_attachment_ids')

        self.purchase_order.button_confirm()
        act_po_confirmed = self.purchase_order.action_send_telegram()
        att_po_2 = act_po_confirmed.get('context', {}).get('default_attachment_ids')
        if att_po_1 and att_po_2:
            self.assertNotEqual(att_po_1, att_po_2)

        # 3. Customer Invoice
        draft_invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'journal_id': self.sale_journal.id,
        })
        with self.assertRaises(ValidationError):
            draft_invoice.action_send_telegram()

        # Vendor bill should not allow sending via Telegram
        vendor_bill = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': self.partner.id,
            'journal_id': self.purchase_journal.id,
        })
        with self.assertRaises(ValidationError):
            vendor_bill.action_send_telegram()

        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'journal_id': self.sale_journal.id,
        })
        invoice.sudo().write({'state': 'posted'})
        act_inv = invoice.action_send_telegram()
        self.assertEqual(act_inv.get('res_model'), 'telegram.test')
        self.assertEqual(act_inv.get('context', {}).get('default_invoice_id'), invoice.id)

        # 4. Picking
        picking_type = self.env['stock.picking.type'].search([('code', '=', 'outgoing')], limit=1)
        if picking_type:
            location_src = picking_type.default_location_src_id
            location_dest = self.partner.property_stock_customer
            picking = self.env['stock.picking'].create({
                'partner_id': self.partner.id,
                'picking_type_id': picking_type.id,
                'location_id': location_src.id,
                'location_dest_id': location_dest.id,
            })
            act_pick = picking.action_send_telegram()
            self.assertEqual(act_pick.get('res_model'), 'telegram.test')
            self.assertEqual(act_pick.get('context', {}).get('default_picking_id'), picking.id)

    # -------------------------------------------------------------------------
    # 5. Wizard Tests
    # -------------------------------------------------------------------------

    @patch('requests.post')
    def test_12_wizard_send(self, mock_post):
        """Test wizard execution and delegation."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {'ok': True, 'result': {'message_id': 9901}}
        mock_post.return_value = mock_resp

        wizard = self.env['telegram.test'].with_context(
            default_partner_id=self.partner.id,
            default_sale_order_id=self.sale_order.id,
        ).create({
            'partner_id': self.partner.id,
            'sale_order_id': self.sale_order.id,
            'message_text': 'Wizard quote confirmation',
        })

        self.assertEqual(wizard.current_model_id.model, 'sale.order')
        action = wizard.action_send()
        self.assertTrue(action)

    @patch('requests.get')
    def test_13_incoming_animated_sticker(self, mock_get):
        """Test receiving an animated sticker and downloading its static thumbnail."""
        mock_info_resp = MagicMock()
        mock_info_resp.status_code = 200
        mock_info_resp.json.return_value = {
            'ok': True,
            'result': {'file_path': 'thumbnails/thumb_123.webp'}
        }
        mock_file_resp = MagicMock()
        mock_file_resp.status_code = 200
        mock_file_resp.content = b'RIFF....WEBPVP8'
        mock_get.side_effect = [mock_info_resp, mock_file_resp]

        payload = {
            'message': {
                'message_id': 9005,
                'chat': {'id': int(self.partner.telegram_chat_id)},
                'sticker': {
                    'file_id': 'animated_raw_tgs_file_id',
                    'file_unique_id': 'AgADanim123',
                    'is_animated': True,
                    'thumbnail': {
                        'file_id': 'thumb_static_webp_file_id',
                        'file_unique_id': 'AQADthumb123',
                    },
                    'emoji': '👍',
                }
            }
        }
        msg = self.env['telegram.message'].create_incoming(self.bot, payload)
        self.assertTrue(msg)
        self.assertEqual(len(msg.attachment_ids), 1)
        self.assertTrue(msg.attachment_ids[0].name.endswith('.webp'))
        self.assertEqual(msg.attachment_ids[0].mimetype, 'image/webp')

    def test_14_webhook_controller_authorized(self):
        """Test incoming webhook request with valid secret token header."""
        controller = TelegramWebhookController()
        if not self.bot.webhook_secret:
            self.bot.webhook_secret = 'test_webhook_secret_key_12345'
        
        payload = {
            'update_id': 99991,
            'message': {
                'message_id': 8888,
                'chat': {'id': int(self.partner.telegram_chat_id)},
                'text': 'Hello from webhook test'
            }
        }
        raw_body = json.dumps(payload).encode('utf-8')
        mock_httprequest = MagicMock()
        mock_httprequest.headers = {'X-Telegram-Bot-Api-Secret-Token': self.bot.webhook_secret}
        mock_httprequest.data = raw_body

        mock_request = MagicMock()
        mock_request.httprequest = mock_httprequest
        mock_request.env = self.env
        del mock_request.get_json_data

        with patch.object(tc_module, 'request', mock_request):
            response = controller.telegram_webhook()
            self.assertEqual(response.status_code, 200)
            res_data = json.loads(response.data.decode('utf-8'))
            self.assertTrue(res_data.get('ok'))

        # Check incoming message was created
        incoming_msg = self.env['telegram.message'].search([
            ('chat_id', '=', self.partner.telegram_chat_id),
            ('message_text', '=', 'Hello from webhook test')
        ], limit=1)
        self.assertTrue(incoming_msg)

    def test_15_webhook_controller_unauthorized(self):
        """Test incoming webhook request with invalid or missing secret token header."""
        controller = TelegramWebhookController()
        
        # 1. Missing header
        mock_httprequest_no_header = MagicMock()
        mock_httprequest_no_header.headers = {}
        mock_request = MagicMock()
        mock_request.httprequest = mock_httprequest_no_header
        mock_request.env = self.env

        with patch.object(tc_module, 'request', mock_request):
            response = controller.telegram_webhook()
            self.assertEqual(response.status_code, 403)

        # 2. Invalid header
        mock_httprequest_invalid = MagicMock()
        mock_httprequest_invalid.headers = {'X-Telegram-Bot-Api-Secret-Token': 'wrong_secret'}
        mock_request.httprequest = mock_httprequest_invalid

        with patch.object(tc_module, 'request', mock_request):
            response = controller.telegram_webhook()
            self.assertEqual(response.status_code, 403)

    @patch('requests.post')
    def test_16_non_admin_user_can_send_telegram(self, mock_post):
        """Test that a regular non-admin internal user can send Telegram messages without AccessError."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {'ok': True, 'result': {'message_id': 9902}}
        mock_post.return_value = mock_resp

        sales_group = self.env.ref('sales_team.group_sale_salesman_all_leads', raise_if_not_found=False) or \
                      self.env.ref('sales_team.group_sale_salesman', raise_if_not_found=False)
        group_ids = [
            Command.link(self.env.ref('base.group_user').id),
            Command.link(self.env.ref('telegram_chatbox.telegram_group_user').id),
        ]
        if sales_group:
            group_ids.append(Command.link(sales_group.id))

        normal_user = self.env['res.users'].create({
            'name': 'Regular Telegram User',
            'login': 'reg_tg_user',
            'email': 'reg_tg_user@test.com',
            'group_ids': group_ids,
        })
        self.sale_order.user_id = normal_user.id

        wizard = self.env['telegram.test'].with_user(normal_user).with_context(
            default_partner_id=self.partner.id,
            default_sale_order_id=self.sale_order.id,
        ).create({
            'partner_id': self.partner.id,
            'sale_order_id': self.sale_order.id,
            'message_text': 'Message from non-admin user',
        })
        action = wizard.action_send()
        self.assertTrue(action)

