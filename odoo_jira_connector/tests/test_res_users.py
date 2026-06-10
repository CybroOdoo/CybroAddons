# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged


class MockResponse:
    def __init__(self, payload=None, status_code=200, ok=True, content=b'data'):
        self._payload = payload
        self.status_code = status_code
        self.ok = ok
        self.content = content
        self.text = str(payload)

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests
            raise requests.exceptions.HTTPError(response=self)


@tagged('post_install', '-at_install')
class JiraConnectorTestCase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Param = cls.env['ir.config_parameter'].sudo()
        cls._set_jira_config(automatic=False, connection=False)
        cls.project = cls.env['project.project'].create({
            'name': 'Jira Test Project',
            'project_id_jira': 1001,
            'jira_project_key': 'JTP',
        })
        cls.task = cls.env['project.task'].create({
            'name': 'Jira Test Task',
            'project_id': cls.project.id,
            'task_id_jira': 'JTP-1',
        })

    @classmethod
    def _set_jira_config(cls, automatic=False, connection=False):
        cls.Param.set_param('odoo_jira_connector.url', 'https://jira.example.com/')
        cls.Param.set_param('odoo_jira_connector.user_id_jira', 'jira@example.com')
        cls.Param.set_param('odoo_jira_connector.api_token', 'token')
        cls.Param.set_param('odoo_jira_connector.automatic', automatic)
        cls.Param.set_param('odoo_jira_connector.connection', connection)


class TestResUsers(JiraConnectorTestCase):
    def test_create_exports_email_user_to_jira(self):
        self._set_jira_config(automatic=True, connection=True)
        with patch('odoo.addons.odoo_jira_connector.models.res_users.requests.post',
                   return_value=MockResponse({'accountId': 'account-1'})) as post_mock:
            user = self.env['res.users'].with_context(no_reset_password=True).create({
                'name': 'Jira Export User',
                'login': 'jira.export.user@example.com',
            })

        self.assertEqual(user.jira_user_key, 'account-1')
        self.assertTrue(post_mock.called)

    def test_create_skips_non_email_login(self):
        self._set_jira_config(automatic=True, connection=True)
        with patch('odoo.addons.odoo_jira_connector.models.res_users.requests.post') as post_mock:
            user = self.env['res.users'].with_context(no_reset_password=True).create({
                'name': 'No Email User',
                'login': 'not-an-email-login',
            })

        self.assertFalse(user.jira_user_key)
        post_mock.assert_not_called()
