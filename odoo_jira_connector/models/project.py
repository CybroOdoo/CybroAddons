# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import logging

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from .jira_client import JIRA_ERRORS, JiraClient, JiraError, project_key_from_name

_logger = logging.getLogger(__name__)


class ProjectProject(models.Model):
    """Extends project.project to integrate with Jira projects."""
    _inherit = 'project.project'

    project_id_jira = fields.Integer(string='Jira Project ID', readonly=True,
                                     help='ID of the matching project in Jira.')
    jira_project_key = fields.Char(readonly=True,
                                   help='Key of the matching project in Jira.')
    board_id_jira = fields.Integer(string='Jira Board ID', readonly=True,
                                   help='ID of the Jira board of this project.')
    sprint_active = fields.Boolean(help='Show the Sprint smart button.')

    @api.model_create_multi
    def create(self, vals_list):
        """Create projects and, in Automatic mode, create them in Jira too."""
        projects = super(ProjectProject, self.with_context(
            mail_create_nosubscribe=True)).create(vals_list)
        client = JiraClient.for_automatic_sync(self.env)
        to_export = projects.filtered(
            lambda p: not p.project_id_jira and not p.is_template)
        if client and to_export:
            to_export._jira_create_projects(client)
        return projects

    def _jira_create_projects(self, client):
        """Create these projects in Jira and store the Jira id and key.

        Projects whose name already exists in Jira are left alone."""
        try:
            jira_names = {project.get('name') for project in
                          client.get('/rest/api/3/project')
                          if isinstance(project, dict)}
        except JIRA_ERRORS as error:
            _logger.error("Failed to fetch projects from Jira: %s", error)
            jira_names = set()
        for project in self.filtered(lambda p: p.name not in jira_names):
            try:
                data = client.create_project(project.name,
                                             project_key_from_name(project.name))
                values = {'project_id_jira': int(data['projectId']),
                          'jira_project_key': data['projectKey']}
            except JiraError as error:
                if 'projectName' in error.errors:
                    raise ValidationError(self.env._(
                        "A project named %s already exists in Jira. Please "
                        "rename the project.", project.name)) from error
                if 'projectKey' in error.errors:
                    raise ValidationError(error.errors['projectKey']) from error
                _logger.error("Failed to create project %s in Jira: %s",
                              project.name, error)
                continue
            except (*JIRA_ERRORS, KeyError) as error:
                _logger.error("Failed to create project %s in Jira: %s",
                              project.name, error)
                continue
            project.write(values)

    def write(self, vals):
        """Update projects and, in Automatic mode, rename them in Jira too."""
        client = vals.get('name') and JiraClient.for_automatic_sync(self.env)
        if client:
            for project in self.filtered(
                    lambda p: p.jira_project_key and p.name != vals['name']):
                try:
                    client.put(f'/rest/api/3/project/{project.jira_project_key}',
                               {'name': vals['name']})
                except JIRA_ERRORS as error:
                    _logger.error("Failed to rename project %s in Jira: %s",
                                  project.jira_project_key, error)
        return super().write(vals)

    def action_get_sprint(self):
        """Returns an action to view sprints associated with the project."""
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Sprints'),
            'view_mode': 'list,form',
            'res_model': 'jira.sprint',
            'context': {'default_project_id': self.id},
            'domain': [('project_id', '=', self.id)],
        }


class ProjectTaskType(models.Model):
    """Extends project task stages with Jira identifiers."""
    _inherit = 'project.task.type'

    stages_jira_id = fields.Char(string='Jira Stage ID',
                                 help='ID of the matching status in Jira.')
    jira_project_key = fields.Char(help='Key of the Jira project of this stage.')
