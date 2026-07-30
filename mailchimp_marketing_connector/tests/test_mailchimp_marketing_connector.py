# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Harshitha AP(<https://www.cybrosys.com>)
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
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestMailchimpMarketingConnector(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.account = cls.env['mailchimp.account'].create({
            'name': 'Test Account',
            'api_key': 'dummy-us1',
        })

        cls.template = cls.env['mailchimp.template'].create({
            'name': 'Test Template',
            'share_url': 'https://example.com/template.png',
            'is_active': True,
        })

    # ---------------------------------------------------------
    # Mailchimp Account
    # ---------------------------------------------------------

    def test_mailchimp_account_creation(self):
        self.assertTrue(self.account)
        self.assertEqual(self.account.name, 'Test Account')
        self.assertEqual(self.account.api_key, 'dummy-us1')

    # ---------------------------------------------------------
    # Mailchimp Template
    # ---------------------------------------------------------

    def test_mailchimp_template_creation(self):
        self.assertTrue(self.template)
        self.assertEqual(
            self.template.share_url,
            'https://example.com/template.png'
        )

    # ---------------------------------------------------------
    # Mailing Contact Extension
    # ---------------------------------------------------------

    def test_mailing_contact_extended_fields(self):
        contact = self.env['mailing.contact'].create({
            'name': 'Demo Contact',
            'email': 'demo@example.com',
            'address': 'Street 1',
            'city': 'Calicut',
            'zip': '673001',
        })

        self.assertEqual(contact.address, 'Street 1')
        self.assertEqual(contact.city, 'Calicut')
        self.assertEqual(contact.zip, '673001')

    # ---------------------------------------------------------
    # Mailing Mailing Onchange
    # ---------------------------------------------------------

    def test_onchange_template_id_updates_body(self):
        mailing = self.env['mailing.mailing'].create({
            'subject': 'Test Campaign',
            'mailing_model_id': self.env.ref(
                'mass_mailing.model_mailing_list'
            ).id,
        })

        mailing.template_id = self.template
        mailing._onchange_template_id()

        self.assertIn(
            self.template.share_url,
            mailing.body_arch or ''
        )

    # ---------------------------------------------------------
    # Mailchimp Mailing List
    # ---------------------------------------------------------

    def test_mailchimp_mailing_list_creation(self):
        mailing_list = self.env['mailchimp.mailing.list'].create({
            'name': 'Audience 1',
            'mailchimp_account_id': self.account.id,
            'from_name': 'Admin',
            'from_email': 'admin@example.com',
            'subject': 'Newsletter',
            'address': 'Street 1',
            'city': 'Calicut',
            'permission_reminder': 'Subscribed user',
            'zip': '673001',
        })

        self.assertEqual(mailing_list.name, 'Audience 1')
        self.assertEqual(
            mailing_list.mailchimp_account_id,
            self.account
        )