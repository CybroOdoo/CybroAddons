# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import models, fields, _


class ProjectTasksRisk(models.Model):
    _inherit = 'project.task'

    task_risk_incident_line = fields.One2many('task.risk.incident.line',
                                              'task_incident_order_id',
                                              string='Risk Incident Lines')

    def task_create_incident_wiz(self):
        return {
            'name': _('Create Incident'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'risk.incident.wiz',
            'target': 'new',
            'context': (
                {'default_user_id': self.project_id.user_id.id,
                 'default_project_id': self.project_id.id})
        }


class RiskIncident(models.Model):
    _name = 'task.risk.incident.line'

    task_incident_order_id = fields.Many2one('project.task', string='Risk '
                                                                    'Reference')
    risk = fields.Many2one('risks.project', string='Risk', required=True)
    des = fields.Char(string="Description")
    category = fields.Many2one('risk.category', string='Category',
                               required=True)
    risk_response = fields.Many2one('risk.response', string='Risk Response',
                                    required=True)
    risk_type = fields.Many2one('risk.type', string='Risk Type', required=True)
    probability = fields.Float(string='Probability(%)')
    tag_ids = fields.Many2many('risk.tag', string='Tags')
