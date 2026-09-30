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
import csv
import io
import base64
import re


class GitHubCommit(models.Model):
    """
    Represents a GitHub commit and handles its synchronization and linking to Odoo tasks.
    """
    _name = 'github.commit'
    _description = 'GitHub Commit'
    _rec_name = 'sha'
    _order = 'committed_date desc'

    repository_id = fields.Many2one('github.repository', 'Repository', required=True, ondelete='cascade', readonly=True, help="The repository this commit belongs to.")
    sha = fields.Char('SHA', required=True, readonly=True, help="The unique 40-character SHA-1 hash identifying the commit.")
    message = fields.Text('Commit Message', required=True, readonly=True, help="The commit message provided by the author.")
    author_name = fields.Char('Author Name', readonly=True, help="The name of the person who authored the commit.")
    author_email = fields.Char('Author Email', readonly=True, help="The email address of the commit author.")
    committed_date = fields.Datetime('Committed Date', readonly=True, help="The date and time when the commit was made.")
    github_url = fields.Char('GitHub URL', help="Direct link to the commit on GitHub.")
    task_ids = fields.Many2many(
        'project.task',
        'github_commit_task_rel',
        'commit_id',
        'task_id',
        string='Linked Tasks',
        help="Odoo tasks associated with this specific commit via regex matching."
    )
    project_ids = fields.Many2many(
        related='repository_id.project_ids',
        comodel_name='project.project',
        string='Projects',
        readonly=True,
        help="Projects associated with this commit's repository."
    )
    commit_day = fields.Date('Commit Date', compute='_compute_commit_date', store=True, help="Helper field for dashboard grouping by day.")
    branch_id = fields.Many2one('github.branch', 'Branch', help="The branch record this commit was synced from.")

    @api.depends('committed_date')
    def _compute_commit_date(self):
        """Helper for grouping commits by day in dashboard views."""
        for record in self:
            record.commit_day = record.committed_date.date() if record.committed_date else False

    def action_view_github_commit(self):
        """Open commit on GitHub"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': self.github_url,
            'target': 'new',
        }

    def action_export_commits_csv(self):
        """Export selected commits to CSV"""
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)
        
        # Header
        writer.writerow(['Repository', 'SHA', 'Author', 'Email', 'Date', 'Message', 'URL'])
        
        for commit in self:
            writer.writerow([
                commit.repository_id.name,
                commit.sha,
                commit.author_name,
                commit.author_email,
                commit.committed_date,
                commit.message,
                commit.github_url
            ])
            
        data = base64.b64encode(output.getvalue().encode()).decode()
        attachment = self.env['ir.attachment'].create({
            'name': 'github_commits.csv',
            'type': 'binary',
            'datas': data,
            'mimetype': 'text/csv',
        })
        
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }

    @api.model
    def create(self, vals):
        """
        Overrides the create method to link the commit to Odoo tasks.
        """
        commit = super().create(vals)
        commit._link_to_task()
        return commit

    def _link_to_task(self):
        """Auto-link commit to tasks based on commit message patterns"""
        if self.task_ids:
            return
        patterns = [
            r'#(\d+)',
            r'task-(\d+)',
            r'issue-(\d+)',
            r'closes #(\d+)',
            r'fixes #(\d+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, self.message, re.IGNORECASE)
            if match:
                task_number = int(match.group(1))
                github_issue = self.env['github.issue'].search([
                    ('number', '=', task_number),
                    ('repository_id', '=', self.repository_id.id),
                    ('task_ids', '!=', False)
                ], limit=1)
                if github_issue and github_issue.task_ids:
                    self.task_ids = [(6, 0, github_issue.task_ids.ids)]
                    break
