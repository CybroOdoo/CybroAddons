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
import logging
from datetime import datetime, timezone

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.fields import Command
from odoo.tools import html2plaintext, plaintext2html

from .jira_client import JIRA_ERRORS, JiraClient, adf_to_text

_logger = logging.getLogger(__name__)

# Jira webhook event -> method of project.task applying it in Odoo.
WEBHOOK_HANDLERS = {
    'project_created': 'create_project',
    'project_updated': 'update_project',
    'project_soft_deleted': 'delete_project',
    'jira:issue_created': 'create_task',
    'jira:issue_updated': 'update_task',
    'jira:issue_deleted': 'delete_task',
    'comment_created': 'create_comment',
    'comment_deleted': 'delete_comment',
    'user_created': 'create_user',
    'user_deleted': 'delete_user',
    'board_configuration_changed': 'board_configuration_change',
    'attachment_deleted': 'delete_attachment',
    'sprint_started': 'sprint_started',
    'sprint_closed': 'sprint_closed',
}
SPRINT_STATES = {'future': 'to_start', 'active': 'ongoing', 'closed': 'completed'}


def jira_datetime(value):
    """Convert a Jira timestamp such as 2026-01-15T10:00:00.000Z to a naive
    UTC datetime for a Datetime field."""
    if not value:
        return False
    moment = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%f%z')
    return moment.astimezone(timezone.utc).replace(tzinfo=None)


