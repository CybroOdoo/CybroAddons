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


class DirectMaterialCost(models.Model):
    """This class creates a new model with the name direct.material.cost"""
    _name = 'direct.material.cost'
    _description = 'Direct Material Cost'

    material_cost_id = fields.Many2one('mrp.bom',
                                       string='Material Cost',
                                       help='Corresponding bill of materials')
    product_id = fields.Many2one('product.product',
                                 string='Product',
                                 help='Product required for the work')
    planned_qty = fields.Integer(string='Planned Qty',
                                 help='Planned minutes for the work')
    uom_id = fields.Many2one('uom.uom', string='UoM',
                             help="Unit of measure")
    cost_unit = fields.Float(string='Cost/Unit',
                             help='Cost per unit for the work')
    total_cost = fields.Float(compute='_compute_total_cost', store=True,
                              string='Total Cost', help='Total material cost')
    production_material_id = fields.Many2one('mrp.production',
                                             string='Production Material',
                                             help='Corresponding manufacturing '
                                                  'order')
    actual_quantity = fields.Integer(string='Actual Quantity',
                                     help='Actual quantity taken for the work')
    total_actual_cost = fields.Float(compute='_compute_total_actual_cost',
                                     string='Total Actual Cost',
                                     help='Total actual material cost')

    @api.depends('planned_qty', 'cost_unit')
    def _compute_total_cost(self):
        """Calculate total_cost based on planned_qty and cost_unit"""
        for rec in self:
            rec.total_cost = rec.planned_qty * rec.cost_unit

    @api.depends('actual_quantity', 'cost_unit')
    def _compute_total_actual_cost(self):
        """Calculate total_actual_cost based on actual_quantity and cost_unit"""
        for rec in self:
            rec.total_actual_cost = rec.actual_quantity * rec.cost_unit
