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

from odoo import api, fields, models


class GitHubBranchCreateWizard(models.TransientModel):
    """
    Wizard to create a new GitHub branch from Odoo.
    """
    _name = "github.branch.create.wizard"
    _description = "Create GitHub Branch Wizard"

    repository_id = fields.Many2one("github.repository", required=True, readonly=True, help="The repository where the new branch will be created.")
    branch_name = fields.Char("New Branch Name", required=True, help="The name of the new branch to create on GitHub.")
    base_branch_name = fields.Char("Base Branch", required=True, help="The name of the existing branch to use as the starting point.")

    @api.model
    def default_get(self, fields_list):
        """Sets the default base branch from the repository's default branch."""
        res = super(GitHubBranchCreateWizard, self).default_get(fields_list)
        if 'repository_id' in res or self._context.get('default_repository_id'):
            repo_id = res.get('repository_id') or self._context.get('default_repository_id')
            repo = self.env['github.repository'].browse(repo_id)
            if repo.exists():
                res['base_branch_name'] = repo.default_branch or 'main'
        return res

    def action_confirm_create(self):
        """Perform branch creation action via the repository."""
        self.ensure_one()
        repo = self.repository_id
        repo.create_new_github_branch(self.branch_name, self.base_branch_name)
        return {"type": "ir.actions.act_window_close"}