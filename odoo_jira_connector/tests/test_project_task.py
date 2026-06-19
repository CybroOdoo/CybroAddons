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
from odoo.tools import html2plaintext


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


class TestProjectTask(JiraConnectorTestCase):
    def test_compute_task_sprint_active_follows_project(self):
        self.project.sprint_active = True
        self.task._compute_task_sprint_active()
        self.assertTrue(self.task.task_sprint_active)
        self.project.sprint_active = False
        self.task._compute_task_sprint_active()
        self.assertFalse(self.task.task_sprint_active)

    def test_create_exports_task_when_automatic_enabled(self):
        self._set_jira_config(automatic=True, connection=True)
        self.Param.set_param('export_task_count', 1)
        with patch('odoo.addons.odoo_jira_connector.models.project_task.requests.post',
                   return_value=MockResponse({'key': 'JTP-99'})) as post_mock:
            task = self.env['project.task'].create({
                'name': 'Exported Task',
                'project_id': self.project.id,
                'description': '<p>Task description</p>',
            })

        self.assertEqual(task.task_id_jira, 'JTP-99')
        self.assertEqual(int(self.Param.get_param('export_task_count')), 2)
        self.assertTrue(post_mock.called)

    def test_write_updates_jira_issue_summary(self):
        self._set_jira_config(automatic=True, connection=True)
        with patch('odoo.addons.odoo_jira_connector.models.project_task.requests.put',
                   return_value=MockResponse({})) as put_mock:
            self.task.write({'name': 'Updated Jira Task'})

        self.assertTrue(put_mock.called)

    def test_unlink_deletes_jira_issue(self):
        self._set_jira_config(automatic=False, connection=False)
        task = self.env['project.task'].create({
            'name': 'Delete Jira Task',
            'project_id': self.project.id,
            'task_id_jira': 'JTP-50',
        })
        self._set_jira_config(automatic=True, connection=True)
        with patch('odoo.addons.odoo_jira_connector.models.project_task.requests.delete',
                   return_value=MockResponse({})) as delete_mock:
            task.unlink()

        self.assertTrue(delete_mock.called)

    def test_webhook_data_handle_dispatches_issue_created(self):
        with patch.object(type(self.env['project.task']), 'create_task') as create_task:
            self.env['project.task'].webhook_data_handle({}, 'jira:issue_created')
        self.assertTrue(create_task.called)

    def test_project_webhook_create_update_delete(self):
        with patch('odoo.addons.odoo_jira_connector.models.project_task.requests.request',
                   return_value=MockResponse({'style': 'next-gen'})):
            self.env['project.task'].create_project({
                'project': {'id': '5101', 'name': 'Webhook Project', 'key': 'WHP'}
            })
        project = self.env['project.project'].search([('project_id_jira', '=', 5101)])
        self.assertTrue(project)
        self.assertTrue(project.sprint_active)

        self.env['project.task'].update_project({
            'project': {'id': '5101', 'name': 'Webhook Project Renamed'}
        })
        self.assertEqual(project.name, 'Webhook Project Renamed')

        self.env['project.task'].delete_project({'project': {'id': '5101'}})
        self.assertFalse(project.exists())

    def test_task_webhook_create_and_delete(self):
        self.env['project.task'].create_task({
            'issue': {
                'key': 'JTP-77',
                'fields': {
                    'summary': 'Webhook Task',
                    'project': {'id': str(self.project.project_id_jira)},
                },
            }
        })
        task = self.env['project.task'].search([('task_id_jira', '=', 'JTP-77')])
        self.assertTrue(task)

        self.env['project.task'].delete_task({'issue': {'key': 'JTP-77'}})
        self.assertFalse(task.exists())

    def test_comment_webhook_create_and_delete(self):
        self.env['project.task'].create_comment({
            'issue': {'key': self.task.task_id_jira},
            'comment': {'id': '8801', 'body': 'prefix.Comment body'},
        })
        message = self.env['mail.message'].search([('message_id_jira', '=', 8801)])
        self.assertTrue(message)
        self.assertIn('Comment body', message.body)

        self.env['project.task'].delete_comment({'comment': {'id': '8801'}})
        self.assertFalse(message.exists())

    def test_user_webhook_create_and_delete(self):
        self.env['project.task'].create_user({
            'user': {'accountId': 'webhook-user-1', 'displayName': 'Webhook User'}
        })
        user = self.env['res.users'].search([('jira_user_key', '=', 'webhook-user-1')])
        self.assertTrue(user)

        self.env['project.task'].delete_user({'accountId': 'webhook-user-1'})
        self.assertFalse(user.exists())

    def test_board_configuration_change_creates_stage(self):
        self.env['project.task'].board_configuration_change({
            'configuration': {
                'id': 9001,
                'location': {'key': self.project.jira_project_key},
                'columnConfig': {'columns': [
                    {'name': 'Backlog', 'statuses': [{'id': '0'}]},
                    {'name': 'In Progress', 'statuses': [{'id': '3'}]},
                ]},
            }
        })
        stage = self.env['project.task.type'].search([('stages_jira_id', '=', '3')])
        self.assertTrue(stage)
        self.assertEqual(self.project.board_id_jira, 9001)

    def test_update_task_status_description_summary_attachment_and_sprint(self):
        stage = self.env['project.task.type'].create({
            'name': 'QA',
            'stages_jira_id': '5',
            'project_ids': [(4, self.project.id)],
        })
        self.env['project.task'].update_task({
            'issue': {'key': self.task.task_id_jira},
            'changelog': {'items': [{'field': 'status', 'to': '5'}]},
        })
        self.assertEqual(self.task.stage_id, stage)

        self.env['project.task'].update_task({
            'issue': {'key': self.task.task_id_jira},
            'changelog': {'items': [{'field': 'description', 'to': 'desc', 'toString': 'Updated description'}]},
        })
        self.assertEqual(html2plaintext(self.task.description), 'Updated description')

        self.env['project.task'].update_task({
            'issue': {'key': self.task.task_id_jira},
            'changelog': {'items': [{'field': 'summary', 'to': 'summary', 'toString': 'Updated summary'}]},
        })
        self.assertEqual(self.task.name, 'Updated summary')

        with patch('odoo.addons.odoo_jira_connector.models.project_task.requests.get',
                   return_value=MockResponse(content=b'attachment-data')):
            self.env['project.task'].update_task({
                'issue': {
                    'key': self.task.task_id_jira,
                    'fields': {'attachment': [{
                        'id': '9901',
                        'filename': 'file.txt',
                        'mimeType': 'text/plain',
                        'content': 'https://jira.example.com/file.txt',
                    }]},
                },
                'changelog': {'items': [{'field': 'Attachment', 'to': '9901'}]},
            })
        attachment = self.env['ir.attachment'].search([('attachment_id_jira', '=', 9901)])
        self.assertTrue(attachment)

        self.env['project.task'].update_task({
            'issue': {
                'key': self.task.task_id_jira,
                'fields': {
                    'summary': 'Sprint Task',
                    'project': {'key': self.project.jira_project_key},
                    'customfield_10020': [{'id': 6101, 'name': 'Sprint Webhook'}],
                },
            },
            'changelog': {'items': [{'field': 'Sprint', 'to': '6101'}]},
        })
        sprint = self.env['jira.sprint'].search([('sprint_id_jira', '=', 6101)])
        self.assertTrue(sprint)

    def test_delete_attachment_and_sprint_lifecycle_webhooks(self):
        attachment = self.env['ir.attachment'].create({
            'name': 'delete.txt',
            'datas': 'ZGF0YQ==',
            'attachment_id_jira': 7701,
        })
        self.env['project.task'].delete_attachment({'attachment': {'id': 7701}})
        self.assertFalse(attachment.exists())

        sprint = self.env['jira.sprint'].create({
            'name': 'Lifecycle Sprint',
            'sprint_id_jira': 6201,
            'project_id': self.project.id,
        })
        self.env['project.task'].sprint_started({
            'sprint': {
                'id': 6201,
                'startDate': '2026-01-01T10:00:00.000Z',
                'endDate': '2026-01-15T10:00:00.000Z',
                'goal': 'Ship',
            }
        })
        self.assertEqual(sprint.state, 'ongoing')
        self.assertEqual(sprint.sprint_goal, 'Ship')

        done_stage = self.env['project.task.type'].create({
            'name': 'Done',
            'project_ids': [(4, self.project.id)],
        })
        done_task = self.env['project.task'].create({
            'name': 'Done Sprint Task',
            'project_id': self.project.id,
            'stage_id': done_stage.id,
            'sprint_id': sprint.id,
        })
        self.env['project.task'].sprint_closed({'sprint': {'id': 6201}})
        self.assertEqual(sprint.state, 'completed')
        self.assertFalse(done_task.exists())
