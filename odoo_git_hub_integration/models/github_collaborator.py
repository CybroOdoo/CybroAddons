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

class GitHubCollaborator(models.Model):
    """
    Represents a GitHub Collaborator for a specific repository.
    """
    _name = 'github.collaborator'
    _description = 'GitHub Collaborator'
    _rec_name = 'login'
    _order = 'login'

    repository_id = fields.Many2one('github.repository', 'Repository', required=True, ondelete='cascade', help="The repository this collaborator has access to.")
    github_id = fields.Char('GitHub ID', readonly=True, help="The unique numerical ID assigned to this user by GitHub.")
    login = fields.Char('Login', required=True, help="The GitHub username (login) of the collaborator.")
    html_url = fields.Char('Profile URL', help="Link to the collaborator's GitHub profile.")
    type = fields.Char('Type', help="The type of user (e.g., User or Organization).")
    permissions = fields.Char('Permissions', help="JSON-formatted string of permissions this user has on the repository.")
    
    _sql_constraints = [
        ('github_id_repo_unique', 'unique(github_id, repository_id)', 'The GitHub ID must be unique per repository!'),
    ]
