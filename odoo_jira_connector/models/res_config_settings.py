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
import re

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import html2plaintext

from .jira_client import (JIRA_ERRORS, JiraClient, JiraError, adf_to_text,
                          project_key_from_name)

_logger = logging.getLogger(__name__)
EMAIL_REGEX = re.compile(r'^\S+@\S+\.\S+$')


class ResConfigSettings(models.TransientModel):
    """Extend system settings with Jira integration configuration."""
    _inherit = 'res.config.settings'

    url = fields.Char(string='URL', config_parameter='odoo_jira_connector.url',
                      help='Your Jira site, e.g. https://yourname.atlassian.net/')
    user_id_jira = fields.Char(
        string='User Name', config_parameter='odoo_jira_connector.user_id_jira',
        help='Email address of the Atlassian account that owns the API token.')
    api_token = fields.Char(string='API Token',
                            config_parameter='odoo_jira_connector.api_token',
                            help='API token created in your Atlassian account.')
    connection = fields.Boolean(
        config_parameter='odoo_jira_connector.connection',
        help='Set once the connection to Jira has been tested successfully.')
    automatic = fields.Boolean(
        config_parameter='odoo_jira_connector.automatic',
        help='Push projects, tasks, comments, attachments and users created '
             'in Odoo to Jira, and apply the Jira webhook events in Odoo.')
    webhook_secret = fields.Char(
        config_parameter='odoo_jira_connector.webhook_secret',
        help='Secret entered on the Jira webhook. Required when Automatic is '
             'enabled to authenticate incoming webhook events.')

    @api.constrains('automatic', 'webhook_secret')
    def _check_webhook_secret(self):
        for record in self:
            if record.automatic and not (record.webhook_secret and record.webhook_secret.strip()):
                raise ValidationError(self.env._(
                    "A Webhook Secret is required when Automatic synchronization is enabled."))

    def set_values(self):
        if self.automatic and not (self.webhook_secret and self.webhook_secret.strip()):
            raise ValidationError(self.env._(
                "A Webhook Secret is required when Automatic synchronization is enabled."))
        super().set_values()

    def action_test_connection(self):
        """Check the credentials against Jira and remember a working connection."""
        self.ensure_one()
        if not (self.url and self.user_id_jira and self.api_token):
            raise UserError(self.env._(
                "Please provide the URL, User Name and API Token to test the "
                "Jira connection."))
        client = JiraClient(self.url, self.user_id_jira, self.api_token)
        try:
            client.get('/rest/api/2/project')
        except JIRA_ERRORS as error:
            _logger.error("Jira connection test failed: %s", error)
            return self._notification(self.env._(
                "Failed to connect to Jira. Please check the URL, user name "
                "and API token."), failures=1)
        self.env['ir.config_parameter'].sudo().set_param(
            'odoo_jira_connector.connection', True)
        return self._notification(
            self.env._("Test connection to Jira successful."))

    def action_export_to_jira(self):
        """Create the Odoo projects and tasks that are missing in Jira, then
        push the comments and attachments Jira does not have yet."""
        self.ensure_one()
        client = self._get_client()
        stats = {'projects': 0, 'tasks': 0, 'failures': 0, 'errors': []}
        try:
            jira_projects = [project for project in client.get('/rest/api/2/project')
                             if isinstance(project, dict)]
        except JIRA_ERRORS as error:
            _logger.error("Failed to fetch projects from Jira: %s", error)
            stats['failures'] += 1
            return self._sync_notification(stats, export=True)
        by_id = {int(project['id']): project for project in jira_projects
                 if str(project.get('id', '')).isdigit()}
        by_name = {project['name']: project for project in jira_projects
                   if project.get('name')}

        Project = self.env['project.project']
        # Odoo projects that already exist in Jira under the same name.
        for project in Project.search([('name', 'in', list(by_name)),
                                       ('is_template', '=', False)]).filtered(
                lambda p: not p.project_id_jira):
            jira_project = by_name[project.name]
            project.write({'project_id_jira': int(jira_project['id']),
                           'jira_project_key': jira_project.get('key')})

        for project in Project.search([('project_id_jira', 'in', list(by_id))]):
            key = by_id[project.project_id_jira].get('key') or project.jira_project_key
            if project.jira_project_key != key:
                project.jira_project_key = key
            self._export_project_tasks(client, project, stats)

        new_projects = Project.search([('project_id_jira', 'not in', list(by_id)),
                                       ('name', 'not in', list(by_name)),
                                       ('is_template', '=', False)])
        for project in new_projects:
            self._export_new_project(client, project, stats)
        return self._sync_notification(stats, export=True)

    def _export_new_project(self, client, project, stats):
        """Create one Odoo project in Jira, then its tasks."""
        project.lock_for_update(allow_referencing=True)
        try:
            data = client.create_project(project.name,
                                         project_key_from_name(project.name))
            project.write({'project_id_jira': int(data['projectId']),
                           'jira_project_key': data['projectKey']})
        except (*JIRA_ERRORS, KeyError) as error:
            _logger.error("Failed to create project %s in Jira: %s",
                          project.name, error)
            stats['failures'] += 1
            if isinstance(error, JiraError) and error.errors:
                stats['errors'].append(self.env._(
                    'Project "%(name)s": %(error)s', name=project.name,
                    error=' '.join(map(str, error.errors.values()))))
            return
        stats['projects'] += 1
        self._export_project_tasks(client, project, stats, new_project=True)

    def _export_project_tasks(self, client, project, stats, new_project=False):
        """Create the missing issues of a linked project and push the
        comments and attachments of all its tasks."""
        if new_project:
            jira_keys = set()
        else:
            try:
                jira_keys = {issue['key'] for issue in client.search_issues(
                    f'project = "{project.jira_project_key}"') if issue.get('key')}
            except JIRA_ERRORS as error:
                _logger.error("Failed to search the issues of project %s: %s",
                              project.jira_project_key, error)
                stats['failures'] += 1
                return
        tasks = self.env['project.task'].search([('project_id', '=', project.id),
                                                 ('is_template', '=', False)])
        tasks.lock_for_update(allow_referencing=True)
        for task in tasks:
            new_issue = task.task_id_jira not in jira_keys
            if new_issue:
                try:
                    task.task_id_jira = client.create_issue(
                        project.jira_project_key, task.name,
                        html2plaintext(task.description or ''))
                except (*JIRA_ERRORS, KeyError) as error:
                    _logger.error("Failed to create a Jira issue for task %s: %s",
                                  task.name, error)
                    stats['failures'] += 1
                    continue
                stats['tasks'] += 1
            try:
                self._export_task_comments(client, task, new_issue)
                self._export_task_attachments(client, task, new_issue)
            except (*JIRA_ERRORS, KeyError, IndexError) as error:
                _logger.error("Failed to export comments or attachments of "
                              "task %s: %s", task.task_id_jira, error)
                stats['failures'] += 1

    def _export_task_comments(self, client, task, new_issue):
        """Post the task's chatter comments that are not in Jira yet."""
        messages = self.env['mail.message'].search([
            ('model', '=', 'project.task'), ('res_id', '=', task.id),
            ('message_type', '=', 'comment'),
        ], order='id').filtered(lambda m: not m.message_id_jira)
        if not messages:
            return
        messages.lock_for_update(allow_referencing=True)
        existing = set() if new_issue else {
            adf_to_text(comment.get('body'))
            for comment in client.comments(task.task_id_jira)}
        for message in messages:
            text = html2plaintext(message.body or '').strip()
            if text and text not in existing:
                message.message_id_jira = client.add_comment(task.task_id_jira, text)
                existing.add(text)

    def _export_task_attachments(self, client, task, new_issue):
        """Upload the task's attachments that are not in Jira yet."""
        attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'project.task'), ('res_id', '=', task.id),
            ('type', '=', 'binary'),
        ]).filtered(lambda a: not a.attachment_id_jira)
        if not attachments:
            return
        attachments.lock_for_update(allow_referencing=True)
        in_jira = {} if new_issue else {
            item.get('filename'): item for item in client.attachments(task.task_id_jira)}
        for attachment in attachments:
            if attachment.name in in_jira:
                attachment.attachment_id_jira = int(in_jira[attachment.name]['id'])
            else:
                attachment._jira_upload(client, task.task_id_jira)

    def action_import_from_jira(self):
        """Create the Jira projects and issues that are missing in Odoo and
        bring in their comments and attachments."""
        self.ensure_one()
        client = self._get_client()
        stats = {'projects': 0, 'tasks': 0, 'failures': 0, 'errors': []}
        try:
            jira_projects = client.get('/rest/api/2/project')
        except JIRA_ERRORS as error:
            _logger.error("Failed to fetch projects from Jira: %s", error)
            stats['failures'] += 1
            return self._sync_notification(stats, export=False)
        # Records created here come from Jira: do not push them back.
        env = self.with_context(jira_skip_sync=True).env
        Project, Task = env['project.project'], env['project.task']
        for jira_project in jira_projects:
            if not isinstance(jira_project, dict) or not jira_project.get('key') \
                    or not str(jira_project.get('id', '')).isdigit():
                continue
            key = jira_project['key']
            project = Project.search(
                [('project_id_jira', '=', int(jira_project['id']))], limit=1)
            if not project:
                # Link a same-named Odoo project instead of duplicating it.
                project = Project.search([
                    ('name', '=', jira_project.get('name')),
                    ('is_template', '=', False),
                ]).filtered(lambda p: not p.project_id_jira)[:1]
                project.write({'project_id_jira': int(jira_project['id']),
                               'jira_project_key': key})
            if not project:
                project = Project.create({
                    'name': jira_project.get('name') or key,
                    'project_id_jira': int(jira_project['id']),
                    'jira_project_key': key,
                })
                stats['projects'] += 1
            try:
                issues = client.search_issues(f'project = "{key}"')
            except JIRA_ERRORS as error:
                _logger.error("Failed to search the issues of project %s: %s",
                              key, error)
                stats['failures'] += 1
                continue
            tasks = {task.task_id_jira: task for task in Task.search(
                [('project_id', '=', project.id), ('task_id_jira', '!=', False)])}
            for issue in issues:
                if not isinstance(issue, dict) or not issue.get('key'):
                    continue
                task = tasks.get(issue['key'])
                if not task:
                    task = Task.create({
                        'project_id': project.id,
                        'name': (issue.get('fields') or {}).get('summary') or issue['key'],
                        'task_id_jira': issue['key'],
                    })
                    stats['tasks'] += 1
                try:
                    self._import_issue_comments(client, task)
                    self._import_issue_attachments(client, task)
                except (*JIRA_ERRORS, KeyError) as error:
                    _logger.error("Failed to import comments or attachments of "
                                  "issue %s: %s", issue['key'], error)
                    stats['failures'] += 1
        return self._sync_notification(stats, export=False)

    def _import_issue_comments(self, client, task):
        """Post the Jira comments of an issue that Odoo does not have yet."""
        known = set(self.env['mail.message'].search([
            ('model', '=', 'project.task'), ('res_id', '=', task.id),
            ('message_id_jira', '!=', False),
        ]).mapped('message_id_jira'))
        for comment in client.comments(task.task_id_jira):
            comment_id = int(comment['id'])
            text = adf_to_text(comment.get('body'))
            if text and comment_id not in known:
                message = task.with_context(mail_create_nosubscribe=True).message_post(
                    body=text, message_type='comment', subtype_xmlid='mail.mt_note')
                message.message_id_jira = comment_id

    def _import_issue_attachments(self, client, task):
        """Download the Jira attachments of an issue that Odoo does not have."""
        Attachment = task.env['ir.attachment']
        existing = Attachment.search([('res_model', '=', 'project.task'),
                                      ('res_id', '=', task.id)])
        known_ids = set(existing.mapped('attachment_id_jira'))
        for item in client.attachments(task.task_id_jira):
            jira_id = int(item['id'])
            if jira_id in known_ids:
                continue
            same_name = existing.filtered(
                lambda a: a.name == item.get('filename') and not a.attachment_id_jira)
            if same_name:
                same_name[:1].attachment_id_jira = jira_id
                continue
            Attachment.create({
                'name': item.get('filename') or str(jira_id),
                'raw': client.download(item['content']),
                'mimetype': item.get('mimeType'),
                'res_model': 'project.task',
                'res_id': task.id,
                'attachment_id_jira': jira_id,
            })

    def action_export_users(self):
        """Invite the internal Odoo users that have no Jira account yet."""
        self.ensure_one()
        client = self._get_client()
        try:
            account_ids = [account.get('accountId') for account in client.users()
                           if isinstance(account, dict) and account.get('accountId')]
        except JIRA_ERRORS as error:
            _logger.error("Failed to fetch users from Jira: %s", error)
            return self._notification(self.env._(
                "Failed to fetch the users from Jira - check the server logs "
                "for details."), failures=1)
        users = self.env['res.users'].search([
            ('share', '=', False), ('jira_user_key', 'not in', account_ids),
        ]).filtered(lambda user: EMAIL_REGEX.match(user.login or ''))
        exported = failures = 0
        for user in users:
            try:
                user.jira_user_key = client.create_user(user.login, user.name)
                exported += 1
            except (*JIRA_ERRORS, KeyError) as error:
                _logger.error("Failed to create a Jira user for %s: %s",
                              user.login, error)
                failures += 1
        parts = []
        if exported:
            parts.append(self.env._("%s user(s) exported.", exported))
        if failures:
            parts.append(self.env._(
                "%s user(s) failed to export - check the server logs for "
                "details.", failures))
        return self._notification(
            ' '.join(parts) or self.env._("There are no new users to export."),
            failures=failures, done=exported)

    def action_import_users(self):
        """Create Odoo users for the Jira accounts, or link existing ones."""
        self.ensure_one()
        client = self._get_client()
        try:
            accounts = client.users()
        except JIRA_ERRORS as error:
            _logger.error("Failed to fetch users from Jira: %s", error)
            return self._notification(self.env._(
                "Failed to fetch the users from Jira - check the server logs "
                "for details."), failures=1)
        Users = self.env['res.users'].with_context(jira_skip_sync=True)
        imported = mapped = 0
        for account in accounts:
            # Skip apps and bots such as "Jira Automation".
            if not isinstance(account, dict) or not account.get('accountId') \
                    or account.get('accountType', 'atlassian') != 'atlassian':
                continue
            if Users.with_context(active_test=False).search_count(
                    [('jira_user_key', '=', account['accountId'])]):
                continue
            logins = [login for login in (account.get('emailAddress'),
                                          account.get('displayName')) if login]
            user = Users.search([('login', 'in', logins)], limit=1) if logins else Users
            if user:
                user.jira_user_key = account['accountId']
                mapped += 1
            elif logins:
                Users.create({
                    'login': logins[0],
                    'name': account.get('displayName') or logins[0],
                    'jira_user_key': account['accountId'],
                })
                imported += 1
        parts = []
        if imported:
            parts.append(self.env._("%s user(s) imported.", imported))
        if mapped:
            parts.append(self.env._(
                "%s user(s) linked to existing Odoo users.", mapped))
        return self._notification(
            ' '.join(parts) or self.env._("There are no new users to import."))

    def _get_client(self):
        """Return a Jira client for the credentials of this settings record."""
        if not (self.url and self.user_id_jira and self.api_token):
            raise UserError(self.env._(
                "Please configure the Jira URL, User Name and API Token first."))
        return JiraClient(self.url, self.user_id_jira, self.api_token)

    def _sync_notification(self, stats, export):
        """Summarise a project/task import or export for the user."""
        if export:
            parts = [self.env._("%s project(s) exported.", stats['projects']),
                     self.env._("%s task(s) exported.", stats['tasks'])]
        else:
            parts = [self.env._("%s project(s) imported.", stats['projects']),
                     self.env._("%s task(s) imported.", stats['tasks'])]
        if stats['failures']:
            parts.append(self.env._(
                "%s item(s) failed - check the server logs for details.",
                stats['failures']))
        parts += stats['errors']
        return self._notification(' '.join(parts), failures=stats['failures'],
                                  done=stats['projects'] + stats['tasks'])

    def _notification(self, message, failures=0, done=0):
        """Return a client notification; sticky when something failed."""
        if failures:
            notif_type = 'warning' if done else 'danger'
        else:
            notif_type = 'success'
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': notif_type,
                'message': message,
                'sticky': bool(failures),
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }
