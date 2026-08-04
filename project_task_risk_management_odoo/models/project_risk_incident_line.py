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
from odoo import api, fields, models


class RiskIncident(models.Model):
    """ Model for Project Risk Incident Line"""
    _name = 'project.risk.incident.line'
    _description = 'Project Risk Incident Line'

    incident_order_id = fields.Many2one('project.project',
                                        string='Risk Reference',
                                        help='Reference of the Risk')
    risk_id = fields.Many2one('risks.project', string='Risk',
                              help='Select Risk', required=True)
    des = fields.Char(string="Description", help='Description of the project risk')
    category_id = fields.Many2one('risk.category', string='Category',
                                  help='Category of the risk')
    risk_response_id = fields.Many2one('risk.response', string='Risk Response',
                                       help='Response of the risk')
    risk_type_id = fields.Many2one('risk.type', string='Risk Type',
                                   help='Type of the risk')
    probability = fields.Float(string='Probability(%)', help='Probability of the risk incident in percentage')
    tag_ids = fields.Many2many('risk.tag', string='Tags', help='Risk Tag')

    @api.onchange('risk_id')
    def _onchange_risk_id(self):
        """ Onchange function to set default values"""
        if self.risk_id:
            self.category_id = self.risk_id.category_id.id or False
            self.risk_response_id = self.risk_id.risk_response_id.id or False
            self.risk_type_id = self.risk_id.risk_type_id.id or False
            self.tag_ids = self.risk_id.tag_ids or False
