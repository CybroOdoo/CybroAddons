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
import requests


class ProjectTask(models.Model):
    """
    Extends the project.task model to link with GitHub issues, PRs, and commits.
    """
    _inherit = 'project.task'

    github_issue_id = fields.Many2one('github.issue', 'GitHub Issue', help="The GitHub issue linked to this task.")
    github_pr_id = fields.Many2one('github.pull.request', 'GitHub Pull Request', help="The GitHub pull request linked to this task.")
    github_issue_number = fields.Integer(related='github_issue_id.number', string='Issue #', readonly=True, help="Display number of the linked GitHub issue.")
    github_issue_state = fields.Selection(related='github_issue_id.state', readonly=True, help="Current status of the linked GitHub issue.")
    github_issue_url = fields.Char(related='github_issue_id.github_url', readonly=True, help="Direct link to the linked GitHub issue.")
    commits_count = fields.Integer('Commits Count', compute='_compute_commits_count', help="Number of GitHub commits associated with this task.")
    
    github_branch_name = fields.Char(string="Branch Name", help="Name of the branch associated with this task.")
    github_branch_url = fields.Char(string="Branch Url", help="Direct link to the branch on GitHub.")
    github_pr_title = fields.Char(string="Title", help="Title for the GitHub pull request.")
    github_pr_description = fields.Char(string="Description", help="Description for the GitHub pull request.")
    github_merge_into = fields.Char(string="Merge Into", help="The target branch for merging (base).")
    github_pr_url = fields.Char(string="Pull Request URL", help="Direct link to the created GitHub pull request.")

    repository_id = fields.Many2one(
        "github.repository",
        string="GitHub Repository",
        related="project_id.github_repository_id",
        store=True,
        readonly=False,
        help="The GitHub repository this task is associated with."
    )
    branch_ids = fields.Many2many(
        "github.branch",
        "github_branch_task_rel",
        "task_id",
        "branch_id",
        string="GitHub Branches",
        domain="[('repository_id', '=', repository_id)]",
        help="GitHub branches related to this task."
    )

    @api.depends('repository_id', 'branch_ids')
    def _compute_commits_count(self):
        """
        Computes the number of commits linked to the task across repositories and branches.
        """
        for task in self:
            domain = [('task_ids', 'in', task.id)]
            if task.repository_id:
                domain.append(('repository_id', '=', task.repository_id.id))
            if task.branch_ids:
                domain.append(('branch_id', 'in', task.branch_ids.ids))
            task.commits_count = self.env['github.commit'].search_count(domain)

    def action_view_github_issue(self):
        """
        Opens the linked GitHub issue in a new browser tab.
        """
        if self.github_issue_url:
            return {
                'type': 'ir.actions.act_url',
                'url': self.github_issue_url,
                'target': 'new',
            }

    def action_view_commits(self):
        """View related commits"""
        self.ensure_one()
        domain = [('task_ids', 'in', self.id)]
        if self.repository_id:
            domain.append(('repository_id', '=', self.repository_id.id))
        if self.branch_ids:
            domain.append(('branch_id', 'in', self.branch_ids.ids))
            
        return {
            'type': 'ir.actions.act_window',
            'name': _('Commits'),
            'res_model': 'github.commit',
            'view_mode': 'tree,form',
            'domain': domain,
            'context': {
                'default_task_ids': [self.id],
                'search_default_group_by_repository_id': 1, 
                'search_default_group_by_branch_id': 1
            },
        }

    def action_export_to_github(self):
        """Create issue on GitHub for this task"""
        self.ensure_one()
        if self.github_issue_id:
            raise UserError(_("Task is already linked to a GitHub Issue."))
        if not self.repository_id:
            raise UserError(_("Please assign a GitHub repository to the task before exporting (Projects need to be linked to a repository)."))
            
        headers = self.repository_id._get_github_headers()
        url = f"https://api.github.com/repos/{self.repository_id.owner}/{self.repository_id.name}/issues"
        payload = {
            "title": self.name,
            "body": self.description or ""
        }
        
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 201:
            data = response.json()
            issue = self.env['github.issue'].sudo().create({
                'repository_id': self.repository_id.id,
                'github_id': str(data['id']),
                'number': data['number'],
                'title': data['title'],
                'body': data.get('body', ''),
                'state': data['state'],
                'github_url': data['html_url'],
            })
            self.github_issue_id = issue.id
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Issue exported successfully to GitHub.'),
                    'type': 'success',
                }
            }
        else:
            raise UserError(_("Failed to export issue: %s") % response.text)

    def action_open_pr_wizard(self):
        """Opens the Pull Request wizard pre-filled with task data."""
        self.ensure_one()
        if not self.repository_id:
            raise UserError(_("Please assign a GitHub repository to the task before creating a pull request."))
            
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create Pull Request'),
            'res_model': 'github.pull.request.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_repository_id': self.repository_id.id,
                'default_head_branch': self.github_branch_name,
                'default_base_branch': self.github_merge_into or self.repository_id.default_branch,
                'default_name': self.github_pr_title or self.name,
                'default_description': self.github_pr_description or self.description,
            }
        }
