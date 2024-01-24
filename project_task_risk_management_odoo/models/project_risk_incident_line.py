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
from odoo import fields, models


class RiskIncident(models.Model):
    """ Model for Project Risk Incident Line"""
    _name = 'project.risk.incident.line'

    incident_order_id = fields.Many2one('project.project',
                                        string='Risk Reference',
                                        help='Reference of the Risk')
    risk = fields.Many2one('risks.project', string='Risk',
                           help='Select Risk', required=True)
    des = fields.Char(string="Description", help='Description of the project risk')
    category = fields.Many2one('risk.category', string='Category',
                               required=True, help='Category of the risk')
    risk_response = fields.Many2one('risk.response', string='Risk Response',
                                    required=True, help='Response of the risk')
    risk_type = fields.Many2one('risk.type', string='Risk Type', required=True,
                                help='Type of the risk')
    probability = fields.Float(string='Probability(%)', help='Probability of the risk incident in percentage')
    tag_ids = fields.Many2many('risk.tag', string='Tags', help='Risk Tag')
