# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Dhanya B (odoo@cybrosys.com)
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
##############################################################################
import json
import requests
from requests.auth import HTTPBasicAuth
from odoo import models, fields, api


class ProjectTaskType(models.Model):
    """This class is inherited for adding some extra field and override the
        create function
        Methods:
            create(vals):
                extends create() to export tasks stages to Jira"""
    _inherit = 'project.task.type'

    stages_jira_id = fields.Integer(string="Jira ID",
                                    help="Jira id for task stages.",
                                    readonly=True)
    jira_project_key = fields.Char(string='Jira Project Key',
                                   help='Corresponding project key of Jira.',
                                   readonly=True)
    jira_stages_category = fields.Selection([
        ('TO_DO', 'TO_DO'),
        ('IN_PROGRESS', 'IN_PROGRESS'),
        ('DONE', 'DONE')],
        default='IN_PROGRESS',
        string="Jira Status Category", help="Here we can choose the category "
                                            "and the Stage will create in "
                                            "jira under the chosen category.")

    @api.model_create_multi
    def create(self, vals):
        """ Override the create method of tasks stages to export
        tasks stages to Jira """
        stages = super(ProjectTaskType, self).create(vals)
        for stage in stages:
            if stage.stages_jira_id == 0 and len(stage.project_ids) == 1:
                ir_config_parameter = self.env['ir.config_parameter'].sudo()
                if ir_config_parameter.get_param('odoo_jira_connector'
                                                 '.connection'):
                    url = ir_config_parameter.get_param('odoo_jira_connector'
                                                        '.url',
                                                        False)
                    user = ir_config_parameter.get_param(
                        'odoo_jira_connector.user_id_jira', False)
                    password = ir_config_parameter.get_param(
                        'odoo_jira_connector.api_token', False)
                    auth = HTTPBasicAuth(user, password)
                    if stage.project_ids[0].sprint_active:
                        payload = json.dumps({
                            "scope": {
                                "project": {
                                    "id": str(stage.project_ids[0].
                                              project_id_jira)
                                },
                                "type": "PROJECT"
                            },
                            "statuses": [
                                {
                                    "description": "The issue is resolved",
                                    "name": stages.name,
                                    "statusCategory": str(
                                        stage.jira_stages_category),
                                }
                            ]
                        })
                    else:
                        payload = json.dumps({
                            "scope": {
                                "type": "GLOBAL"
                            },
                            "statuses": [
                                {
                                    "description": "The issue is resolved",
                                    "name": stage.name,
                                    "statusCategory": str(
                                        stage.jira_stages_category),
                                }
                            ]
                        })
                    headers = {
                        "Accept": "application/json",
                        "Content-Type": "application/json"
                    }
                    requests.request(
                        "POST",
                        url + "rest/api/3/statuses",
                        data=payload,
                        headers=headers,
                        auth=auth
                    )
            return stages