class ProjectTask(models.Model):
    """Extends project.task to integrate with Jira tasks."""
    _inherit = 'project.task'

    task_id_jira = fields.Char(string='Jira Task ID', readonly=True,
                               help='Key of the matching issue in Jira, e.g. PRJ-12.')
    sprint_id = fields.Many2one('jira.sprint', readonly=True,
                                help='Jira sprint of this task.')
    task_sprint_active = fields.Boolean(string='Active Sprint',
                                        compute='_compute_task_sprint_active',
                                        help='Whether the project of this task '
                                             'uses Jira sprints.')

    @api.depends('project_id.sprint_active')
    def _compute_task_sprint_active(self):
        """Tasks show their sprint when their project uses sprints."""
        for task in self:
            task.task_sprint_active = task.project_id.sprint_active

    @api.model_create_multi
    def create(self, vals_list):
        """Create tasks and, in Automatic mode, create their Jira issues."""
        tasks = super().create(vals_list)
        client = JiraClient.for_automatic_sync(self.env)
        if client:
            for task in tasks.filtered(lambda t: not t.task_id_jira and not t.is_template
                                       and t.project_id.jira_project_key):
                try:
                    task.task_id_jira = client.create_issue(
                        task.project_id.jira_project_key, task.name,
                        html2plaintext(task.description or ''))
                except (*JIRA_ERRORS, KeyError) as error:
                    _logger.error("Failed to create a Jira issue for task %s: %s",
                                  task.name, error)
        return tasks

    def write(self, vals):
        """Update tasks and, in Automatic mode, rename their Jira issues."""
        client = vals.get('name') and JiraClient.for_automatic_sync(self.env)
        if client:
            for task in self.filtered(
                    lambda t: t.task_id_jira and t.name != vals['name']):
                try:
                    client.put(f'/rest/api/2/issue/{task.task_id_jira}',
                               {'fields': {'summary': vals['name']}})
                except JIRA_ERRORS as error:
                    _logger.error("Failed to rename Jira issue %s: %s",
                                  task.task_id_jira, error)
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_except_synced_in_folded_stage(self):
        """In Automatic mode, deleting a task also deletes its Jira issue, so
        synced tasks in a folded (closed) stage are protected."""
        if JiraClient.for_automatic_sync(self.env) and any(
                task.task_id_jira and task.stage_id.fold for task in self):
            raise UserError(self.env._(
                "You cannot delete a task in a folded stage."))

    def unlink(self):
        """Delete tasks and, in Automatic mode, their Jira issues."""
        client = JiraClient.for_automatic_sync(self.env)
        issue_keys = self.filtered('task_id_jira').mapped('task_id_jira') if client else []
        result = super().unlink()
        for issue_key in issue_keys:
            try:
                client.delete(f'/rest/api/2/issue/{issue_key}')
            except JIRA_ERRORS as error:
                _logger.error("Failed to delete Jira issue %s: %s", issue_key, error)
        return result

    def webhook_data_handle(self, jira_data, webhook_event):
        """Apply a Jira webhook event. Changes made here are not pushed back
        to Jira."""
        handler = WEBHOOK_HANDLERS.get(webhook_event)
        if handler:
            getattr(self.with_context(jira_skip_sync=True), handler)(jira_data)

    def create_project(self, jira_data):
        """Create (or link) the Odoo project of a new Jira project."""
        jira_project = jira_data['project']
        jira_id = int(jira_project['id'])
        Project = self.env['project.project'].sudo()
        if Project.search_count([('project_id_jira', '=', jira_id)]):
            return
        # A project exported from Odoo is linked instead of duplicated.
        project = Project.search([
            ('name', '=', jira_project['name']), ('is_template', '=', False),
        ]).filtered(lambda p: not p.project_id_jira)[:1]
        values = {'project_id_jira': jira_id, 'jira_project_key': jira_project['key']}
        if project:
            project.write(values)
        else:
            project = Project.create(dict(values, name=jira_project['name']))
        project.sprint_active = self._jira_project_uses_sprints(jira_project['key'])

    def _jira_project_uses_sprints(self, project_key):
        """Team-managed (next-gen) Jira projects get the Sprint button."""
        client = JiraClient.from_settings(self.env)
        if not client:
            return False
        try:
            return client.get(f'/rest/api/2/project/{project_key}').get('style') != 'classic'
        except JIRA_ERRORS as error:
            _logger.error("Failed to read Jira project %s: %s", project_key, error)
            return False

    def update_project(self, jira_data):
        """Rename the Odoo project of a renamed Jira project."""
        name = jira_data['project']['name']
        self.env['project.project'].sudo().search([
            ('project_id_jira', '=', int(jira_data['project']['id'])),
        ]).filtered(lambda p: p.name != name).write({'name': name})

    def delete_project(self, jira_data):
        """Delete the Odoo project of a deleted Jira project."""
        self.env['project.project'].sudo().search([
            ('project_id_jira', '=', int(jira_data['project']['id'])),
        ]).unlink()

    def create_task(self, jira_data):
        """Create (or link) the Odoo task of a new Jira issue."""
        issue = jira_data['issue']
        Task = self.env['project.task'].sudo()
        if Task.search_count([('task_id_jira', '=', issue['key'])]):
            return
        project = self.env['project.project'].sudo().search([
            ('project_id_jira', '=', int(issue['fields']['project']['id'])),
        ], limit=1)
        if not project:
            return
        name = issue['fields']['summary']
        # A task exported from Odoo is linked instead of duplicated.
        task = Task.search([('project_id', '=', project.id), ('name', '=', name),
                            ('task_id_jira', '=', False)], limit=1)
        if task:
            task.task_id_jira = issue['key']
        else:
            Task.create({'project_id': project.id, 'name': name,
                         'task_id_jira': issue['key']})

    def delete_task(self, jira_data):
        """Delete the Odoo task of a deleted Jira issue."""
        self.env['project.task'].sudo().search([
            ('task_id_jira', '=', jira_data['issue']['key']),
        ]).unlink()

    def create_comment(self, jira_data):
        """Post a new Jira comment in the chatter of its task."""
        comment = jira_data['comment']
        comment_id = int(comment['id'])
        Message = self.env['mail.message'].sudo()
        task = self.env['project.task'].sudo().search([
            ('task_id_jira', '=', jira_data['issue']['key']),
        ], limit=1)
        if not task or Message.search_count([('message_id_jira', '=', comment_id)]):
            return
        text = adf_to_text(comment.get('body'))
        # A comment exported from Odoo is linked instead of duplicated.
        message = Message.search([
            ('model', '=', 'project.task'), ('res_id', '=', task.id),
            ('message_type', '=', 'comment'),
        ]).filtered(lambda m: not m.message_id_jira
                    and html2plaintext(m.body or '').strip() == text)[:1]
        if not message:
            message = task.with_context(mail_create_nosubscribe=True).message_post(
                body=text, message_type='comment', subtype_xmlid='mail.mt_note')
        message.message_id_jira = comment_id

    def delete_comment(self, jira_data):
        """Delete the Odoo message of a deleted Jira comment."""
        self.env['mail.message'].sudo().search([
            ('message_id_jira', '=', int(jira_data['comment']['id'])),
        ]).unlink()

    def create_user(self, jira_data):
        """Create (or link) the Odoo user of a new Jira account."""
        account = jira_data['user']
        Users = self.env['res.users'].sudo().with_context(active_test=False)
        if account.get('accountType', 'atlassian') != 'atlassian' or \
                Users.search_count([('jira_user_key', '=', account['accountId'])]):
            return
        login = account.get('emailAddress') or account['displayName']
        user = Users.search([('login', '=', login)], limit=1)
        if user:
            user.jira_user_key = account['accountId']
        else:
            Users.create({'login': login, 'name': account['displayName'],
                          'jira_user_key': account['accountId']})

    def delete_user(self, jira_data):
        """Archive the Odoo user of a deleted Jira account. Users are not
        deleted because Odoo records keep referring to them."""
        account_id = (jira_data.get('user') or {}).get('accountId') \
            or jira_data.get('accountId')
        if account_id:
            self.env['res.users'].sudo().search([
                ('jira_user_key', '=', account_id),
            ]).action_archive()

    def board_configuration_change(self, jira_data):
        """Keep the project stages in line with the columns of its Jira board."""
        configuration = jira_data['configuration']
        location_key = (configuration.get('location') or {}).get('key')
        Project = self.env['project.project'].sudo()
        if location_key:
            project = Project.search([('jira_project_key', '=', location_key)], limit=1)
        else:
            project = Project.search([('board_id_jira', '=', configuration['id'])], limit=1)
        if not project:
            return
        Stage = self.env['project.task.type'].sudo()
        columns = [column for column in configuration['columnConfig']['columns']
                   if column['name'] != 'Backlog' and column.get('statuses')]
        status_ids = []
        for sequence, column in enumerate(columns, start=1):
            status_id = str(column['statuses'][0]['id'])
            status_ids.append(status_id)
            stage = Stage.search([('stages_jira_id', '=', status_id)], limit=1)
            if stage:
                stage.write({'project_ids': [Command.link(project.id)],
                             'sequence': sequence})
            else:
                Stage.create({
                    'name': column['name'],
                    'stages_jira_id': status_id,
                    'jira_project_key': project.jira_project_key,
                    'project_ids': [Command.link(project.id)],
                    'sequence': sequence,
                })
        # Columns removed from the board: detach their stages from the project.
        Stage.search([
            ('project_ids', 'in', project.ids), ('stages_jira_id', '!=', False),
            ('stages_jira_id', 'not in', status_ids),
        ]).write({'project_ids': [Command.unlink(project.id)]})
        if location_key:
            project.board_id_jira = configuration['id']

    def update_task(self, jira_data):
        """Apply the changes of an updated Jira issue to its Odoo task."""
        issue = jira_data['issue']
        task = self.env['project.task'].sudo().search(
            [('task_id_jira', '=', issue['key'])], limit=1)
        for item in (jira_data.get('changelog') or {}).get('items') or []:
            field = item.get('field')
            if field == 'Sprint':
                self._jira_update_sprint(task, issue)
            elif not task:
                continue
            elif field == 'status':
                stage = self.env['project.task.type'].sudo().search(
                    [('stages_jira_id', '=', item.get('to'))], limit=1)
                if stage:
                    task.stage_id = stage
            elif field == 'summary' and item.get('toString'):
                if task.name != item['toString']:
                    task.name = item['toString']
            elif field == 'description':
                task.description = plaintext2html(item.get('toString') or '')
            elif field == 'Attachment' and item.get('to'):
                self._jira_import_attachment(task, issue, int(item['to']))

    def _jira_import_attachment(self, task, issue, jira_id):
        """Download the Jira attachment ``jira_id`` onto the issue's task."""
        Attachment = self.env['ir.attachment'].sudo()
        if Attachment.search_count([('attachment_id_jira', '=', jira_id)]):
            return
        client = JiraClient.from_settings(self.env)
        try:
            items = (issue.get('fields') or {}).get('attachment') \
                or (client.attachments(issue['key']) if client else [])
            item = next((item for item in items if int(item['id']) == jira_id), None)
            if not item:
                return
            # An attachment exported from Odoo is linked instead of duplicated.
            same_name = Attachment.search([
                ('res_model', '=', 'project.task'), ('res_id', '=', task.id),
                ('name', '=', item.get('filename')),
            ]).filtered(lambda a: not a.attachment_id_jira)[:1]
            if same_name:
                same_name.attachment_id_jira = jira_id
            elif client:
                Attachment.create({
                    'name': item.get('filename') or str(jira_id),
                    'raw': client.download(item['content']),
                    'mimetype': item.get('mimeType'),
                    'res_model': 'project.task',
                    'res_id': task.id,
                    'attachment_id_jira': jira_id,
                })
        except (*JIRA_ERRORS, KeyError) as error:
            _logger.error("Failed to import Jira attachment %s: %s", jira_id, error)

    def _jira_update_sprint(self, task, issue):
        """Put the issue's task in its latest Jira sprint (customfield_10020),
        creating the sprint, and the task if needed."""
        issue_fields = issue.get('fields') or {}
        sprints = issue_fields.get('customfield_10020') or []
        if not sprints:
            task.sprint_id = False
            return
        sprint_data = sprints[-1]
        project = task.project_id
        project_key = (issue_fields.get('project') or {}).get('key')
        if not project and project_key:
            project = self.env['project.project'].sudo().search(
                [('jira_project_key', '=', project_key)], limit=1)
        Sprint = self.env['jira.sprint'].sudo()
        sprint = Sprint.search([('sprint_id_jira', '=', sprint_data['id'])], limit=1)
        if not sprint:
            sprint = Sprint.create({
                'name': sprint_data.get('name'),
                'sprint_id_jira': sprint_data['id'],
                'project_id': project.id,
                'sprint_goal': sprint_data.get('goal'),
                'state': SPRINT_STATES.get(sprint_data.get('state'), 'to_start'),
            })
        if task:
            task.sprint_id = sprint
        elif project:
            self.env['project.task'].sudo().create({
                'project_id': project.id,
                'name': issue_fields.get('summary') or issue['key'],
                'task_id_jira': issue['key'],
                'sprint_id': sprint.id,
            })

    def delete_attachment(self, jira_data):
        """Delete the Odoo attachment of a deleted Jira attachment."""
        self.env['ir.attachment'].sudo().search([
            ('attachment_id_jira', '=', int(jira_data['attachment']['id'])),
        ]).unlink()

    def sprint_started(self, jira_data):
        """Copy the dates and goal of a started Jira sprint."""
        sprint_data = jira_data['sprint']
        self.env['jira.sprint'].sudo().search([
            ('sprint_id_jira', '=', sprint_data['id']),
        ]).write({
            'start_date': jira_datetime(sprint_data.get('startDate')),
            'end_date': jira_datetime(sprint_data.get('endDate')),
            'sprint_goal': sprint_data.get('goal'),
            'state': 'ongoing',
        })

    def sprint_closed(self, jira_data):
        """Mark a closed Jira sprint as completed. Its tasks stay in Odoo,
        as the issues stay in Jira."""
        self.env['jira.sprint'].sudo().search([
            ('sprint_id_jira', '=', jira_data['sprint']['id']),
        ]).write({'state': 'completed'})
