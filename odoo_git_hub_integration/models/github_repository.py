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
import logging

from datetime import datetime

_logger = logging.getLogger(__name__)


class GitHubRepository(models.Model):
    """
    Represents a GitHub repository and manages its synchronization with Odoo.
    """
    _name = 'github.repository'
    _description = 'GitHub Repository'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _default_owner(self):
        """Returns the username from the active GitHub configuration."""
        config = self.env['github.config'].sudo().search([('active', '=', True)], limit=1)
        return config.username if config else False

    name = fields.Char('Repository Name', tracking=True, help="The name of the repository on GitHub.")
    full_name = fields.Char('Full Name', help='The full name of the repository (owner/repository).')
    github_id = fields.Char('GitHub ID', readonly=True, help="The unique numerical ID assigned by GitHub.")
    owner = fields.Char('Owner', default=_default_owner, help="The GitHub username or organization that owns the repository.")
    description = fields.Text('Description', help="The description of the repository as seen on GitHub.")
    url = fields.Char('Repository URL', readonly=True, help="The web URL to view the repository on GitHub.")
    clone_url = fields.Char('Clone URL', readonly=True, help="The URL used for cloning the repository via HTTPS.")
    default_branch = fields.Char('Default Branch', default='main', readonly=True, help="The default branch of the repository (e.g., main or master).")
    private = fields.Boolean('Visibility', default=False, help="Choose whether the repository is private or public. When checked, the repository on GitHub is set to private. When unchecked, it is set to public.")
    stars_count = fields.Integer('Stars', readonly=True, help="The number of stars the repository has received.")
    open_issues_count = fields.Integer('Issues', readonly=True, compute="compute_open_issues_count", help="The number of open issues in the repository.")
    project_ids = fields.Many2many(
        'project.project',
        'github_repository_project_rel',
        'repository_id',
        'project_id',
        string='Linked Projects',
        help="Projects in Odoo that are synchronized with this GitHub repository."
    )
    # Aggregates for Dashboard Kanban
    pull_requests_count = fields.Integer('Total PRs', compute='_compute_dashboard_stats', help="Total number of pull requests associated with this repository.")
    task_ids = fields.Many2many(
        "project.task",
        "github_repository_task_rel",
        "repository_id",
        "task_id",
        string="Linked Tasks",
        domain="[('project_id', 'in', project_ids)]",
        help="Specific Odoo tasks linked to this repository."
    )
    issue_ids = fields.One2many('github.issue', 'repository_id', 'Issues', help="List of issues fetched from GitHub.")
    pull_request_ids = fields.One2many('github.pull.request', 'repository_id', 'Pull Requests', help="List of Pull Requests fetched from GitHub.")
    commit_ids = fields.One2many('github.commit', 'repository_id', 'Commits', help="List of commits successfully synced.")
    last_sync = fields.Datetime('Last Sync', readonly=True, help="Date and time of the last successful synchronization.")
    last_commit_sync = fields.Datetime('Last Commit Sync', readonly=True, help="Timestamp of the last successful commit history synchronization.")
    sync_status = fields.Selection([
        ('never', 'Never Synced'),
        ('syncing', 'Syncing'),
        ('success', 'Success'),
        ('error', 'Error'),
    ], default='never', readonly=True, help="Current status of the repository synchronization.")
    sync_error = fields.Text('Last Sync Error', readonly=True, help="Details of the error if the last sync failed.")
    branch_ids = fields.One2many('github.branch', 'repository_id', 'Branches', help="Branches tracked for this repository.")
    branches_count = fields.Integer('Branches Count', compute='_compute_branches_count', help="Number of branches in this repository.")
    collaborator_ids = fields.One2many('github.collaborator', 'repository_id', 'Collaborators', help="Users who have access to this repository.")
    collaborators_count = fields.Integer('Collaborators Count', compute='_compute_collaborators_count', help="Total number of collaborators.")
    fork_parent_id = fields.Many2one(
        "github.repository", string="Forked From", readonly=True, help="The parent repository if this is a fork."
    )
    fork_child_ids = fields.One2many(
        "github.repository", "fork_parent_id", string="Forks", readonly=True, help="Repositories that have forked from this one."
    )

    def _update_github_visibility(self, private):
        """Update repository visibility on GitHub"""
        for repo in self:
            if not repo.github_id:
                continue
            if not repo.owner or not repo.name:
                continue
            headers = repo._get_github_headers()
            url = f"https://api.github.com/repos/{repo.owner}/{repo.name}"
            payload = {
                "private": private
            }
            try:
                response = requests.patch(url, headers=headers, json=payload, timeout=10)
                if response.status_code != 200:
                    raise UserError(_("Failed to update repository visibility on GitHub: %s") % response.text)
            except Exception as e:
                raise UserError(_("Failed to update repository visibility on GitHub: %s") % str(e))

    def write(self, vals):
        res = super().write(vals)
        if 'private' in vals and not self.env.context.get('skip_github_sync'):
            for repo in self:
                if repo.github_id:
                    repo._update_github_visibility(vals['private'])
        return res

    @api.depends('pull_request_ids')
    def _compute_dashboard_stats(self):
        """Compute aggregate counts for dashboard visibility."""
        for repo in self:
            repo.pull_requests_count = len(repo.pull_request_ids)

    def _parse_github_datetime(self, value):
        """
        Parses GitHub datetime string into Python datetime object.
        """
        if not value:
            return False
        if isinstance(value, str):
            return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
        return value

    @api.model
    def _get_github_headers(self):
        """Get GitHub API headers with authentication"""
        config = self.env['github.config'].sudo().search([('active', '=', True)], limit=1)
        token = config.access_token if config else False
        if not token:
            raise UserError(_('GitHub access token is not configured. Please configure it in GitHub Integration > Configuration.'))
        return {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }

    def _fetch_all_pages(self, url, params=None, max_pages=None):
        """Fetch all pages from GitHub API, handling rate limits and optional page limit."""
        headers = self._get_github_headers()
        if params is None:
            params = {}
        all_data = []
        page_count = 0
        while url:
            if max_pages and page_count >= max_pages:
                _logger.info(f"Reached max pages limit ({max_pages}) for URL: {url}")
                break
            
            response = requests.get(url, headers=headers, params=params)
            
            # Rate limit handling
            if response.status_code == 403 and 'X-RateLimit-Remaining' in response.headers:
                if int(response.headers.get('X-RateLimit-Remaining', 1)) == 0:
                    _logger.warning("GitHub API rate limit exceeded.")
                    raise UserError(_("GitHub API rate limit exceeded. Please try again later."))
            
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list):
                all_data.extend(data)
            else:
                all_data.append(data)
                
            page_count += 1
            # Check for next page
            url = None
            params = {}  # Clear params as they are included in the 'next' URL
            if 'Link' in response.headers:
                links = response.headers['Link'].split(', ')
                for link in links:
                    if 'rel="next"' in link:
                        url_part = link.split(';')[0].strip()
                        url = url_part[1:-1] # Remove < and >
                        break
        return all_data

    def action_sync_repository(self):
        """Sync repository data from GitHub with timeout protection."""
        for repo in self:
            if not repo.owner or not repo.name:
                raise UserError(_("Please provide both Owner and Repository Name before syncing."))
            try:
                repo.sudo().write({'sync_status': 'syncing'})
                headers = repo._get_github_headers()
                url = f"https://api.github.com/repos/{repo.owner}/{repo.name}"
                
                # Metadata sync with short timeout
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                repo.sudo().with_context(skip_github_sync=True).write({
                    'name': data['name'],
                    'github_id': str(data['id']),
                    'full_name': data['full_name'],
                    'description': data.get('description', ''),
                    'url': data['html_url'],
                    'clone_url': data['clone_url'],
                    'default_branch': data['default_branch'],
                    'private': data['private'],
                    'stars_count': data['stargazers_count'],
                    'open_issues_count': data['open_issues_count'],
                    'sync_error': False,
                })
                
                # Perform sub-syncs with progress logging
                _logger.info(f"Syncing collaborators for {repo.name}...")
                repo._sync_collaborators()
                _logger.info(f"Syncing branches for {repo.name}...")
                repo._sync_branches()
                _logger.info(f"Syncing issues for {repo.name}...")
                repo._sync_issues()
                _logger.info(f"Syncing pull requests for {repo.name}...")
                repo._sync_pull_requests()
                _logger.info(f"Syncing commits for {repo.name}...")
                # repo._sync_commits()  # Moved to separate action

                # Update status and last sync date at the very end
                repo.sudo().write({
                    'last_sync': fields.Datetime.now(),
                    'sync_status': 'success',
                })

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Sync Complete'),
                        'message': _('Repository data has been successfully synchronized.'),
                        'type': 'success',
                    }
                }
            except Exception as e:
                _logger.error(f"Error syncing repository {repo.name}: {str(e)}")
                repo.sudo().write({
                    'sync_status': 'error',
                    'sync_error': str(e)
                })
                raise UserError(_('Error syncing repository: %s') % str(e))

    def action_sync_commits(self):
        """Dedicated action to sync commits for the repository."""
        for repo in self:
            try:
                repo.sudo().write({'sync_status': 'syncing'})
                repo._sync_commits()
                repo.sudo().write({
                    'last_commit_sync': fields.Datetime.now(),
                    'sync_status': 'success',
                })
            except Exception as e:
                _logger.error(f"Error syncing commits for {repo.name}: {str(e)}")
                repo.sudo().write({
                    'sync_status': 'error',
                    'sync_error': str(e)
                })
                raise UserError(_('Error syncing commits: %s') % str(e))
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Commits Synced'),
                'message': _('Commit history has been successfully updated.'),
                'type': 'success',
            }
        }

    def _sync_issues(self):
        """Sync GitHub issues"""
        url = f"https://api.github.com/repos/{self.owner}/{self.name}/issues"
        params = {'state': 'all', 'per_page': 100}
        # Limit issues sync to avoid timeouts on very old/large repos
        issues_data = self._fetch_all_pages(url, params=params, max_pages=10)
        for issue_data in issues_data:
            if 'pull_request' in issue_data:
                continue
            existing_issue = self.env['github.issue'].sudo().search([
                ('github_id', '=', str(issue_data['id'])),
                ('repository_id', '=', self.id)
            ], limit=1)
            issue_vals = {
                'repository_id': self.id,
                'github_id': str(issue_data['id']),
                'number': issue_data['number'],
                'title': issue_data['title'],
                'body': issue_data.get('body', ''),
                'state': issue_data['state'],
                'github_url': issue_data['html_url'],
                'created_at': self._parse_github_datetime(issue_data['created_at']),
                'updated_at': self._parse_github_datetime(issue_data['updated_at']),
                'assignee': issue_data['assignee']['login'] if issue_data.get('assignee') else False,
                'labels': ', '.join([label['name'] for label in issue_data.get('labels', [])]),
            }
            if existing_issue:
                existing_issue.sudo().write(issue_vals)
                issue_to_check = existing_issue
            else:
                issue_to_check = self.env['github.issue'].sudo().create(issue_vals)
            
            # Ensure task exists if project is linked - only for open issues to save time
            if self.project_ids and not issue_to_check.task_ids and issue_to_check.state == 'open':
                _logger.info(f"Creating task for open issue #{issue_to_check.number}")
                issue_to_check.action_create_task()

    def _sync_pull_requests(self):
        """Sync GitHub pull requests"""
        url = f"https://api.github.com/repos/{self.owner}/{self.name}/pulls"
        params = {'state': 'all', 'per_page': 100}
        # Limit PRs sync to avoid timeouts
        prs_data = self._fetch_all_pages(url, params=params, max_pages=10)
        for pr_data in prs_data:
            existing_pr = self.env['github.pull.request'].sudo().search([
                ('github_id', '=', str(pr_data['id'])),
                ('repository_id', '=', self.id)
            ], limit=1)
            pr_vals = {
                'repository_id': self.id,
                'github_id': str(pr_data['id']),
                'number': pr_data['number'],
                'title': pr_data['title'],
                'body': pr_data.get('body', ''),
                'state': pr_data['state'],
                'github_url': pr_data['html_url'],
                'created_at': self._parse_github_datetime(pr_data['created_at']),
                'updated_at': self._parse_github_datetime(pr_data['updated_at']),
                'merged_at': self._parse_github_datetime(pr_data.get('merged_at')),
                'author': pr_data['user']['login'],
                'head_branch': pr_data['head']['ref'],
                'base_branch': pr_data['base']['ref'],
                'merged': pr_data.get('merged', False),
                'mergeable': pr_data.get('mergeable'),
            }
            if existing_pr:
                existing_pr.sudo().write(pr_vals)
            else:
                self.env['github.pull.request'].sudo().create(pr_vals)

    def _sync_commits(self):
        """Sync recent commits per branch"""
        for branch in self.branch_ids:
            _logger.info(f"Fetching commits for branch {branch.name}...")
            url = f"https://api.github.com/repos/{self.owner}/{self.name}/commits"
            # Default branch gets more history, others get minimal to avoid timeouts
            per_page = 100 if branch.is_default else 30
            params = {'sha': branch.name, 'per_page': per_page}
            if self.last_commit_sync:
                params['since'] = self.last_commit_sync.strftime("%Y-%m-%dT%H:%M:%SZ")
            
            # Limit pages: 3 for default branch, 1 for others (on first sync)
            if not self.last_commit_sync:
                max_pages = 3 if branch.is_default else 1
            else:
                max_pages = 5 if branch.is_default else 2
                
            commits_data = self._fetch_all_pages(url, params=params, max_pages=max_pages)
            _logger.info(f"Fetched {len(commits_data)} commits for {branch.name}")
            for commit_data in commits_data:
                existing_commit = self.env['github.commit'].sudo().search([
                    ('sha', '=', commit_data['sha']),
                    ('repository_id', '=', self.id)
                ], limit=1)
                if existing_commit:
                    if not existing_commit.branch_id:
                        existing_commit.sudo().write({'branch_id': branch.id})
                else:
                    commit_vals = {
                        'repository_id': self.id,
                        'branch_id': branch.id,
                        'sha': commit_data['sha'],
                        'message': commit_data['commit']['message'],
                        'author_name': commit_data['commit']['author']['name'],
                        'author_email': commit_data['commit']['author']['email'],
                        'committed_date': self._parse_github_datetime(commit_data['commit']['author']['date']),
                        'github_url': commit_data['html_url'],
                    }
                    commit = self.env['github.commit'].sudo().create(commit_vals)
                    commit._link_to_task()


    @api.depends('branch_ids')
    def _compute_branches_count(self):
        """
        Computes the number of branches in the repository.
        """
        for repo in self:
            repo.branches_count = len(repo.branch_ids)

    @api.depends('collaborator_ids')
    def _compute_collaborators_count(self):
        """
        Computes the number of collaborators in the repository.
        """
        for repo in self:
            repo.collaborators_count = len(repo.collaborator_ids)

    def _sync_branches(self):
        """Sync repository branches"""
        url = f"https://api.github.com/repos/{self.owner}/{self.name}/branches"
        params = {'per_page': 100}
        branches_data = self._fetch_all_pages(url, params=params)
        github_branch_names = [branch_data['name'] for branch_data in branches_data]
        for branch_data in branches_data:
            existing_branch = self.env['github.branch'].sudo().search([
                ('name', '=', branch_data['name']),
                ('repository_id', '=', self.id)
            ])
            branch_vals = {
                'repository_id': self.id,
                'name': branch_data['name'],
                'sha': branch_data['commit']['sha'],
                'is_default': branch_data['name'] == self.default_branch,
                'is_protected': branch_data.get('protected', False),
                'github_url': f"https://github.com/{self.owner}/{self.name}/tree/{branch_data['name']}",
            }
            if existing_branch:
                existing_branch.sudo().write(branch_vals)
                # Pass skip_heavy=True to avoid redundant deep sync during repo-level sync
                existing_branch.action_sync_branch(skip_heavy=True)
            else:
                new_branch = self.env['github.branch'].sudo().create(branch_vals)
                new_branch.action_sync_branch(skip_heavy=True)

        # Remove branches that no longer exist on GitHub
        branches_to_remove = self.env['github.branch'].sudo().search([
            ('repository_id', '=', self.id),
            ('name', 'not in', github_branch_names)
        ])
        if branches_to_remove:
            branches_to_remove.unlink()

    def _sync_collaborators(self):
        """Sync repository collaborators"""
        url = f"https://api.github.com/repos/{self.owner}/{self.name}/collaborators"
        params = {'per_page': 100}
        collaborators_data = self._fetch_all_pages(url, params=params)
        github_collab_ids = [collab['id'] for collab in collaborators_data]
        for collab in collaborators_data:
            existing = self.env['github.collaborator'].sudo().search([
                ('github_id', '=', collab['id']),
                ('repository_id', '=', self.id)
            ], limit=1)
            vals = {
                'repository_id': self.id,
                'github_id': collab['id'],
                'login': collab['login'],
                'html_url': collab['html_url'],
                'permissions': str(collab.get('permissions', {})),
                'type': collab.get('type'),
            }
            if existing:
                existing.write(vals)
            else:
                self.env['github.collaborator'].sudo().create(vals)

        # Remove collaborators that no longer exist on GitHub
        collabs_to_remove = self.env['github.collaborator'].sudo().search([
            ('repository_id', '=', self.id),
            ('github_id', 'not in', github_collab_ids)
        ])
        if collabs_to_remove:
            collabs_to_remove.unlink()


    def open_in_github(self):
        """Open repository in GitHub"""
        if self.url:
            return {
                'type': 'ir.actions.act_url',
                'url': self.url,
                'target': 'new',
            }


    def cron_github_sync(self):
        """
        Cron job to periodically sync all repositories.
        """
        repositories = self.env['github.repository'].search([('sync_status', '!=', 'syncing')])
        for repo in repositories:
            try:
                repo.action_sync_repository()
            except Exception as e:
                pass  # Errors are logged in the sync method

    @api.depends('issue_ids')
    def compute_open_issues_count(self):
        """
        Computes the number of open issues in the repository.
        """
        for record in self:
            record.open_issues_count = self.env['github.issue'].search_count(
                [('repository_id', '=', record.id), ('state', '=', 'open')])


    def action_view_commits(self):
        """
        Returns an action to view commits of the repository.
        """
        return {
            'type': 'ir.actions.act_window',
            'name': _('Commits'),
            'res_model': 'github.commit',
            'view_mode': 'tree,form',
            'domain': [('branch_id', 'in', self.branch_ids.ids),
                       ('repository_id', '=', self.id)],
            'context': {'search_default_group_by_repository_id': 1,
                        'search_default_group_by_branch_id': 1},
        }


    def create_new_github_branch(self, branch_name, base_branch_name="main"):
        """Create a new branch on GitHub from Odoo"""
        self.ensure_one()
        headers = self._get_github_headers()
        url = f"https://api.github.com/repos/{self.owner}/{self.name}/git/ref/heads/{base_branch_name}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise UserError(_("Failed to fetch base branch: %s") % response.text)
        base_ref = response.json()
        base_sha = base_ref["object"]["sha"]
        url = f"https://api.github.com/repos/{self.owner}/{self.name}/git/refs"
        payload = {
            "ref": f"refs/heads/{branch_name}",
            "sha": base_sha,
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code not in (200, 201):
            raise UserError(_("Failed to create branch: %s") % response.text)
        branch = self.env["github.branch"].sudo().create({
            "repository_id": self.id,
            "name": branch_name,
            "sync_status": "success",
            "last_sync": fields.Datetime.now(),
            "github_url": f"https://github.com/{self.owner}/{self.name}/tree/{branch_name}",
        })

        return {
            "type": "ir.actions.act_window",
            "name": _("Branch Created"),
            "res_model": "github.branch",
            "res_id": branch.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_export_to_github(self):
        """Create repository on GitHub if it doesn't exist"""
        self.ensure_one()
        if self.github_id:
            raise UserError(_("Repository is already linked to GitHub."))
        if not self.owner:
            config = self.env['github.config'].sudo().search([('active', '=', True)], limit=1)
            self.owner = config.username if config else False
            
        headers = self._get_github_headers()
        
        # Check if we should create in an organization or personal account
        user_response = requests.get("https://api.github.com/user", headers=headers)
        user_response.raise_for_status()
        authenticated_user = user_response.json()['login']
        
        if self.owner and self.owner.lower() != authenticated_user.lower():
            # Try to create in organization
            url = f"https://api.github.com/orgs/{self.owner}/repos"
        else:
            # Create in personal account
            url = "https://api.github.com/user/repos"
            
        payload = {
            "name": self.name,
            "description": self.description or "",
            "private": self.private
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 201:
            data = response.json()
            self.write({
                'github_id': str(data['id']),
                'full_name': data['full_name'],
                'url': data['html_url'],
                'clone_url': data['clone_url'],
                'owner': data['owner']['login'],
                'sync_status': 'success',
                'last_sync': fields.Datetime.now()
            })
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Repository created successfully on GitHub.'),
                    'type': 'success',
                }
            }
        else:
            raise UserError(_("Failed to create repository: %s") % response.text)

    def action_create_new_repository(self):
        """Action to open the form view for creating a new repository."""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create Repository'),
            'res_model': 'github.repository',
            'view_mode': 'form',
            'target': 'current',
            'context': self.env.context,
        }
