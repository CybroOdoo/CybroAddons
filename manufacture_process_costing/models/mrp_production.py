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


class MrpProduction(models.Model):
    """This class inherits the existing class mrp production to add the
    additional feature of the costing methods"""
    _inherit = 'mrp.production'

    material_cost_ids = fields.One2many('direct.material.cost',
                                        'production_material_id',
                                        string='Material Costs')
    labour_cost_ids = fields.One2many('direct.labour.cost',
                                      'production_labour_id',
                                      string='Labour Costs')
    overhead_cost_ids = fields.One2many('direct.overhead.cost',
                                        'production_overhead_id',
                                        string='Overhead Costs')
    total_material_cost = fields.Float(compute='_compute_total_material_cost',
                                       store=True,
                                       string='Total Material Cost',
                                       help='Total Material Cost of production')
    total_labour_cost = fields.Float(compute='_compute_total_labour_cost',
                                     store=True, string='Total Labour Cost',
                                     help='Total Labour Cost of production')
    total_overhead_cost = fields.Float(compute='_compute_total_overhead_cost',
                                       store=True,
                                       string='Total Overhead Cost',
                                       help='Total Overhead Cost of production')
    total_cost = fields.Float(compute='_compute_total_cost', store=True,
                              help='Total Cost of production',
                              string='Total Cost')
    total_actual_material_cost = fields.Float(
        string='Total Actual Material Cost',
        compute='_compute_total_actual_material_cost', store=True,
        help='Total Actual Material Cost of production')
    total_actual_labour_cost = fields.Float(string='Total Actual Labour Cost',
                                            compute='_compute_total_actual_'
                                                    'labour_cost',
                                            store=True,
                                            help='Total Actual Labour Cost '
                                                 'of production')
    total_actual_overhead_cost = fields.Float(
        string='Total Actual Overhead Cost',
        compute='_compute_total_actual_overhead_cost', store=True,
        help='Total Actual Overhead Cost of production')
    total_actual_cost = fields.Float(compute='_compute_total_actual_cost',
                                     store=True, string='Total Actual Cost',
                                     help='Total Actual Cost of production')

    def action_cancel_button(self):
        """Returns the mrp.cancel.reason"""
        reason = self.env['mrp.cancel.reason'].create(
            {'manufacturing_id': self.id})
        return {
            'type': 'ir.actions.act_window',
            'name': 'Cancel Reason',
            'view_mode': 'form',
            'res_model': 'mrp.cancel.reason',
            'target': 'new',
            'view_type': 'form',
            'res_id': reason.id,
        }

    @api.model_create_multi
    def create(self, vals_list):
        """Writes data to material_cost_ids, labour_cost_ids and
        overhead_cost_ids when change in bom_id"""
        res = super().create(vals_list)
        res.write({'material_cost_ids': [(5, 0)]})
        res.write({
            'material_cost_ids': [
                (0, 0, {
                    'production_material_id': res.id,
                    'material_cost_id': res.bom_id.id,
                    'product_id': rec.product_id.id,
                    'planned_qty': rec.planned_qty,
                    'uom_id': rec.uom_id.id,
                    'cost_unit': rec.cost_unit,
                }) for rec in res.bom_id.material_cost_ids]
        })
        res.write({'labour_cost_ids': [(5, 0)]})
        res.write({
            'labour_cost_ids': [
                (0, 0, {
                    'production_labour_id': res.id,
                    'labour_cost_id': rec.id,
                    'operation': rec.operation,
                    'work_center_id': rec.work_center_id.id,
                    'planned_minute': rec.planned_minute,
                    'cost_minute': rec.cost_minute,
                }) for rec in res.bom_id.labour_cost_ids]
        })
        res.write({'overhead_cost_ids': [(5, 0)]})
        res.write({
            'overhead_cost_ids': [
                (0, 0, {
                    'production_overhead_id': res.id,
                    'overhead_cost_id': rec.id,
                    'operation': rec.operation,
                    'work_center_id': rec.work_center_id.id,
                    'planned_minute': rec.planned_minute,
                    'cost_minute': rec.cost_minute,
                }) for rec in res.bom_id.overhead_cost_ids]
        })
        return res

    @api.onchange('bom_id')
    def _onchange_bom_id(self):
        """Writes data to material_cost_ids, labour_cost_ids and
        overhead_cost_ids when change in bom_id"""
        self.write({'material_cost_ids': [(5, 0)]})
        self.write({
            'material_cost_ids': [
                (0, 0, {
                    'production_material_id': self.id,
                    'material_cost_id': self.bom_id.id,
                    'product_id': rec.product_id.id,
                    'planned_qty': rec.planned_qty,
                    'uom_id': rec.uom_id.id,
                    'cost_unit': rec.cost_unit,
                }) for rec in self.bom_id.material_cost_ids]
        })
        self.write({'labour_cost_ids': [(5, 0)]})
        self.write({
            'labour_cost_ids': [
                (0, 0, {
                    'production_labour_id': self.id,
                    'labour_cost_id': rec.id,
                    'operation': rec.operation,
                    'work_center_id': rec.work_center_id.id,
                    'planned_minute': rec.planned_minute,
                    'cost_minute': rec.cost_minute,
                }) for rec in self.bom_id.labour_cost_ids]
        })
        self.write({'overhead_cost_ids': [(5, 0)]})
        self.write({
            'overhead_cost_ids': [
                (0, 0, {
                    'production_overhead_id': self.id,
                    'overhead_cost_id': rec.id,
                    'operation': rec.operation,
                    'work_center_id': rec.work_center_id.id,
                    'planned_minute': rec.planned_minute,
                    'cost_minute': rec.cost_minute,
                }) for rec in self.bom_id.overhead_cost_ids]
        })

    @api.depends('material_cost_ids.total_cost')
    def _compute_total_material_cost(self):
        """Calculate total_material_cost"""
        for result in self:
            result.total_material_cost = sum(
                result.mapped('material_cost_ids').mapped('total_cost'))

    @api.depends('labour_cost_ids.total_cost')
    def _compute_total_labour_cost(self):
        """Calculate total_labour_cost"""
        for result in self:
            result.total_labour_cost = sum(
                result.mapped('labour_cost_ids').mapped('total_cost'))

    @api.depends('overhead_cost_ids.total_cost')
    def _compute_total_overhead_cost(self):
        """Calculates total_overhead_cost"""
        for result in self:
            result.total_overhead_cost = sum(
                result.mapped('overhead_cost_ids').mapped('total_cost'))

    @api.depends('total_material_cost', 'total_labour_cost',
                 'total_overhead_cost')
    def _compute_total_cost(self):
        """Calculates total_cost"""
        for rec in self:
            rec.total_cost = rec.total_material_cost + \
                             rec.total_labour_cost + rec.total_overhead_cost

    @api.depends('material_cost_ids.total_actual_cost')
    def _compute_total_actual_material_cost(self):
        """Calculates total_actual_material_cost"""
        for cost in self:
            cost.total_actual_material_cost = sum(
                cost.mapped('material_cost_ids').mapped('total_actual_cost'))

    @api.depends('labour_cost_ids.total_actual_cost')
    def _compute_total_actual_labour_cost(self):
        """Calculates total_actual_labour_cost"""
        for cost in self:
            cost.total_actual_labour_cost = sum(
                cost.mapped('labour_cost_ids').mapped('total_actual_cost'))

    @api.depends('overhead_cost_ids.total_actual_cost')
    def _compute_total_actual_overhead_cost(self):
        """Calculates total_actual_overhead_cost"""
        for cost in self:
            cost.total_actual_overhead_cost = sum(
                cost.mapped('overhead_cost_ids').mapped('total_actual_cost'))

    @api.depends('total_actual_material_cost', 'total_actual_labour_cost',
                 'total_actual_overhead_cost')
    def _compute_total_actual_cost(self):
        """Calculates total_actual_cost"""
        for rec in self:
            rec.total_actual_cost = rec.total_actual_material_cost + \
                                    rec.total_actual_labour_cost + \
                                    rec.total_actual_overhead_cost
