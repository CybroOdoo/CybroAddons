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

from odoo.exceptions import UserError
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

    def _settings(self):
        return self.env['res.config.settings'].create({
            'url': 'https://jira.example.com/',
            'user_id_jira': 'jira@example.com',
            'api_token': 'token',
        })


class TestResConfigSettings(JiraConnectorTestCase):
    def test_action_test_connection_requires_credentials(self):
        settings = self.env['res.config.settings'].create({
            'url': False,
            'user_id_jira': False,
            'api_token': False,
        })
        with self.assertRaises(UserError):
            settings.action_test_connection()

    def test_action_test_connection_success_sets_connection_parameter(self):
        settings = self._settings()
        with patch('odoo.addons.odoo_jira_connector.models.res_config_settings.requests.get',
                   return_value=MockResponse([])):
            action = settings.action_test_connection()

        self.assertEqual(action['params']['type'], 'success')
        self.assertEqual(self.Param.get_param('odoo_jira_connector.connection'), 'True')

    def test_find_attachment_type_and_guess_mimetype(self):
        settings = self._settings()
        attachment = self.env['ir.attachment'].create({
            'name': 'sheet.xlsx',
            'datas': 'ZGF0YQ==',
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        self.assertEqual(settings.find_attachment_type(attachment), 'xlsx')
        self.assertEqual(settings._guess_mimetype('file.pdf'), 'application/pdf')
        self.assertEqual(settings._guess_mimetype('file.unknownext'), 'application/octet-stream')

    def test_action_import_users_creates_jira_users(self):
        settings = self._settings()
        with patch('odoo.addons.odoo_jira_connector.models.res_config_settings.requests.get',
                   return_value=MockResponse([{
                       'displayName': 'Imported Jira User',
                       'emailAddress': 'imported.jira.user@example.com',
                       'accountId': 'jira-account-2',
                   }])):
            action = settings.action_import_users()

        user = self.env['res.users'].search([('jira_user_key', '=', 'jira-account-2')])
        self.assertTrue(user)
        self.assertEqual(action['params']['type'], 'success')

    def test_action_export_users_exports_unmapped_email_user(self):
        settings = self._settings()
        user = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Export Settings User',
            'login': 'export.settings.user@example.com',
        })
        with patch('odoo.addons.odoo_jira_connector.models.res_config_settings.requests.get',
                   return_value=MockResponse([])), \
             patch('odoo.addons.odoo_jira_connector.models.res_config_settings.requests.post',
                   return_value=MockResponse({'accountId': 'jira-account-3'})):
            action = settings.action_export_users()

        self.assertEqual(user.jira_user_key, 'jira-account-3')
        self.assertEqual(action['params']['type'], 'success')

    def test_action_import_from_jira_creates_project_and_task(self):
        settings = self._settings()

        def get(url, **kwargs):
            if url.endswith('/rest/api/2/project'):
                return MockResponse([{'id': '3003', 'key': 'IMP', 'name': 'Imported Project'}])
            if '/search' in url:
                return MockResponse({'issues': [{'key': 'IMP-1', 'fields': {'summary': 'Imported Task'}}]})
            if 'fields=attachment' in url:
                return MockResponse({'fields': {'attachment': []}})
            if url.endswith('/comment'):
                return MockResponse({'comments': []})
            return MockResponse({})

        with patch('odoo.addons.odoo_jira_connector.models.res_config_settings.requests.get',
                   side_effect=get):
            action = settings.action_import_from_jira()

        project = self.env['project.project'].search([('project_id_jira', '=', 3003)])
        task = self.env['project.task'].search([('task_id_jira', '=', 'IMP-1')])
        self.assertTrue(project)
        self.assertTrue(task)
        self.assertEqual(action['params']['type'], 'success')

    def test_action_export_to_jira_creates_missing_project(self):
        settings = self._settings()
        project = self.env['project.project'].create({'name': 'Export Missing Project'})
        self.env['project.task'].create({'name': 'Export Missing Task', 'project_id': project.id})

        def request(method, url, **kwargs):
            if method == 'GET':
                return MockResponse([])
            return MockResponse({'projectId': 4004, 'projectKey': 'EMP'}, status_code=201)

        with patch('odoo.addons.odoo_jira_connector.models.res_config_settings.requests.request',
                   side_effect=request), \
             patch('odoo.addons.odoo_jira_connector.models.res_config_settings.requests.post',
                   return_value=MockResponse({'key': 'EMP-1'})):
            action = settings.action_export_to_jira()

        self.assertEqual(project.project_id_jira, 4004)
        self.assertEqual(action['params']['type'], 'success')
