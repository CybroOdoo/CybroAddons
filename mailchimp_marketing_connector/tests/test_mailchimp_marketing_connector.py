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

from unittest.mock import patch, MagicMock

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestMailchimpMarketingConnector(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.account = cls.env["mailchimp.account"].create({
            "name": "Test Account",
            "api_key": "test-us1",
        })

        cls.template = cls.env["mailchimp.template"].create({
            "name": "Test Template",
            "is_active": True,
            "type": "regular",
            "is_drag_drop": True,
            "is_responsive": True,
            "share_url": "https://example.com/template.png",
        })

        cls.mailing_list = cls.env["mailchimp.mailing.list"].create({
            "name": "Test Audience",
            "from_name": "Admin",
            "from_email": "admin@example.com",
            "subject": "Test Subject",
            "address": "Test Address",
            "city": "Calicut",
            "permission_reminder": "Subscribed",
            "zip": "673001",
            "mailchimp_account_id": cls.account.id,
        })

    def test_account_creation(self):
        self.assertEqual(self.account.name, "Test Account")
        self.assertEqual(self.account.api_key, "test-us1")

    def test_template_creation(self):
        self.assertTrue(self.template.is_active)
        self.assertEqual(self.template.type, "regular")

    def test_mailing_list_creation(self):
        self.assertEqual(
            self.mailing_list.mailchimp_account_id,
            self.account
        )

    def test_wizard_creation(self):
        wizard = self.env["mailchimp.operations"].create({
            "mailchimp_account_ids": [(6, 0, [self.account.id])],
            "is_import_list": True,
        })
        self.assertTrue(wizard)

    def test_action_import_without_flags(self):
        wizard = self.env["mailchimp.operations"].create({
            "mailchimp_account_ids": [(6, 0, [self.account.id])],
        })
        self.assertFalse(wizard.action_import())

    def test_write_account(self):
        self.account.write({"name": "Updated Account"})
        self.assertEqual(self.account.name, "Updated Account")

    def test_unlink_template(self):
        template = self.env["mailchimp.template"].create({
            "name": "Delete Template",
        })
        template.unlink()
        self.assertFalse(template.exists())

    def test_onchange_template_id(self):
        mailing = self.env["mailing.mailing"].create({
            "subject": "Test Mailing",
            "body_arch": "<p>Test</p>",
            "mailing_type": "mail",
        })
        mailing.template_id = self.template
        mailing._onchange_template_id()
        self.assertIn(self.template.share_url, mailing.body_arch)

    @patch(
        "odoo.addons.mailchimp_marketing_connector.wizards.mailchimp_operations._get_mailchimp_client"
    )
    def test_import_templates(self, mock_client_fn):
        client = MagicMock()
        mock_client_fn.return_value = (client, None, None)

        client.templates.list.return_value = {
            "templates": [{
                "name": "Imported Template",
                "active": True,
                "type": "regular",
                "drag_and_drop": True,
                "thumbnail": "https://example.com/img.png",
            }]
        }

        wizard = self.env["mailchimp.operations"].create({
            "mailchimp_account_ids": [(6, 0, [self.account.id])],
            "is_import_template": True,
        })

        wizard.import_templates()

        template = self.env["mailchimp.template"].search(
            [("name", "=", "Imported Template")],
            limit=1
        )
        self.assertTrue(template)

    @patch(
        "odoo.addons.mailchimp_marketing_connector.wizards.mailchimp_operations._get_mailchimp_client"
    )
    def test_import_campaigns(self, mock_client_fn):
        client = MagicMock()
        mock_client_fn.return_value = (client, None, None)

        client.campaigns.list.return_value = {
            "campaigns": [{
                "create_time": "2026-01-01",
                "emails_sent": 10,
                "settings": {
                    "title": "Test Campaign"
                }
            }]
        }

        wizard = self.env["mailchimp.operations"].create({
            "mailchimp_account_ids": [(6, 0, [self.account.id])],
        })

        wizard.import_campaigns()

        campaign = self.env["utm.campaign"].search(
            [("title", "=", "Test Campaign")],
            limit=1
        )
        self.assertTrue(campaign)