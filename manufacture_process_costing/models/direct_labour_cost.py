# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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


class DirectLabourCost(models.Model):
    """This class creates a new model with the name direct.labour.cost"""
    _name = 'direct.labour.cost'
    _description = 'Direct Labour Cost'

    labour_cost_id = fields.Many2one('mrp.bom',
                                     string='Labour Cost',
                                     help='Corresponding bill of materials')
    operation = fields.Char(string='Operation',
                            help='Operation required for the work')
    work_center_id = fields.Many2one('mrp.workcenter',
                                     string='Work Center',
                                     help='Corresponding work center')
    planned_minute = fields.Float(string='Planned Minute',
                                  help='Planned minutes for the work')
    cost_minute = fields.Float(string='Cost/Minute',
                               help='Cost per minute for the work')
    total_cost = fields.Float(compute='_compute_total_cost', store=True,
                              string='Total Cost', help='Total labour cost')
    production_labour_id = fields.Many2one('mrp.production',
                                           string='Production Labour',
                                           help='corresponding manufacturing '
                                                'order')
    actual_minute = fields.Float(string='Actual Minute',
                                 help='Actual minutes taken for the work')
    total_actual_cost = fields.Float(compute='_compute_total_actual_cost',
                                     string='Total Actual Cost',
                                     help='Total Actual labour cost')

    @api.depends('planned_minute', 'cost_minute')
    def _compute_total_cost(self):
        """Calculate total_cost based on planned_minute and cost_minute"""
        for rec in self:
            rec.total_cost = rec.planned_minute * rec.cost_minute

    @api.depends('actual_minute', 'cost_minute')
    def _compute_total_actual_cost(self):
        """Calculate total_actual_cost based on actual_minute and cost_minute"""
        for rec in self:
            rec.total_actual_cost = rec.actual_minute * rec.cost_minute
