# -*- coding: utf-8 -*-

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestSmsGatewayConfig(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Config = cls.env['sms.gateway.config']
        cls.twilio_gateway = cls.env['sms.gateway'].create({'name': 'twilio'})
        cls.vonage_gateway = cls.env['sms.gateway'].create({'name': 'vonage'})
        cls.telesign_gateway = cls.env['sms.gateway'].create(
            {'name': 'telesign'})

    def test_twilio_credentials_are_required(self):
        with self.assertRaisesRegex(UserError, 'Twilio'):
            self.Config.create({'sms_gateway_id': self.twilio_gateway.id})

        config = self.Config.create({
            'sms_gateway_id': self.twilio_gateway.id,
            'twilio_account_sid': 'account-sid',
            'twilio_auth_token': 'auth-token',
            'twilio_phone_number': '15550009999',
        })

        self.assertTrue(config)

    def test_vonage_credentials_are_required(self):
        with self.assertRaisesRegex(UserError, 'Vonage'):
            self.Config.create({'sms_gateway_id': self.vonage_gateway.id})

        config = self.Config.create({
            'sms_gateway_id': self.vonage_gateway.id,
            'vonage_key': 'vonage-key',
            'vonage_secret': 'vonage-secret',
        })

        self.assertTrue(config)

    def test_telesign_credentials_are_required(self):
        with self.assertRaisesRegex(UserError, 'Telesign'):
            self.Config.create({'sms_gateway_id': self.telesign_gateway.id})

        config = self.Config.create({
            'sms_gateway_id': self.telesign_gateway.id,
            'telesign_customer': 'customer-id',
            'telesign_api_key': 'api-key',
        })

        self.assertTrue(config)
