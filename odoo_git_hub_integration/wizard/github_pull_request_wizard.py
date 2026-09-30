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

from odoo import fields, models
from odoo.exceptions import UserError
from dateutil import parser
import requests


class GitHubPullRequestWizard(models.TransientModel):
    """
    Wizard to create a new GitHub Pull Request directly from Odoo.
    """
    _name = 'github.pull.request.wizard'
    _description = 'Create GitHub Pull Request'

    repository_id = fields.Many2one('github.repository', 'Repository', required=True, help="The repository where the pull request will be opened.")
    head_branch = fields.Char('Source Branch', required=True, help="The branch containing your changes (head).")
    base_branch = fields.Char('Target Branch', required=True, help="The branch you want to merge your changes into (base).")
    name = fields.Char('Title', required=True, help="The summary title for the pull request.")
    description = fields.Text('Description', help="Detailed information about the changes in this pull request.")
    draft = fields.Boolean('Create as Draft', default=False, help="If checked, the PR will be created in draft mode.")

    def action_create_pull_request(self):
        """Create a pull request on GitHub and corresponding record in Odoo."""
        headers = self.repository_id._get_github_headers()
        url = f"https://api.github.com/repos/{self.repository_id.owner}/{self.repository_id.name}/pulls"
        data = {
            'title': self.name,
            'head': self.head_branch,
            'base': self.base_branch,
            'body': self.description or '',
            'draft': self.draft,
        }
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 201:
            pr_data = response.json()
            created_at = parser.isoparse(pr_data['created_at'])
            if created_at.tzinfo:
                created_at = created_at.replace(tzinfo=None)
            updated_at = parser.isoparse(pr_data['updated_at'])
            if updated_at.tzinfo:
                updated_at = updated_at.replace(tzinfo=None)
            pr_vals = {
                'repository_id': self.repository_id.id,
                'github_id': str(pr_data['id']),
                'number': pr_data['number'],
                'title': pr_data['title'],
                'body': pr_data.get('body', ''),
                'state': pr_data['state'],
                'github_url': pr_data['html_url'],
                'created_at': created_at,
                'updated_at': updated_at,
                'author': pr_data['user']['login'],
                'head_branch': pr_data['head']['ref'],
                'base_branch': pr_data['base']['ref'],
            }
            pr = self.env['github.pull.request'].create(pr_vals)
            return {
                'type': 'ir.actions.act_window',
                'name': _('Pull Request Created'),
                'res_model': 'github.pull.request',
                'res_id': pr.id,
                'view_mode': 'form',
                'target': 'current',
            }
        else:
            try:
                error_data = response.json()
                message = error_data.get('message', 'Unknown error')
                if 'errors' in error_data:
                    details = []
                    for err in error_data['errors']:
                        if err.get('message'):
                            details.append(err['message'])
                        elif err.get('code') == 'custom':
                            details.append(err.get('message', 'Custom validation failed'))
                    if details:
                        message = f"{message}: {', '.join(details)}"
                
                # Common GitHub error translations
                if "No commits between" in message:
                    message = _("The source branch '%s' has no new changes compared to '%s'. Please push your commits to GitHub before creating a pull request.") % (self.head_branch, self.base_branch)
                elif "already exists" in message.lower():
                    message = _("A pull request already exists for these branches.")
                
                raise UserError(_("GitHub API Error: %s") % message)
            except (ValueError, KeyError):
                raise UserError(_('Failed to create pull request: %s') % response.text)