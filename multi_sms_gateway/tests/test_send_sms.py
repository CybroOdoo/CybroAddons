# -*- coding: utf-8 -*-

from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase

from odoo.addons.multi_sms_gateway.wizard import send_sms as send_sms_module


class TestSendSms(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'SMS Recipient',
            'mobile': '+15550000000',
        })
        cls.twilio_gateway = cls.env['sms.gateway'].create({'name': 'twilio'})
        cls.vonage_gateway = cls.env['sms.gateway'].create({'name': 'vonage'})
        cls.telesign_gateway = cls.env['sms.gateway'].create(
            {'name': 'telesign'})
        cls.twilio_config = cls.env['sms.gateway.config'].create({
            'sms_gateway_id': cls.twilio_gateway.id,
            'twilio_account_sid': 'account-sid',
            'twilio_auth_token': 'auth-token',
            'twilio_phone_number': '15550009999',
        })
        cls.vonage_config = cls.env['sms.gateway.config'].create({
            'sms_gateway_id': cls.vonage_gateway.id,
            'vonage_key': 'vonage-key',
            'vonage_secret': 'vonage-secret',
        })
        cls.telesign_config = cls.env['sms.gateway.config'].create({
            'sms_gateway_id': cls.telesign_gateway.id,
            'telesign_customer': 'customer-id',
            'telesign_api_key': 'api-key',
        })

    def _create_wizard(self, config, sms_to='+15550000001', text='Test SMS'):
        return self.env['send.sms'].with_context(
            active_model='res.partner',
            active_id=self.partner.id,
        ).create({
            'sms_id': config.id,
            'sms_to': sms_to,
            'text': text,
        })

    def _assert_sms_history_created(self, gateway, sms_to, text):
        history = self.env['sms.history'].search(
            [
                ('sms_gateway_id', '=', gateway.id),
                ('sms_mobile', '=', sms_to),
                ('sms_text', '=', text),
            ],
            limit=1,
        )
        self.assertTrue(history)

    def _assert_partner_message_posted(self, text):
        self.assertTrue(
            self.partner.message_ids.filtered(
                lambda message: 'Message: %s' % text in message.body
            )
        )

    def test_action_send_sms_with_twilio_sends_each_number_and_logs_history(self):
        wizard = self._create_wizard(
            self.twilio_config,
            sms_to='+15550000001,,+15550000002',
            text='Twilio message',
        )

        with patch.object(send_sms_module, 'Client') as twilio_client:
            client = twilio_client.return_value

            wizard.action_send_sms()

        twilio_client.assert_called_once_with('account-sid', 'auth-token')
        self.assertEqual(client.messages.create.call_count, 2)
        client.messages.create.assert_any_call(
            body='Twilio message',
            from_=15550009999,
            to='+15550000001',
        )
        client.messages.create.assert_any_call(
            body='Twilio message',
            from_=15550009999,
            to='+15550000002',
        )
        self._assert_sms_history_created(
            self.twilio_gateway,
            '+15550000001,,+15550000002',
            'Twilio message',
        )
        self._assert_partner_message_posted('Twilio message')

    def test_action_send_sms_with_twilio_raises_for_client_error(self):
        wizard = self._create_wizard(self.twilio_config)

        with patch.object(send_sms_module, 'Client') as twilio_client:
            twilio_client.return_value.messages.create.side_effect = Exception(
                'invalid credentials')
            with self.assertRaisesRegex(UserError, 'Provide correct credentials'):
                wizard.action_send_sms()

        self.assertFalse(self.env['sms.history'].search([
            ('sms_gateway_id', '=', self.twilio_gateway.id),
            ('sms_mobile', '=', wizard.sms_to),
            ('sms_text', '=', wizard.text),
        ]))

    def test_action_send_sms_with_vonage_sends_each_number_and_logs_history(self):
        wizard = self._create_wizard(
            self.vonage_config,
            sms_to='15550000001,,15550000002',
            text='Vonage message',
        )

        with patch.object(send_sms_module.vonage, 'Client',
                          create=True) as vonage_client, \
                patch.object(send_sms_module.vonage, 'Sms',
                             create=True) as vonage_sms:
            client = vonage_client.return_value
            client.sms.send_message.return_value = {
                'messages': [{'status': '0'}],
            }

            wizard.action_send_sms()

        vonage_client.assert_called_once_with(
            key='vonage-key',
            secret='vonage-secret',
        )
        vonage_sms.assert_called_once_with(client)
        self.assertEqual(client.sms.send_message.call_count, 2)
        client.sms.send_message.assert_any_call({
            'from': 'Vonage APIs',
            'to': '15550000001',
            'text': 'Vonage message',
        })
        client.sms.send_message.assert_any_call({
            'from': 'Vonage APIs',
            'to': '15550000002',
            'text': 'Vonage message',
        })
        self._assert_sms_history_created(
            self.vonage_gateway,
            '15550000001,,15550000002',
            'Vonage message',
        )
        self._assert_partner_message_posted('Vonage message')

    def test_action_send_sms_with_vonage_raises_for_gateway_error(self):
        wizard = self._create_wizard(self.vonage_config)

        with patch.object(send_sms_module.vonage, 'Client',
                          create=True) as vonage_client, \
                patch.object(send_sms_module.vonage, 'Sms', create=True):
            vonage_client.return_value.sms.send_message.return_value = {
                'messages': [{
                    'status': '1',
                    'error-text': 'Rejected by gateway',
                }],
            }
            with self.assertRaisesRegex(UserError, 'Rejected by gateway'):
                wizard.action_send_sms()

        self.assertFalse(self.env['sms.history'].search([
            ('sms_gateway_id', '=', self.vonage_gateway.id),
            ('sms_mobile', '=', wizard.sms_to),
            ('sms_text', '=', wizard.text),
        ]))

    def test_action_send_sms_with_telesign_sends_each_number_and_logs_history(self):
        wizard = self._create_wizard(
            self.telesign_config,
            sms_to='15550000001,,15550000002',
            text='Telesign message',
        )

        with patch.object(send_sms_module, 'MessagingClient') as messaging_client:
            messaging = messaging_client.return_value

            wizard.action_send_sms()

        self.assertEqual(messaging_client.call_count, 2)
        messaging_client.assert_any_call('customer-id', 'api-key')
        messaging.message.assert_any_call(
            '15550000001',
            'Telesign message',
            'ARN',
        )
        messaging.message.assert_any_call(
            '15550000002',
            'Telesign message',
            'ARN',
        )
        self._assert_sms_history_created(
            self.telesign_gateway,
            '15550000001,,15550000002',
            'Telesign message',
        )
        self._assert_partner_message_posted('Telesign message')
