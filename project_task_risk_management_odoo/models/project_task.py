# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import fields, models, _


class ProjectTasksRisk(models.Model):
    """ Inherits project task and adding fields """
    _inherit = 'project.task'

    task_risk_incident_line = fields.One2many('task.risk.incident.line',
                                              'task_incident_order_id',
                                              string='Risk Incident Lines',
                                              help='Risk Incident Lines')

    def task_create_incident_wiz(self):
        """ Returns Wizard"""
        return {
            'name': _('Create Incident'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'risk.incident.simplified',
            'target': 'new',
            'context': (
                {'default_user_id': self.project_id.user_id.id,
                 'default_project_id': self.project_id.id})
        }
