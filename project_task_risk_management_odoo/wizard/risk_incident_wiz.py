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
from odoo import models, fields


class RiskIncident(models.TransientModel):
    _name = 'risk.incident.wiz'

    risk_incident = fields.Char(string='Risk Incident', required=True)
    note = fields.Text(string='Description', required=True)
    user_id = fields.Many2one('res.users', string='Assigned to')
    project_id = fields.Many2one('project.project', string='Project',
                                 required=True)
    image = fields.Binary(string='Incident Photo')

    def create_incident(self):
        self.env['risk.incident'].create({
            'risk_incident': self.risk_incident,
            'user_id': self.user_id.id,
            'project_id': self.project_id.id,
            'incident_image': self.image,
            'note': self.note
        })
