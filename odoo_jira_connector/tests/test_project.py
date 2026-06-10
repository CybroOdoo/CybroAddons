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


class TestProjectProject(JiraConnectorTestCase):
    def test_action_get_sprint_returns_project_sprint_action(self):
        action = self.project.action_get_sprint()
        self.assertEqual(action['res_model'], 'jira.sprint')
        self.assertEqual(action['context'], {'default_project_id': self.project.id})
        self.assertEqual(action['domain'], [('project_id', '=', self.project.id)])

    def test_create_exports_project_when_automatic_enabled(self):
        self._set_jira_config(automatic=True, connection=True)
        self.Param.set_param('import_project_count', 1)

        def request(method, url, **kwargs):
            if method == 'GET':
                return MockResponse([])
            return MockResponse({'projectId': 2002, 'projectKey': 'NTP'}, status_code=201)

        with patch('odoo.addons.odoo_jira_connector.models.project.requests.request', side_effect=request):
            project = self.env['project.project'].create({'name': 'New Test Project'})

        self.assertEqual(project.project_id_jira, 2002)
        self.assertEqual(project.jira_project_key, 'NTP')
        self.assertEqual(int(self.Param.get_param('import_project_count')), 2)

    def test_write_updates_jira_project_name(self):
        self._set_jira_config(automatic=True, connection=True)
        with patch('odoo.addons.odoo_jira_connector.models.project.requests.get',
                   return_value=MockResponse({'name': 'Old Name'})), \
             patch('odoo.addons.odoo_jira_connector.models.project.requests.request',
                   return_value=MockResponse({})) as request_mock:
            self.project.write({'name': 'Renamed Project'})

        self.assertTrue(any(call.args[0] == 'PUT' for call in request_mock.call_args_list))
