# -*- coding: utf-8 -*-
###############################################################################
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
###############################################################################

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError
import re
import requests


class GitHubIssue(models.Model):
    """
    Represents a GitHub issue and manages its synchronization and Odoo task creation.
    """
    _name = 'github.issue'
    _description = 'GitHub Issue'
    _rec_name = 'number'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'number desc'

    repository_id = fields.Many2one('github.repository', 'Repository', required=True, ondelete='cascade', help="The repository this issue belongs to.")
    github_id = fields.Char('GitHub ID', readonly=True, help="The unique internal ID assigned to this issue by GitHub.")
    number = fields.Integer('Issue Number', readonly=True, help="The display number of the issue on GitHub (e.g., #1).")
    title = fields.Char('Title', required=True, tracking=True, help="The title of the GitHub issue.")
    body = fields.Html('Description', help="The body/description content of the GitHub issue.")
    state = fields.Selection([
        ('open', 'Open'),
        ('closed', 'Closed'),
    ], required=True, default='open', tracking=True, help="The current status of the issue on GitHub.")
    github_url = fields.Char('GitHub URL', readonly=True, help="The direct link to this issue on GitHub.")
    created_at = fields.Datetime('Created At', readonly=True, help="The date and time when the issue was created on GitHub.")
    updated_at = fields.Datetime('Updated At', readonly=True, help="The date and time when the issue was last updated on GitHub.")
    closed_at = fields.Datetime('Closed At', readonly=True, help="The date and time when the issue was closed, if applicable.")
    assignee = fields.Char('Assignee', help="The GitHub login of the user assigned to this issue.")
    labels = fields.Char('Labels', help="Comma-separated list of labels applied to this issue.")
    issue_age_days = fields.Integer('Issue Age (Days)', compute='_compute_issue_age_days', store=True, help="The total age of the issue in days since creation.")
    task_ids = fields.Many2many(
        'project.task',
        'github_issue_task_rel',
        'issue_id',
        'task_id',
        string="Tasks",
        help="Odoo tasks linked to this GitHub issue."
    )
    project_ids = fields.Many2many(
        related='repository_id.project_ids',
        comodel_name='project.project',
        string='Projects',
        readonly=True,
        help="Projects linked to the repository of this GitHub issue."
    )
    
    _sql_constraints = [
        ('github_id_repo_unique', 'unique(github_id, repository_id)', 'The GitHub ID must be unique per repository!'),
    ]

    @api.depends('created_at', 'closed_at', 'state')
    def _compute_issue_age_days(self):
        """Calculate the age of an issue in days."""
        from datetime import datetime
        now = fields.Datetime.now()
        for record in self:
            if record.created_at:
                end_date = record.closed_at if record.state == 'closed' and record.closed_at else now
                record.issue_age_days = (end_date - record.created_at).days
            else:
                record.issue_age_days = 0

    @api.model
    def create(self, vals):
        """
        Extends create to automatically link the issue to tasks.
        """
        issue = super().create(vals)
        issue._link_to_task()
        return issue

    def write(self, vals):
        """
        Extends write to re-link issue to tasks if title or body changes.
        """
        res = super().write(vals)
        if 'title' in vals or 'body' in vals:
            self._link_to_task()
        return res

    def _link_to_task(self):
        """Auto-link issue to tasks based on message patterns"""
        patterns = [
            r'\[TASK-(\d+)\]',
            r'\btask-(\d+)\b',
        ]
        for record in self:
            text_to_search = f"{record.title or ''} {record.body or ''}"
            task_ids_to_add = []
            for pattern in patterns:
                for match in re.finditer(pattern, text_to_search, re.IGNORECASE):
                    try:
                        task_id = int(match.group(1))
                        task = self.env['project.task'].sudo().search([('id', '=', task_id)], limit=1)
                        if task and task.id not in record.task_ids.ids:
                            task_ids_to_add.append(task.id)
                    except ValueError:
                        continue
            if task_ids_to_add:
                record.sudo().write({'task_ids': [(4, tid) for tid in task_ids_to_add]})

    def action_create_task(self):
        """Create Odoo task from GitHub issue for all linked projects"""
        tasks_to_return = self.env['project.task']
        for issue in self:
            if not issue.project_ids:
                # If called manually on an issue with no projects linked to its repo
                raise ValidationError(_('No project linked to repository %s. Please configure project integration first.', issue.repository_id.name))
            
            for project in issue.project_ids:
                # Check if a task already exists for this issue in THIS specific project
                existing_task = self.env['project.task'].sudo().search([
                    ('github_issue_id', '=', issue.id),
                    ('project_id', '=', project.id)
                ], limit=1)
                
                if not existing_task:
                    task_vals = {
                        'name': f"[#{issue.number}] {issue.title}",
                        'description': issue.body,
                        'project_id': project.id,
                        'github_issue_id': issue.id,
                    }
                    if issue.state == 'closed':
                        done_stage = project.type_ids.filtered(lambda s: s.fold)
                        if done_stage:
                            task_vals['stage_id'] = done_stage[0].id
                    task = self.env['project.task'].create(task_vals)
                    
                    # Link the new task to the issue (Many2many)
                    issue.sudo().write({'task_ids': [(4, task.id)]})
                    
                    issue.message_post(
                        body=_('Created task: <a href="#" data-oe-model="project.task" data-oe-id="%s">%s</a>') % (task.id, task.name)
                    )
                    tasks_to_return |= task
                else:
                    tasks_to_return |= existing_task
                
        if len(self) == 1 and tasks_to_return:
            return tasks_to_return[0].get_formview_action()
        return None

    def action_view_github_issue(self):
        """Open GitHub issue in browser"""
        if self.github_url:
            return {
                'type': 'ir.actions.act_url',
                'url': self.github_url,
                'target': 'new',
            }

    def action_export_to_github(self):
        """Create issue on GitHub if it doesn't exist"""
        self.ensure_one()
        if self.github_id:
            raise UserError(_("Issue is already linked to GitHub."))
        headers = self.repository_id._get_github_headers()
        url = f"https://api.github.com/repos/{self.repository_id.owner}/{self.repository_id.name}/issues"
        payload = {
            "title": self.title,
            "body": self.body or ""
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 201:
            data = response.json()
            self.write({
                'github_id': str(data['id']),
                'number': data['number'],
                'github_url': data['html_url'],
                'state': data['state'],
            })
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Issue created successfully on GitHub.'),
                    'type': 'success',
                }
            }
        else:
            raise UserError(_("Failed to create issue: %s") % response.text)