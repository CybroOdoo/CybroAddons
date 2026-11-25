# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from datetime import datetime
from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tools import html2plaintext

from .common import LOGGER, JIRA_URL, JiraTestCommon, MockResponse


class TestProjectTask(JiraTestCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Task = cls.env['project.task']

    def issue_event(self, key, items, **issue_fields):
        """Payload of a jira:issue_updated event."""
        issue_fields.setdefault('project', {'id': '1001', 'key': 'JTP'})
        return {'issue': {'key': key, 'fields': issue_fields},
                'changelog': {'items': items}}

    def test_compute_task_sprint_active_follows_project(self):
        self.project.sprint_active = True
        self.assertTrue(self.task.task_sprint_active)
        self.project.sprint_active = False
        self.assertFalse(self.task.task_sprint_active)

    def test_create_exports_task_with_plain_text_description(self):
        self.set_jira_config(automatic=True)
        with self.mock_jira({('POST', '/rest/api/2/issue'): {'key': 'JTP-99'}}) as jira:
            task = self.Task.create({
                'name': 'Exported Task', 'project_id': self.project.id,
                'description': '<p>Task description</p>'})
        self.assertEqual(task.task_id_jira, 'JTP-99')
        fields = jira.requests_to('POST', '/rest/api/2/issue')[0]['json']['fields']
        self.assertEqual(fields['description'], 'Task description')
        self.assertEqual(fields['project'], {'key': 'JTP'})

    def test_create_keeps_task_when_jira_refuses_it(self):
        self.set_jira_config(automatic=True)
        with self.mock_jira({('POST', '/rest/api/2/issue'): MockResponse({}, 400)}), \
                self.assertLogs(LOGGER, 'ERROR'):
            task = self.Task.create({'name': 'Refused Task', 'project_id': self.project.id})
        self.assertTrue(task.exists())
        self.assertFalse(task.task_id_jira)

    def test_write_renames_jira_issue(self):
        self.set_jira_config(automatic=True)
        with self.mock_jira() as jira:
            self.task.write({'name': 'Updated Jira Task'})
            self.task.write({'priority': '1'})
        puts = jira.requests_to('PUT', '/rest/api/2/issue/JTP-1')
        self.assertEqual([call['json'] for call in puts],
                         [{'fields': {'summary': 'Updated Jira Task'}}])

    def test_write_logs_rename_errors(self):
        self.set_jira_config(automatic=True)
        with self.mock_jira({('PUT', '/rest/api/2/issue/JTP-1'): MockResponse({}, 404)}), \
                self.assertLogs(LOGGER, 'ERROR'):
            self.task.write({'name': 'Lost Issue'})

    def test_unlink_deletes_jira_issue(self):
        task = self.Task.create({'name': 'Delete Me', 'project_id': self.project.id,
                                 'task_id_jira': 'JTP-50'})
        self.set_jira_config(automatic=True)
        with self.mock_jira() as jira:
            task.unlink()
        self.assertEqual(len(jira.requests_to('DELETE', '/rest/api/2/issue/JTP-50')), 1)

    def test_unlink_logs_jira_errors(self):
        self.set_jira_config(automatic=True)
        with self.mock_jira({('DELETE', '/rest/api/2/issue/JTP-1'): MockResponse({}, 403)}), \
                self.assertLogs(LOGGER, 'ERROR'):
            self.task.unlink()
        self.assertFalse(self.task.exists())

    def test_synced_task_in_folded_stage_is_protected(self):
        folded = self.env['project.task.type'].create({
            'name': 'Closed', 'fold': True, 'project_ids': [(4, self.project.id)]})
        self.task.stage_id = folded
        self.set_jira_config(automatic=True)
        with self.mock_jira() as jira, self.assertRaises(UserError):
            self.task.unlink()
        self.assertFalse(jira.calls)
        self.task.with_context(jira_skip_sync=True).unlink()
        self.assertFalse(self.task.exists())

    def test_webhook_data_handle_dispatches_without_pushing_back(self):
        with patch.object(type(self.Task), 'create_task') as create_task:
            self.Task.webhook_data_handle({'issue': {}}, 'jira:issue_created')
            self.Task.webhook_data_handle({}, 'unknown_event')
        create_task.assert_called_once_with({'issue': {}})

    def test_project_webhooks(self):
        self.set_jira_config(automatic=True)
        with self.mock_jira({('GET', '/rest/api/2/project/WHP'): {'style': 'next-gen'}}) as jira:
            self.Task.webhook_data_handle(
                {'project': {'id': '5101', 'name': 'Webhook Project', 'key': 'WHP'}},
                'project_created')
            self.Task.webhook_data_handle(
                {'project': {'id': '5101', 'name': 'Webhook Project', 'key': 'WHP'}},
                'project_created')
        project = self.env['project.project'].search([('project_id_jira', '=', 5101)])
        self.assertEqual(len(project), 1)
        self.assertTrue(project.sprint_active)
        # Created from Jira: not sent back to Jira.
        self.assertFalse(jira.requests_to('POST'))

        with self.mock_jira() as jira:
            self.Task.webhook_data_handle(
                {'project': {'id': '5101', 'name': 'Webhook Project Renamed'}},
                'project_updated')
        self.assertEqual(project.name, 'Webhook Project Renamed')
        self.assertFalse(jira.requests_to('PUT'))

        self.Task.webhook_data_handle({'project': {'id': '5101'}}, 'project_soft_deleted')
        self.assertFalse(project.exists())

    def test_project_created_links_exported_project(self):
        exported = self.env['project.project'].create({'name': 'Exported From Odoo'})
        with self.mock_jira({('GET', '/rest/api/2/project/EXP'): {'style': 'classic'}}):
            self.Task.create_project(
                {'project': {'id': '5102', 'name': 'Exported From Odoo', 'key': 'EXP'}})
        self.assertEqual(exported.project_id_jira, 5102)
        self.assertFalse(exported.sprint_active)
        self.assertEqual(self.env['project.project'].search_count(
            [('name', '=', 'Exported From Odoo')]), 1)

    def test_project_created_when_style_cannot_be_read(self):
        with self.mock_jira({('GET', '/rest/api/2/project/ERR'): MockResponse({}, 500)}), \
                self.assertLogs(LOGGER, 'ERROR'):
            self.Task.create_project({'project': {'id': '5103', 'name': 'No Style', 'key': 'ERR'}})
        project = self.env['project.project'].search([('project_id_jira', '=', 5103)])
        self.assertFalse(project.sprint_active)
        self.Param.set_param('odoo_jira_connector.url', False)
        self.Task.create_project({'project': {'id': '5104', 'name': 'No Url', 'key': 'NOU'}})
        self.assertTrue(self.env['project.project'].search([('project_id_jira', '=', 5104)]))

    def test_task_webhooks(self):
        exported = self.Task.create({'name': 'Exported Task', 'project_id': self.project.id})
        event = {'issue': {'key': 'JTP-77', 'fields': {
            'summary': 'Webhook Task', 'project': {'id': '1001'}}}}
        self.Task.webhook_data_handle(event, 'jira:issue_created')
        self.Task.webhook_data_handle(event, 'jira:issue_created')
        task = self.Task.search([('task_id_jira', '=', 'JTP-77')])
        self.assertEqual(len(task), 1)
        self.assertEqual(task.project_id, self.project)

        self.Task.create_task({'issue': {'key': 'JTP-78', 'fields': {
            'summary': 'Exported Task', 'project': {'id': '1001'}}}})
        self.assertEqual(exported.task_id_jira, 'JTP-78')

        self.Task.create_task({'issue': {'key': 'UNK-1', 'fields': {
            'summary': 'Unknown project', 'project': {'id': '999999'}}}})
        self.assertFalse(self.Task.search([('task_id_jira', '=', 'UNK-1')]))

        self.set_jira_config(automatic=True)
        with self.mock_jira() as jira:
            self.Task.webhook_data_handle({'issue': {'key': 'JTP-77'}}, 'jira:issue_deleted')
        self.assertFalse(task.exists())
        self.assertFalse(jira.calls)

    def test_comment_webhooks(self):
        self.Task.webhook_data_handle({
            'issue': {'key': 'JTP-1'},
            'comment': {'id': '8801', 'body': 'First sentence. Second sentence.'},
        }, 'comment_created')
        message = self.env['mail.message'].search([('message_id_jira', '=', 8801)])
        self.assertEqual(html2plaintext(message.body), 'First sentence. Second sentence.')
        self.assertEqual(message.res_id, self.task.id)
        self.assertEqual(message.message_type, 'comment')

        exported = self.task.message_post(body='Sent from Odoo', message_type='comment')
        self.Task.create_comment({'issue': {'key': 'JTP-1'},
                                  'comment': {'id': '8802', 'body': 'Sent from Odoo'}})
        self.assertEqual(exported.message_id_jira, 8802)

        count = self.env['mail.message'].search_count([])
        self.Task.create_comment({'issue': {'key': 'JTP-1'},
                                  'comment': {'id': '8801', 'body': 'Repeated event'}})
        self.Task.create_comment({'issue': {'key': 'NOPE-1'},
                                  'comment': {'id': '8803', 'body': 'Unknown issue'}})
        self.assertEqual(self.env['mail.message'].search_count([]), count)

        self.Task.webhook_data_handle({'comment': {'id': '8801'}}, 'comment_deleted')
        self.assertFalse(message.exists())

    def test_user_webhooks(self):
        self.Task.webhook_data_handle({'user': {
            'accountId': 'webhook-user-1', 'displayName': 'Webhook User'}}, 'user_created')
        user = self.env['res.users'].search([('jira_user_key', '=', 'webhook-user-1')])
        self.assertEqual(user.login, 'Webhook User')

        existing = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Mapped', 'login': 'mapped@example.com'})
        self.Task.create_user({'user': {'accountId': 'webhook-user-2', 'displayName': 'Mapped',
                                        'emailAddress': 'mapped@example.com'}})
        self.assertEqual(existing.jira_user_key, 'webhook-user-2')
        self.Task.create_user({'user': {'accountId': 'bot', 'displayName': 'Bot',
                                        'accountType': 'app'}})
        self.assertFalse(self.env['res.users'].search([('jira_user_key', '=', 'bot')]))

        self.Task.webhook_data_handle({'user': {'accountId': 'webhook-user-1'}}, 'user_deleted')
        self.Task.delete_user({'accountId': 'webhook-user-2'})
        self.assertFalse(user.active)
        self.assertFalse(existing.active)

    def test_board_configuration_change(self):
        other = self.env['project.project'].create({'name': 'Other Project'})
        shared = self.env['project.task.type'].create({
            'name': 'In Progress', 'stages_jira_id': '3', 'project_ids': [(4, other.id)]})
        local = self.env['project.task.type'].create({
            'name': 'Odoo Only', 'project_ids': [(4, self.project.id)]})
        self.Task.webhook_data_handle({'configuration': {
            'id': 9001,
            'location': {'key': 'JTP'},
            'columnConfig': {'columns': [
                {'name': 'Backlog', 'statuses': [{'id': '10000'}]},
                {'name': 'To Do', 'statuses': [{'id': '10001'}]},
                {'name': 'In Progress', 'statuses': [{'id': '3'}]},
            ]},
        }}, 'board_configuration_changed')
        to_do = self.env['project.task.type'].search([('stages_jira_id', '=', '10001')])
        self.assertEqual(to_do.project_ids, self.project)
        self.assertEqual(shared.project_ids, other | self.project)
        self.assertEqual((to_do.sequence, shared.sequence), (1, 2))
        self.assertEqual(self.project.board_id_jira, 9001)

        # Column removed, board found through its id.
        self.Task.board_configuration_change({'configuration': {
            'id': 9001,
            'columnConfig': {'columns': [{'name': 'In Progress', 'statuses': [{'id': '3'}]}]},
        }})
        self.assertNotIn(self.project, to_do.project_ids)
        self.assertEqual(shared.project_ids, other | self.project)
        self.assertIn(self.project, local.project_ids)

        self.Task.board_configuration_change({'configuration': {
            'id': 404, 'columnConfig': {'columns': []}}})

    def test_update_task_fields(self):
        stage = self.env['project.task.type'].create({
            'name': 'QA', 'stages_jira_id': '5', 'project_ids': [(4, self.project.id)]})
        self.Task.webhook_data_handle(self.issue_event('JTP-1', [
            {'field': 'resolution', 'to': '10000'},
            {'field': 'status', 'to': '5'},
            {'field': 'summary', 'toString': 'Updated summary'},
            {'field': 'description', 'toString': 'Updated description'},
        ]), 'jira:issue_updated')
        self.assertEqual(self.task.stage_id, stage)
        self.assertEqual(self.task.name, 'Updated summary')
        self.assertEqual(html2plaintext(self.task.description), 'Updated description')

        self.Task.update_task(self.issue_event('JTP-1', [{'field': 'status', 'to': '404'}]))
        self.assertEqual(self.task.stage_id, stage)
        self.Task.update_task(self.issue_event('NOPE-1', [{'field': 'summary', 'toString': 'X'}]))

    def test_update_task_attachment(self):
        attachment_item = {'id': '9901', 'filename': 'file.txt', 'mimeType': 'text/plain',
                           'content': JIRA_URL + '/secure/attachment/9901/file.txt'}
        with self.mock_jira({('GET', '/secure/attachment/9901/file.txt'):
                             MockResponse({}, content=b'attachment-data')}):
            event = self.issue_event('JTP-1', [{'field': 'Attachment', 'to': '9901'}],
                                     attachment=[attachment_item])
            self.Task.update_task(event)
            self.Task.update_task(event)
        attachment = self.env['ir.attachment'].search([('attachment_id_jira', '=', 9901)])
        self.assertEqual(len(attachment), 1)
        self.assertEqual(attachment.raw, b'attachment-data')
        self.assertEqual(attachment.res_id, self.task.id)

        exported = self.env['ir.attachment'].create({
            'name': 'exported.pdf', 'raw': b'pdf', 'res_model': 'project.task',
            'res_id': self.task.id})
        with self.mock_jira({('GET', '/rest/api/2/issue/JTP-1'): {'fields': {'attachment': [
                {'id': '9902', 'filename': 'exported.pdf', 'content': JIRA_URL + '/x'}]}}}):
            self.Task.update_task(self.issue_event(
                'JTP-1', [{'field': 'Attachment', 'to': '9902'}]))
        self.assertEqual(exported.attachment_id_jira, 9902)

        forged = dict(attachment_item, id='9903', content='https://attacker.example.com/f')
        with self.mock_jira() as jira, self.assertLogs(LOGGER, 'ERROR'):
            self.Task.update_task(self.issue_event(
                'JTP-1', [{'field': 'Attachment', 'to': '9903'}], attachment=[forged]))
        self.assertFalse(jira.calls)
        self.assertFalse(self.env['ir.attachment'].search([('attachment_id_jira', '=', 9903)]))

    def test_update_task_sprint(self):
        other_task = self.Task.create({'name': 'Other Task', 'project_id': self.project.id})
        sprint_field = [{'id': 6100, 'name': 'Old Sprint', 'state': 'closed'},
                        {'id': 6101, 'name': 'Sprint Webhook', 'state': 'active', 'goal': 'Ship'}]
        self.Task.update_task(self.issue_event(
            'JTP-1', [{'field': 'Sprint', 'to': '6101'}], customfield_10020=sprint_field))
        sprint = self.env['jira.sprint'].search([('sprint_id_jira', '=', 6101)])
        self.assertEqual(sprint.state, 'ongoing')
        self.assertEqual(sprint.project_id, self.project)
        self.assertEqual(self.task.sprint_id, sprint)
        self.assertFalse(other_task.sprint_id)

        self.Task.update_task(self.issue_event(
            'JTP-2', [{'field': 'Sprint', 'to': '6101'}], customfield_10020=sprint_field,
            summary='Created By Sprint'))
        created = self.Task.search([('task_id_jira', '=', 'JTP-2')])
        self.assertEqual((created.name, created.sprint_id), ('Created By Sprint', sprint))
        self.assertEqual(self.env['jira.sprint'].search_count([('sprint_id_jira', '=', 6101)]), 1)

        self.Task.update_task(self.issue_event(
            'JTP-1', [{'field': 'Sprint', 'to': ''}], customfield_10020=None))
        self.assertFalse(self.task.sprint_id)

    def test_attachment_and_sprint_lifecycle_webhooks(self):
        attachment = self.env['ir.attachment'].create({
            'name': 'delete.txt', 'raw': b'data', 'attachment_id_jira': 7701})
        self.Task.webhook_data_handle({'attachment': {'id': 7701}}, 'attachment_deleted')
        self.assertFalse(attachment.exists())

        sprint = self.env['jira.sprint'].create({
            'name': 'Lifecycle Sprint', 'sprint_id_jira': 6201, 'project_id': self.project.id})
        self.task.sprint_id = sprint
        self.Task.webhook_data_handle({'sprint': {
            'id': 6201, 'startDate': '2026-01-01T10:00:00.000Z',
            'endDate': '2026-01-15T10:00:00.000+0530', 'goal': 'Ship'}}, 'sprint_started')
        self.assertEqual(sprint.state, 'ongoing')
        self.assertEqual(sprint.sprint_goal, 'Ship')
        self.assertEqual(sprint.start_date, datetime(2026, 1, 1, 10, 0))
        self.assertEqual(sprint.end_date, datetime(2026, 1, 15, 4, 30))

        self.Task.webhook_data_handle({'sprint': {'id': 6201}}, 'sprint_closed')
        self.assertEqual(sprint.state, 'completed')
        self.assertTrue(self.task.exists())
