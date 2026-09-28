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

from odoo import  _, api, fields, models
from odoo.exceptions import UserError
import requests
import json


class ProjectProject(models.Model):
    """
    Extends the project.project model to include GitHub repository and activity tracking.
    """
    _inherit = 'project.project'

    github_repository_ids = fields.Many2many(
        'github.repository',
        'github_repository_project_rel',
        'project_id',
        'repository_id',
        string='GitHub Repositories',
        help="All GitHub repositories linked to this project."
    )
    github_repository_id = fields.Many2one(
        'github.repository', string='Repository',
        help="Primary GitHub repository for this project.")
    github_repository_url = fields.Char(
        related='github_repository_id.url', string='Repository Url', readonly=True,
        help="The web URL of the linked GitHub repository.")
    enable_github = fields.Boolean(
        'Enable GitHub', default=False,
        help="If enabled, GitHub synchronization features will be active for this project.")
    github_collaborator_ids = fields.Many2many(
        'github.collaborator', compute='_compute_github_collaborators',
        string='Collaborators', readonly=True,
        help="Collaborators from the linked GitHub repository.")

    repositories_count = fields.Integer(
        'Repositories', compute='_compute_repositories_count',
        help="Total number of GitHub repositories linked to this project.")
    open_issues_count = fields.Integer(
        'Open Issues', compute='_compute_open_issues_count',
        help="Number of open GitHub issues across all linked repositories.")
    open_prs_count = fields.Integer(
        'Open PRs', compute='_compute_open_prs_count',
        help="Number of open GitHub pull requests across all linked repositories.")
    collaborators_count = fields.Integer(
        'Collaborators', compute='_compute_collaborators_count',
        help="Total number of collaborators from the linked GitHub repository.")

    @api.model_create_multi
    def create(self, vals_list):
        """Create project records and configure their GitHub repository settings."""
        for vals in vals_list:
            if vals.get('github_repository_id'):
                vals['enable_github'] = True
            elif vals.get('github_repository_ids'):
                vals['enable_github'] = True
        projects = super().create(vals_list)
        for project in projects:
            if project.github_repository_id and project.github_repository_id not in project.github_repository_ids:
                project.github_repository_ids = [(4, project.github_repository_id.id)]
            if project.github_repository_ids and not project.github_repository_id:
                project.github_repository_id = project.github_repository_ids[0].id
        return projects

    def write(self, vals):
        """Update project GitHub settings and synchronize repository associations."""
        if 'enable_github' in vals and not vals['enable_github']:
            vals['github_repository_ids'] = [(5, 0, 0)]
            vals['github_repository_id'] = False
            
        if vals.get('github_repository_id'):
            vals['enable_github'] = True
            
        res = super().write(vals)
        
        for project in self:
            if 'github_repository_id' in vals and project.github_repository_id:
                if project.github_repository_id not in project.github_repository_ids:
                    project.github_repository_ids = [(4, project.github_repository_id.id)]
                    
            if 'github_repository_ids' in vals:
                if not project.github_repository_ids:
                    if project.enable_github or project.github_repository_id:
                        project.write({
                            'enable_github': False,
                            'github_repository_id': False
                        })
                else:
                    update_vals = {}
                    if not project.enable_github:
                        update_vals['enable_github'] = True
                    if not project.github_repository_id or project.github_repository_id not in project.github_repository_ids:
                        update_vals['github_repository_id'] = project.github_repository_ids[0].id
                    if update_vals:
                        project.write(update_vals)
                        
        return res

    @api.depends('github_repository_id')
    def _compute_github_collaborators(self):
        """Link collaborators from the primary repository to the project."""
        for rec in self:
            rec.github_collaborator_ids = rec.github_repository_id.collaborator_ids if rec.github_repository_id else self.env['github.collaborator']

    @api.depends('github_collaborator_ids')
    def _compute_collaborators_count(self):
        """Calculate the total number of collaborators."""
        for rec in self:
            rec.collaborators_count = len(rec.github_collaborator_ids)

    def _compute_repositories_count(self):
        """
        Computes the number of GitHub repositories linked to the project.
        """
        for rec in self:
            rec.repositories_count = self.env['github.repository'].search_count([('project_ids', 'in', rec.ids)])

    def _compute_open_issues_count(self):
        """
        Computes the number of open GitHub issues across linked repositories.
        """
        for rec in self:
            rec.open_issues_count = self.env['github.issue'].search_count([('project_ids', 'in', rec.ids), ('state', '=', 'open')])

    def _compute_open_prs_count(self):
        """
        Computes the number of open GitHub pull requests across linked repositories.
        """
        for rec in self:
            rec.open_prs_count = self.env['github.pull.request'].search_count([('project_ids', 'in', rec.ids), ('state', '=', 'open')])

    def action_view_details(self):
        """
        Open the form view of the primary GitHub repository.
        :return: Act window action.
        """
        self.ensure_one()
        if not self.github_repository_id:
             raise UserError(_("No GitHub repository linked to this project."))
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'github.repository',
            'view_mode': 'form',
            'res_id': self.github_repository_id.id,
            'target': 'current',
        }

    def action_view_github_repositories(self):
        """
        View linked GitHub repositories in a list view.
        :return: Act window action.
        """
        return {
            'type': 'ir.actions.act_window',
            'name': _('GitHub Repositories'),
            'res_model': 'github.repository',
            'view_mode': 'list,form',
            'domain': [('project_ids', 'in', [self.id])],
            'context': {'default_project_ids': [(6, 0, [self.id])]},
        }
    def action_import_issues_from_github(self):
        """Sync issues for the linked repository and create tasks for new issues"""
        self.ensure_one()
        if not self.github_repository_id:
            raise UserError(_("Please link a GitHub repository to this project first."))

        # Record initial task count for this project
        initial_task_count = self.env['project.task'].search_count([('project_id', '=', self.id)])

        # 1. Sync issues from GitHub to our github.issue model
        # This may automatically create tasks via _sync_issues -> action_create_task
        self.github_repository_id._sync_issues()

        # 2. Find all issues for this repository and ensure they have tasks in THIS project
        # (Fallback in case _sync_issues didn't create them for this specific project)
        issues = self.env['github.issue'].search([
            ('repository_id', '=', self.github_repository_id.id)
        ])

        for issue in issues:
            # Check if a task already exists for this issue in THIS project
            existing_task = self.env['project.task'].search([
                ('github_issue_id', '=', issue.id),
                ('project_id', '=', self.id)
            ], limit=1)

            if not existing_task:
                # Create a new task in this project
                self.env['project.task'].create({
                    'name': f"[#{issue.number}] {issue.title}",
                    'project_id': self.id,
                    'description': issue.body or '',
                    'github_issue_id': issue.id,
                })

        # Calculate if new tasks were added
        final_task_count = self.env['project.task'].search_count([('project_id', '=', self.id)])
        new_tasks_added = final_task_count > initial_task_count

        if new_tasks_added:
            message = _('GitHub issues have been successfully synchronized and imported as tasks.')
        else:
            message = _('All GitHub issues are already synchronized with your tasks.')

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Issues Sync'),
                'message': message,
                'type': 'success',
            }
        }

    def action_export_tasks_to_github(self):
        """Export project tasks to GitHub issues"""
        self.ensure_one()
        if not self.github_repository_id:
            raise UserError(_("Please link a GitHub repository to this project first."))
        
        repo = self.github_repository_id
        headers = repo._get_github_headers()
        url = f"https://api.github.com/repos/{repo.owner}/{repo.name}/issues"
        
        tasks_to_export = self.env['project.task'].search([
            ('project_id', '=', self.id),
            ('github_issue_id', '=', False)
        ])
        
        if not tasks_to_export:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Tasks to Export'),
                    'message': _('All tasks in this project are already linked to GitHub issues.'),
                    'type': 'info',
                }
            }
            
        success_count = 0
        for task in tasks_to_export:
            data = {
                'title': task.name,
                'body': task.description or '',
            }
            try:
                response = requests.post(url, headers=headers, data=json.dumps(data), timeout=10)
                if response.status_code == 201:
                    issue_data = response.json()
                    # Create the github.issue record in Odoo
                    issue_vals = {
                        'repository_id': repo.id,
                        'github_id': str(issue_data['id']),
                        'number': issue_data['number'],
                        'title': issue_data['title'],
                        'body': issue_data.get('body', ''),
                        'state': issue_data['state'],
                        'github_url': issue_data['html_url'],
                        'created_at': repo._parse_github_datetime(issue_data['created_at']),
                        'updated_at': repo._parse_github_datetime(issue_data['updated_at']),
                    }
                    new_issue = self.env['github.issue'].create(issue_vals)
                    task.write({'github_issue_id': new_issue.id})
                    success_count += 1
            except Exception as e:
                continue
                
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Export Complete'),
                'message': _('Successfully exported %s tasks to GitHub.') % success_count,
                'type': 'success',
            }
        }
