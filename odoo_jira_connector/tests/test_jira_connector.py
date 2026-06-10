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
from unittest.mock import Mock, patch

from odoo.addons.odoo_jira_connector.controllers.jira_connector import JiraWebhook
from odoo.tests import TransactionCase, tagged


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


class TestJiraWebhookController(JiraConnectorTestCase):
    def test_import_jira_data_dispatches_webhook_when_automatic_enabled(self):
        self._set_jira_config(automatic=True, connection=True)
        request_stub = Mock()
        request_stub.env = self.env
        request_stub.httprequest.data = b'{"webhookEvent": "jira:issue_created", "issue": {"key": "JTP-2"}}'
        request_stub.make_json_response.return_value = {'status': 'received'}

        with patch('odoo.addons.odoo_jira_connector.controllers.jira_connector.request', request_stub), \
             patch.object(type(self.env['project.task']), 'webhook_data_handle') as handler:
            result = JiraWebhook.import_jira_data.original_endpoint(JiraWebhook())

        self.assertEqual(result, {'status': 'received'})
        self.assertTrue(handler.called)

    def test_import_jira_data_ignores_body_when_automatic_disabled(self):
        self._set_jira_config(automatic=False, connection=False)
        request_stub = Mock()
        request_stub.env = self.env
        request_stub.httprequest.data = b'{"webhookEvent": "jira:issue_created"}'
        request_stub.make_json_response.return_value = {'status': 'received'}

        with patch('odoo.addons.odoo_jira_connector.controllers.jira_connector.request', request_stub), \
             patch.object(type(self.env['project.task']), 'webhook_data_handle') as handler:
            result = JiraWebhook.import_jira_data.original_endpoint(JiraWebhook())

        self.assertEqual(result, {'status': 'received'})
        handler.assert_not_called()
