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
from odoo.exceptions import UserError
import re


class GitHubPullRequest(models.Model):
    """
    Represents a GitHub pull request and manages its synchronization and Odoo task creation.
    """
    _name = 'github.pull.request'
    _description = 'GitHub Pull Request'
    _rec_name = 'number'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'number desc'

    repository_id = fields.Many2one('github.repository', 'Repository', required=True, ondelete='cascade', help="The repository this pull request belongs to.")
    github_id = fields.Char('GitHub ID', readonly=True, help="The unique internal ID assigned to this PR by GitHub.")
    number = fields.Integer('PR Number', readonly=True, help="The pull request number on GitHub (e.g., #42).")
    title = fields.Char('Title', required=True, tracking=True, help="The title of the pull request.")
    body = fields.Html('Description', help="The description content of the pull request.")
    state = fields.Selection([
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('merged', 'Merged'),
    ], required=True, default='open', tracking=True, help="The current status of the PR on GitHub.")
    github_url = fields.Char('GitHub URL', readonly=True, help="Direct link to the pull request on GitHub.")
    created_at = fields.Datetime('Created At', readonly=True, help="The date and time when the PR was opened on GitHub.")
    updated_at = fields.Datetime('Updated At', readonly=True, help="The date and time when the PR was last updated on GitHub.")
    merged_at = fields.Datetime('Merged At', readonly=True, help="The date and time when the PR was merged, if applicable.")
    closed_at = fields.Datetime('Closed At', readonly=True, help="The date and time when the PR was closed without merging.")
    author = fields.Char('Author', help="The GitHub login of the user who opened the PR.")
    assignee = fields.Char('Assignee', help="The GitHub login of the user assigned to this PR.")
    head_branch = fields.Char('Source Branch', help="The branch containing the changes to be merged.")
    base_branch = fields.Char('Target Branch', help="The branch into which the changes are intended to be merged.")
    merged = fields.Boolean('Merged', default=False, help="Indicates if the PR has been successfully merged.")
    mergeable = fields.Boolean('Mergeable', help="Indicates if the PR can be merged without conflicts.")
    review_state = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('changes_requested', 'Changes Requested'),
    ], default='pending', help="The current review status of the pull request.")
    task_ids = fields.Many2many(
        'project.task',
        'github_pr_task_rel',
        'pr_id',
        'task_id',
        string='Linked Tasks',
        help="Odoo tasks associated with this pull request."
    )
    project_ids = fields.Many2many(
        related='repository_id.project_ids',
        comodel_name='project.project',
        string='Projects',
        readonly=True,
        help="Projects linked to the repository of this pull request."
    )
    head_branch_id = fields.Many2one('github.branch', 'Source Branch Record',
                                     help="Linked branch record if exists")
    base_branch_id = fields.Many2one('github.branch', 'Target Branch Record',
                                     help="Linked branch record if exists")
    
    _sql_constraints = [
        ('github_id_repo_unique', 'unique(github_id, repository_id)', 'The GitHub ID must be unique per repository!'),
    ]

    def action_create_task(self):
        """Create Odoo task from GitHub pull request"""
        tasks_to_return = self.env['project.task']
        for pr in self:
            if pr.task_ids:
                tasks_to_return |= pr.task_ids[0]
                continue
            if not pr.project_ids:
                raise UserError(_('No project linked to repository %s. Please configure project integration first.', pr.repository_id.name))
            tasks = []
            created_tasks = self.env['project.task']
            for project in pr.project_ids:
                task_vals = {
                    'name': f"[PR #{pr.number}] {pr.title}",
                    'description': pr.body,
                    'project_id': project.id,
                    'github_pr_id': pr.id,
                }
                task = self.env['project.task'].create(task_vals)
                tasks.append(task.id)
                created_tasks |= task
            if tasks:
                pr.task_ids = [(6, 0, tasks)]
                pr.message_post(
                    body=_('Created task: <a href="#" data-oe-model="project.task" data-oe-id="%s">%s</a>') % (created_tasks[-1].id, created_tasks[-1].name)
                )
                tasks_to_return |= created_tasks[0]
        
        if len(self) == 1 and tasks_to_return:
            return tasks_to_return.get_formview_action()
        return None

    @api.model
    def create(self, vals):
        """Override to link branches and tasks"""
        pr = super().create(vals)
        pr._link_branches()
        pr._link_to_task()
        return pr

    def write(self, vals):
        """Override to update branch links and tasks"""
        result = super().write(vals)
        if 'head_branch' in vals or 'base_branch' in vals:
            self._link_branches()
        if 'title' in vals or 'body' in vals:
            self._link_to_task()
        return result

    def _link_to_task(self):
        """Auto-link PR to tasks based on message patterns"""
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

    def _link_branches(self):
        """Link PR to branch records"""
        for pr in self:
            if pr.head_branch:
                head_branch = self.env['github.branch'].search([
                    ('name', '=', pr.head_branch),
                    ('repository_id', '=', pr.repository_id.id)
                ], limit=1)
                if head_branch:
                    pr.head_branch_id = head_branch.id
            if pr.base_branch:
                base_branch = self.env['github.branch'].search([
                    ('name', '=', pr.base_branch),
                    ('repository_id', '=', pr.repository_id.id)
                ], limit=1)
                if base_branch:
                    pr.base_branch_id = base_branch.id
