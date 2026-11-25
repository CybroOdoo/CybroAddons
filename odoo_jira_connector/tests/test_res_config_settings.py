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
from odoo.exceptions import UserError, ValidationError
from odoo.fields import Command

from .common import JIRA_URL, LOGGER, JiraTestCommon, MockResponse, adf


def jira_projects(*projects):
    """Answer of GET /rest/api/2/project."""
    return [{'id': str(pid), 'key': key, 'name': name} for pid, key, name in projects]


class TestResConfigSettings(JiraTestCommon):

    def new_project_route(self):
        """POST /rest/simplified/latest/project answering 200 with new ids,
        as Jira Cloud does."""
        counter = iter(range(5000, 6000))

        def create(json, **kwargs):
            return {'projectId': next(counter), 'projectKey': json['key']}
        return create

    def new_issue_route(self):
        """POST /rest/api/2/issue answering new issue keys, numbered per
        project like Jira does."""
        counters = {}

        def create(json, **kwargs):
            key = json['fields']['project']['key']
            counters[key] = counters.get(key, 0) + 1
            return {'key': f"{key}-{counters[key]}"}
        return create

    def test_action_test_connection_requires_credentials(self):
        settings = self.env['res.config.settings'].create({
            'url': False, 'user_id_jira': False, 'api_token': False})
        with self.assertRaises(UserError):
            settings.action_test_connection()
        with self.assertRaises(UserError):
            settings.action_export_to_jira()

    def test_action_test_connection_success_sets_connection_parameter(self):
        with self.mock_jira({('GET', '/rest/api/2/project'): []}):
            action = self.settings().action_test_connection()
        self.assertEqual(action['params']['type'], 'success')
        self.assertEqual(self.Param.get_param('odoo_jira_connector.connection'), 'True')

    def test_action_test_connection_failure(self):
        with self.mock_jira({('GET', '/rest/api/2/project'): MockResponse({}, 401)}), \
                self.assertLogs(LOGGER, 'ERROR'):
            action = self.settings().action_test_connection()
        self.assertEqual(action['params']['type'], 'danger')
        self.assertFalse(self.Param.get_param('odoo_jira_connector.connection'))

    def test_export_creates_missing_project_with_tasks_comments_attachments(self):
        project = self.env['project.project'].create({'name': 'Export Missing Project'})
        task = self.env['project.task'].create({
            'name': 'Export Missing Task', 'project_id': project.id,
            'description': '<p>Plain <b>description</b></p>'})
        message = task.message_post(body='Exported comment', message_type='comment')
        attachment = self.env['ir.attachment'].create({
            'name': 'spec.pdf', 'raw': b'%PDF', 'mimetype': 'application/pdf',
            'res_model': 'project.task', 'res_id': task.id})
        with self.mock_jira({
            ('GET', '/rest/api/2/project'): jira_projects((1001, 'JTP', 'Jira Test Project')),
            ('POST', '/rest/simplified/latest/project'): self.new_project_route(),
            ('POST', '/rest/api/2/issue'): self.new_issue_route(),
            ('POST', '/rest/api/3/issue/EXP1ECT-1/comment'): {'id': '9001'},
            ('POST', '/rest/api/3/issue/EXP1ECT-1/attachments'): [{'id': '7001'}],
        }) as jira:
            action = self.settings().action_export_to_jira()

        self.assertTrue(project.project_id_jira)
        self.assertEqual(project.jira_project_key, 'EXP1ECT')
        self.assertEqual(task.task_id_jira, 'EXP1ECT-1')
        self.assertEqual(message.message_id_jira, 9001)
        self.assertEqual(attachment.attachment_id_jira, 7001)
        issue = next(call['json'] for call in jira.requests_to('POST', '/rest/api/2/issue')
                     if call['json']['fields']['summary'] == 'Export Missing Task')
        self.assertEqual(issue['fields']['description'].strip(), 'Plain *description*')
        self.assertEqual(action['params']['type'], 'success')
        self.assertIn('task(s) exported', action['params']['message'])

    def test_export_existing_project_only_pushes_what_jira_lacks(self):
        same_name = self.env['project.project'].create({'name': 'Same Name'})
        new_task = self.env['project.task'].create({
            'name': 'Second Task', 'project_id': self.project.id})
        self.task.message_post(body='Already in Jira', message_type='comment')
        new_message = self.task.message_post(body='Only in Odoo', message_type='comment')
        in_jira = self.env['ir.attachment'].create({
            'name': 'a.pdf', 'raw': b'a', 'res_model': 'project.task', 'res_id': self.task.id})
        not_in_jira = self.env['ir.attachment'].create({
            'name': 'b.pdf', 'raw': b'b', 'res_model': 'project.task', 'res_id': self.task.id})
        with self.mock_jira({
            ('GET', '/rest/api/2/project'): jira_projects(
                (1001, 'JTP', 'Jira Test Project'), (2002, 'SAM', 'Same Name')),
            ('GET', '/rest/api/3/search/jql'): {'issues': [{'key': 'JTP-1'}], 'isLast': True},
            ('POST', '/rest/api/2/issue'): {'key': 'JTP-2'},
            ('GET', '/rest/api/3/issue/JTP-1/comment'): {
                'comments': [{'id': '1', 'body': adf('Already in Jira')}]},
            ('POST', '/rest/api/3/issue/JTP-1/comment'): {'id': '77'},
            ('GET', '/rest/api/2/issue/JTP-1'): {
                'fields': {'attachment': [{'id': '55', 'filename': 'a.pdf'}]}},
            ('POST', '/rest/api/3/issue/JTP-1/attachments'): [{'id': '56'}],
            ('POST', '/rest/simplified/latest/project'): self.new_project_route(),
        }) as jira:
            self.settings().action_export_to_jira()

        self.assertEqual(same_name.project_id_jira, 2002)
        self.assertEqual(same_name.jira_project_key, 'SAM')
        self.assertEqual(self.task.task_id_jira, 'JTP-1')
        self.assertEqual(new_task.task_id_jira, 'JTP-2')
        summaries = [call['json']['fields']['summary']
                     for call in jira.requests_to('POST', '/rest/api/2/issue')]
        self.assertNotIn('Jira Test Task', summaries)
        posted = jira.requests_to('POST', '/rest/api/3/issue/JTP-1/comment')
        self.assertEqual([call['json'] for call in posted], [{'body': adf('Only in Odoo')}])
        self.assertEqual(new_message.message_id_jira, 77)
        self.assertEqual(in_jira.attachment_id_jira, 55)
        self.assertEqual(not_in_jira.attachment_id_jira, 56)

    def test_export_reports_jira_errors(self):
        project = self.env['project.project'].create({'name': 'Duplicate Name'})
        with self.mock_jira({
            ('GET', '/rest/api/2/project'): jira_projects((1001, 'JTP', 'Jira Test Project')),
            ('POST', '/rest/simplified/latest/project'): MockResponse(
                {'errors': {'projectName': 'A project with that name already exists.'}}, 400),
            ('POST', '/rest/api/2/issue'): MockResponse({'errors': {}}, 400),
            ('GET', '/rest/api/3/search/jql'): {'issues': [], 'isLast': True},
        }), self.assertLogs(LOGGER, 'ERROR'):
            action = self.settings().action_export_to_jira()
        self.assertFalse(project.project_id_jira)
        self.assertIn('A project with that name already exists.', action['params']['message'])
        self.assertEqual(action['params']['type'], 'danger')
        self.assertTrue(action['params']['sticky'])

    def test_export_stops_when_jira_projects_cannot_be_read(self):
        with self.mock_jira({('GET', '/rest/api/2/project'): MockResponse({}, 500)}) as jira, \
                self.assertLogs(LOGGER, 'ERROR'):
            action = self.settings().action_export_to_jira()
        self.assertEqual(action['params']['type'], 'danger')
        self.assertFalse(jira.requests_to('POST'))

    def test_export_counts_failed_issue_search(self):
        with self.mock_jira({
            ('GET', '/rest/api/2/project'): jira_projects((1001, 'JTP', 'Jira Test Project')),
            ('GET', '/rest/api/3/search/jql'): MockResponse({}, 500),
            ('POST', '/rest/simplified/latest/project'): self.new_project_route(),
        }) as jira, self.assertLogs(LOGGER, 'ERROR'):
            action = self.settings().action_export_to_jira()
        self.assertIn('failed', action['params']['message'])
        self.assertFalse(jira.requests_to('POST', '/rest/api/2/issue'))

    def test_export_counts_failed_comment_export(self):
        self.task.message_post(body='Will fail', message_type='comment')
        with self.mock_jira({
            ('GET', '/rest/api/2/project'): jira_projects((1001, 'JTP', 'Jira Test Project')),
            ('GET', '/rest/api/3/search/jql'): {'issues': [{'key': 'JTP-1'}]},
            ('GET', '/rest/api/3/issue/JTP-1/comment'): MockResponse({}, 403),
            ('POST', '/rest/simplified/latest/project'): self.new_project_route(),
        }), self.assertLogs(LOGGER, 'ERROR'):
            action = self.settings().action_export_to_jira()
        self.assertIn('failed', action['params']['message'])

    def import_routes(self):
        return {
            ('GET', '/rest/api/2/project'): jira_projects((3003, 'IMP', 'Imported Project')),
            ('GET', '/rest/api/3/search/jql'): {
                'issues': [{'key': 'IMP-1', 'fields': {'summary': 'Imported Task'}}],
                'isLast': True},
            ('GET', '/rest/api/3/issue/IMP-1/comment'): {
                'comments': [{'id': '801', 'body': adf('Hello from Jira')}]},
            ('GET', '/rest/api/2/issue/IMP-1'): {'fields': {'attachment': [{
                'id': '901', 'filename': 'spec.pdf', 'mimeType': 'application/pdf',
                'content': JIRA_URL + '/rest/api/3/attachment/content/901'}]}},
            ('GET', '/rest/api/3/attachment/content/901'): MockResponse({}, content=b'%PDF'),
        }

    def test_import_creates_projects_tasks_comments_attachments_once(self):
        self.set_jira_config(automatic=True)
        with self.mock_jira(self.import_routes()) as jira:
            action = self.settings().action_import_from_jira()
            again = self.settings().action_import_from_jira()

        project = self.env['project.project'].search([('project_id_jira', '=', 3003)])
        task = self.env['project.task'].search([('task_id_jira', '=', 'IMP-1')])
        self.assertEqual(len(project), 1)
        self.assertEqual(task.project_id, project)
        self.assertEqual(task.name, 'Imported Task')
        message = self.env['mail.message'].search([('message_id_jira', '=', 801)])
        self.assertEqual(len(message), 1)
        self.assertIn('Hello from Jira', message.body)
        attachment = self.env['ir.attachment'].search([('attachment_id_jira', '=', 901)])
        self.assertEqual(attachment.raw, b'%PDF')
        self.assertEqual(attachment.res_id, task.id)
        # Nothing imported from Jira is pushed back to Jira.
        self.assertFalse(jira.requests_to('POST'))
        self.assertEqual(action['params']['type'], 'success')
        self.assertIn('1 project(s) imported', action['params']['message'])
        self.assertIn('0 project(s) imported', again['params']['message'])

    def test_import_links_same_named_project(self):
        project = self.env['project.project'].create({'name': 'Imported Project'})
        with self.mock_jira(self.import_routes()):
            self.settings().action_import_from_jira()
        self.assertEqual(project.project_id_jira, 3003)
        self.assertEqual(project.jira_project_key, 'IMP')
        self.assertEqual(self.env['project.project'].search_count(
            [('name', '=', 'Imported Project')]), 1)

    def test_import_links_same_named_attachment(self):
        task = self.env['project.task'].create({
            'name': 'Imported Task', 'project_id': self.project.id, 'task_id_jira': 'IMP-1'})
        self.project.write({'project_id_jira': 3003, 'jira_project_key': 'IMP'})
        attachment = self.env['ir.attachment'].create({
            'name': 'spec.pdf', 'raw': b'%PDF', 'res_model': 'project.task', 'res_id': task.id})
        with self.mock_jira(self.import_routes()) as jira:
            self.settings().action_import_from_jira()
        self.assertEqual(attachment.attachment_id_jira, 901)
        self.assertFalse(jira.requests_to('GET', '/rest/api/3/attachment/content/901'))

    def test_import_failures(self):
        with self.mock_jira({('GET', '/rest/api/2/project'): MockResponse({}, 500)}), \
                self.assertLogs(LOGGER, 'ERROR'):
            action = self.settings().action_import_from_jira()
        self.assertEqual(action['params']['type'], 'danger')

        routes = self.import_routes()
        routes[('GET', '/rest/api/3/search/jql')] = MockResponse({}, 500)
        with self.mock_jira(routes), self.assertLogs(LOGGER, 'ERROR'):
            action = self.settings().action_import_from_jira()
        self.assertEqual(action['params']['type'], 'warning')

        routes = self.import_routes()
        routes[('GET', '/rest/api/3/issue/IMP-1/comment')] = MockResponse({}, 500)
        with self.mock_jira(routes), self.assertLogs(LOGGER, 'ERROR'):
            action = self.settings().action_import_from_jira()
        self.assertIn('failed', action['params']['message'])

    def test_action_export_users(self):
        Users = self.env['res.users'].with_context(no_reset_password=True)
        user = Users.create({'name': 'Export User', 'login': 'export.user@example.com'})
        not_email = Users.create({'name': 'No Email', 'login': 'no-email-login'})
        portal = Users.create({
            'name': 'Portal User', 'login': 'portal.user@example.com',
            'group_ids': [Command.set([self.env.ref('base.group_portal').id])]})
        with self.mock_jira({
            ('GET', '/rest/api/2/users/search'): [],
            ('POST', '/rest/api/3/user'): lambda json, **kw: {'accountId': 'acc-' + json['emailAddress']},
        }) as jira:
            action = self.settings().action_export_users()
        self.assertEqual(user.jira_user_key, 'acc-export.user@example.com')
        self.assertFalse(not_email.jira_user_key)
        self.assertFalse(portal.jira_user_key)
        self.assertEqual(jira.requests_to('POST')[0]['json']['products'], ['jira-software'])
        self.assertEqual(action['params']['type'], 'success')

    def test_action_export_users_failures(self):
        with self.mock_jira({('GET', '/rest/api/2/users/search'): MockResponse({}, 500)}), \
                self.assertLogs(LOGGER, 'ERROR'):
            action = self.settings().action_export_users()
        self.assertEqual(action['params']['type'], 'danger')

        self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Refused User', 'login': 'refused.user@example.com'})
        with self.mock_jira({
            ('GET', '/rest/api/2/users/search'): [],
            ('POST', '/rest/api/3/user'): MockResponse({'errorMessages': ['No licence']}, 400),
        }), self.assertLogs(LOGGER, 'ERROR'):
            action = self.settings().action_export_users()
        self.assertIn('failed to export', action['params']['message'])

    def test_action_import_users(self):
        existing = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Existing User', 'login': 'existing.user@example.com'})

        def users(params, **kwargs):
            if params['startAt']:
                return []
            return [
                {'accountId': 'new-1', 'displayName': 'New Jira User',
                 'emailAddress': 'new.jira.user@example.com', 'accountType': 'atlassian'},
                {'accountId': 'map-1', 'displayName': 'Existing User',
                 'emailAddress': 'existing.user@example.com', 'accountType': 'atlassian'},
                {'accountId': 'bot-1', 'displayName': 'Jira Automation', 'accountType': 'app'},
            ]

        with self.mock_jira({('GET', '/rest/api/2/users/search'): users}):
            action = self.settings().action_import_users()
            again = self.settings().action_import_users()
        new_user = self.env['res.users'].search([('jira_user_key', '=', 'new-1')])
        self.assertEqual(new_user.login, 'new.jira.user@example.com')
        self.assertEqual(existing.jira_user_key, 'map-1')
        self.assertFalse(self.env['res.users'].search([('jira_user_key', '=', 'bot-1')]))
        self.assertIn('1 user(s) imported', action['params']['message'])
        self.assertIn('no new users', again['params']['message'])

    def test_action_import_users_failure(self):
        with self.mock_jira({('GET', '/rest/api/2/users/search'): MockResponse({}, 500)}), \
                self.assertLogs(LOGGER, 'ERROR'):
            action = self.settings().action_import_users()
        self.assertEqual(action['params']['type'], 'danger')

    def test_automatic_requires_webhook_secret(self):
        with self.assertRaises(ValidationError):
            self.env['res.config.settings'].create({
                'automatic': True,
                'webhook_secret': False,
            })
        settings = self.env['res.config.settings'].create({
            'automatic': False,
            'webhook_secret': False,
        })
        with self.assertRaises(ValidationError):
            settings.write({'automatic': True})
