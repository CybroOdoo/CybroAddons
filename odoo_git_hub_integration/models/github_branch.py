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
from odoo.exceptions import UserError, ValidationError
import requests
import logging
from dateutil import parser

_logger = logging.getLogger(__name__)


class GitHubBranch(models.Model):
    """
    Represents a GitHub branch and manages its synchronization and operations.
    """
    _name = 'github.branch'
    _description = 'GitHub Branch'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'is_default desc, name'

    repository_id = fields.Many2one('github.repository', 'Repository', required=True, ondelete='cascade', help="The repository this branch belongs to.")
    name = fields.Char('Branch Name', required=True, tracking=True, help="The name of the branch on GitHub.")
    sha = fields.Char('Latest Commit SHA', readonly=True, help="The 40-character SHA-1 hash of the latest commit on this branch.")
    is_default = fields.Boolean('Default Branch', default=False, help="If checked, this is the main/primary branch of the repository.")
    is_protected = fields.Boolean('Protected Branch', default=False, help="If checked, this branch has protection rules enabled on GitHub.")
    commits_count = fields.Integer('Commits Count', readonly=True, compute="compute_commits_count", help="Total number of commits synced for this specific branch.")
    pull_request_count = fields.Integer('Pull Requests Count', readonly=True, compute="compute_pull_request_count", help="Total number of PRs associated with this branch.")
    ahead_count = fields.Integer('Ahead Count', readonly=True, help="Number of commits this branch is ahead of the default branch.")
    behind_count = fields.Integer('Behind Count', readonly=True, help="Number of commits this branch is behind the default branch.")
    last_commit_date = fields.Datetime('Last Commit Date', readonly=True, help="The date and time of the most recent commit on this branch.")
    last_commit_author = fields.Char('Last Commit Author', readonly=True, help="The author of the most recent commit.")
    last_commit_message = fields.Text('Last Commit Message', readonly=True, help="The message of the most recent commit.")
    github_url = fields.Char('Branch URL', readonly=True, help="Direct link to the branch tree on GitHub.")
    compare_url = fields.Char('Compare URL', readonly=True, help="Link to compare this branch with the default branch on GitHub.")
    pull_request_source_ids = fields.One2many('github.pull.request', 'head_branch_id', 'PRs from this branch', help="Pull requests where this branch is the source.")
    pull_request_target_ids = fields.One2many('github.pull.request', 'base_branch_id', 'PRs to this branch', help="Pull requests where this branch is the target.")
    commit_ids = fields.One2many('github.commit', 'branch_id', 'Commits', help="Commits associated with this branch.")
    sync_status = fields.Selection([
        ('never', 'Never Synced'),
        ('syncing', 'Syncing'),
        ('success', 'Success'),
        ('error', 'Error'),
    ], default='never', readonly=True, help="Status of the most recent synchronization for this branch.")
    last_sync = fields.Datetime('Last Sync', readonly=True, help="Timestamp of the last successful sync.")
    sync_error = fields.Text('Sync Error', readonly=True, help="Error details if the branch sync failed.")

    def action_sync_branch(self, skip_heavy=False):
        """Sync branch information from GitHub"""
        for branch in self:
            try:
                branch.sync_status = 'syncing'
                headers = branch.repository_id._get_github_headers()
                url = f"https://api.github.com/repos/{branch.repository_id.owner}/{branch.repository_id.name}/branches/{branch.name}"
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                commit_data = data['commit']
                commit_date_str = commit_data['commit']['author']['date']
                commit_date = parser.isoparse(commit_date_str)
                if commit_date.tzinfo:
                    commit_date = commit_date.replace(tzinfo=None)
                branch.sudo().write({
                    'sha': commit_data['sha'],
                    'last_commit_date': commit_date,
                    'last_commit_author': commit_data['commit']['author']['name'],
                    'last_commit_message': commit_data['commit']['message'],
                    'is_protected': data.get('protected', False),
                    'github_url': f"https://github.com/{branch.repository_id.owner}/{branch.repository_id.name}/tree/{branch.name}",
                    'compare_url': f"https://github.com/{branch.repository_id.owner}/{branch.repository_id.name}/compare/{branch.name}",
                    'last_sync': fields.Datetime.now(),
                    'sync_status': 'success',
                    'sync_error': False,
                })
                if not skip_heavy:
                    if not branch.is_default:
                        branch._sync_branch_comparison()
                    branch._sync_commits()
                    branch._sync_pull_requests()

            except Exception as e:
                _logger.error(f"Error syncing branch {branch.name}: {str(e)}")
                branch.sudo().write({
                    'sync_status': 'error',
                    'sync_error': str(e)
                })

    @api.depends('commit_ids')
    def compute_commits_count(self):
        """
        Computes the number of commits in the branch.
        """
        for record in self:
            record.commits_count = self.env['github.commit'].search_count(
                [('branch_id', '=', record.id)])

    @api.depends('pull_request_source_ids', 'pull_request_target_ids')
    def compute_pull_request_count(self):
        """
        Computes the number of pull requests related to this branch.
        """
        for record in self:
            pr_ids = list(record.pull_request_source_ids.ids) + list(record.pull_request_target_ids.ids)
            record.pull_request_count = self.env['github.pull.request'].search_count(
                [('id', 'in', pr_ids)])

    def _sync_branch_comparison(self):
        """Compare branch with default branch and update ahead/behind counts"""
        self.ensure_one()
        try:
            headers = self.repository_id._get_github_headers()
            base = self.repository_id.default_branch
            head = self.name
            url = f"https://api.github.com/repos/{self.repository_id.owner}/{self.repository_id.name}/compare/{base}...{head}"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            self.sudo().write({
                'ahead_count': data.get('ahead_by', 0),
                'behind_count': data.get('behind_by', 0),
            })
        except Exception as e:
            _logger.warning(f"Failed to sync branch comparison for {self.name}: {e}")

    def _sync_commits(self):
        """Fetch commits for this branch"""
        self.ensure_one()
        headers = self.repository_id._get_github_headers()
        url = f"https://api.github.com/repos/{self.repository_id.owner}/{self.repository_id.name}/commits?sha={self.name}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        commits = response.json()
        commit_model = self.env['github.commit']
        for commit in commits:
            commit_date = parser.isoparse(commit['commit']['author']['date'])
            if commit_date.tzinfo:
                commit_date = commit_date.replace(tzinfo=None)
            existing = commit_model.sudo().search([
                ('sha', '=', commit['sha']),
                ('repository_id', '=', self.repository_id.id)
            ], limit=1)
            if existing:
                if not existing.branch_id:
                    existing.sudo().write({'branch_id': self.id})
            else:
                vals = {
                    'repository_id': self.repository_id.id,
                    'branch_id': self.id,
                    'sha': commit['sha'],
                    'message': commit['commit']['message'],
                    'author_name': commit['commit']['author']['name'],
                    'author_email': commit['commit']['author']['email'],
                    'committed_date': commit_date,
                    'github_url': commit['html_url'],
                }
                commit_model.sudo().create(vals)

    def _sync_pull_requests(self):
        """Fetch pull requests involving this branch"""
        self.ensure_one()
        headers = self.repository_id._get_github_headers()
        url = f"https://api.github.com/repos/{self.repository_id.owner}/{self.repository_id.name}/pulls?state=all"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        pulls = response.json()
        pr_model = self.env['github.pull.request']
        for pr in pulls:
            head_branch = pr['head']['ref']
            base_branch = pr['base']['ref']
            vals = {
                'repository_id': self.repository_id.id,
                'github_id': pr['id'],
                'number': pr['number'],
                'title': pr['title'],
                'state': 'merged' if pr.get('merged') else pr['state'],
                'github_url': pr['html_url'],
                'head_branch_id': self.id if head_branch == self.name else False,
                'base_branch_id': self.id if base_branch == self.name else False,
            }
            existing = pr_model.sudo().search([
                ('github_id', '=', pr['id']),
                ('repository_id', '=', self.repository_id.id)
            ], limit=1)
            if existing:
                existing.sudo().write(vals)
            else:
                pr_model.sudo().create(vals)

    def action_create_pull_request(self):
        """Create a pull request from this branch"""
        if self.is_default:
            raise UserError(_('Cannot create PR from default branch'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create Pull Request'),
            'res_model': 'github.pull.request.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_repository_id': self.repository_id.id,
                'default_head_branch': self.name,
                'default_base_branch': self.repository_id.default_branch,
            }
        }

    def action_view_commits(self):
        """View commits in this branch"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Branch Commits'),
            'res_model': 'github.commit',
            'view_mode': 'tree,form',
            'domain': [('branch_id', '=', self.id)],
            'context': {'default_branch_id': self.id}
        }

    def action_view_pull_requests(self):
        """View pull requests from/to this branch"""
        pr_ids = list(self.pull_request_source_ids.ids) + list(self.pull_request_target_ids.ids)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Related Pull Requests'),
            'res_model': 'github.pull.request',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', pr_ids)],
        }

    def action_delete_branch(self):
        """Delete branch on GitHub (protected operation)"""
        if self.is_default:
            raise ValidationError(_('Cannot delete default branch'))
        if self.is_protected:
            raise ValidationError(_('Cannot delete protected branch'))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Delete Branch'),
            'res_model': 'github.branch.delete.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_branch_id': self.id}
        }



