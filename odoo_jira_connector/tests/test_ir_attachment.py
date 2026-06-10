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


class TestIrAttachment(JiraConnectorTestCase):
    def test_create_exports_supported_task_attachment(self):
        self._set_jira_config(automatic=True, connection=True)
        with patch('odoo.addons.odoo_jira_connector.models.ir_attachment.requests.post',
                   return_value=MockResponse([{'id': 701}])) as post_mock:
            attachment = self.env['ir.attachment'].create({
                'name': 'document.pdf',
                'datas': 'ZGF0YQ==',
                'res_model': 'project.task',
                'res_id': self.task.id,
                'mimetype': 'application/pdf',
            })

        self.assertEqual(attachment.attachment_id_jira, 701)
        self.assertTrue(post_mock.called)

    def test_unlink_deletes_jira_attachment(self):
        self._set_jira_config(automatic=True, connection=True)
        attachment = self.env['ir.attachment'].create({
            'name': 'jira-file.pdf',
            'datas': 'ZGF0YQ==',
            'res_model': 'project.task',
            'res_id': self.task.id,
            'mimetype': 'application/pdf',
            'attachment_id_jira': 702,
        })
        with patch('odoo.addons.odoo_jira_connector.models.ir_attachment.requests.delete',
                   return_value=MockResponse({})) as delete_mock:
            attachment.unlink()

        self.assertTrue(delete_mock.called)
