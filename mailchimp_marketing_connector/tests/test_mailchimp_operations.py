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

from types import SimpleNamespace
from importlib import import_module
from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestMailchimpOperations(TransactionCase):

    def _make_wizard(self, **values):
        defaults = {
            'is_import_list': False,
            'is_import_template': False,
            'is_import_campaigns': False,
            'is_export_list': False,
            'mailchimp_account_ids': SimpleNamespace(api_key='abc-us1', is_auto_sync=False),
            'env': SimpleNamespace(),
        }
        defaults.update(values)
        return SimpleNamespace(**defaults)

    def test_action_import_dispatches_selected_actions(self):
        MailchimpOperations = import_module(
            'odoo.addons.mailchimp_marketing_connector.wizards.mailchimp_operations'
        ).MailchimpOperations

        calls = []

        class FakeWizard:
            is_import_list = True
            is_import_template = True
            is_import_campaigns = True

            def import_list(self):
                calls.append('list')

            def import_templates(self):
                calls.append('template')

            def import_campaigns(self):
                calls.append('campaign')

        MailchimpOperations.action_import(FakeWizard())

        self.assertEqual(calls, ['list', 'template', 'campaign'])

    def test_export_list_requires_company_details(self):
        MailchimpOperations = import_module(
            'odoo.addons.mailchimp_marketing_connector.wizards.mailchimp_operations'
        ).MailchimpOperations

        wizard = self._make_wizard()
        wizard.env.company = SimpleNamespace(
            email='',
            street='',
            city='',
            zip='',
            country_id=None,
        )

        with patch(
            'odoo.addons.mailchimp_marketing_connector.wizards.mailchimp_operations._get_mailchimp_client'
        ) as get_client:
            get_client.return_value = (SimpleNamespace(lists=SimpleNamespace()), None, Exception)
            original_translate = MailchimpOperations.export_list.__globals__.get('_')
            MailchimpOperations.export_list.__globals__['_'] = lambda message: message
            try:
                with self.assertRaises(UserError):
                    MailchimpOperations.export_list(wizard)
            finally:
                MailchimpOperations.export_list.__globals__['_'] = original_translate

    def test_import_templates_creates_missing_template(self):
        MailchimpOperations = import_module(
            'odoo.addons.mailchimp_marketing_connector.wizards.mailchimp_operations'
        ).MailchimpOperations

        created = []

        class FakeTemplateModel:
            def search(self, domain):
                return []

            def create(self, vals):
                created.append(vals)

        class FakeClient:
            class templates:
                @staticmethod
                def list():
                    return {
                        'templates': [
                            {
                                'name': 'Welcome',
                                'active': True,
                                'type': 'regular',
                                'drag_and_drop': False,
                                'thumbnail': 'https://example.com/thumb.png',
                            }
                        ]
                    }

        wizard = self._make_wizard()
        wizard.env = {
            'mailchimp.template': FakeTemplateModel(),
        }

        with patch(
            'odoo.addons.mailchimp_marketing_connector.wizards.mailchimp_operations._get_mailchimp_client',
            return_value=(FakeClient(), None, None),
        ):
            MailchimpOperations.import_templates(wizard)

        self.assertEqual(created[0]['name'], 'Welcome')
        self.assertTrue(created[0]['is_active'])

    def test_sync_mailchimp_list_runs_all_when_auto_sync_enabled(self):
        MailchimpOperations = import_module(
            'odoo.addons.mailchimp_marketing_connector.wizards.mailchimp_operations'
        ).MailchimpOperations

        calls = []

        class FakeAccounts:
            is_auto_sync = True

        wizard = self._make_wizard(mailchimp_account_ids=FakeAccounts())
        wizard.import_list = lambda: calls.append('list')
        wizard.import_templates = lambda: calls.append('template')
        wizard.import_campaigns = lambda: calls.append('campaign')
        wizard.export_list = lambda: calls.append('export')

        MailchimpOperations.sync_mailchimp_list(wizard)

        self.assertEqual(calls, ['list', 'template', 'campaign', 'export'])
