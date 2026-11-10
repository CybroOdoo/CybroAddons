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
#############################################################################
from odoo import Command, api, fields, models


class MrpBom(models.Model):
    """This class inherits the existing class mrp.bom to add the
    additional features of the costing"""
    _inherit = 'mrp.bom'

    material_cost_ids = fields.One2many('direct.material.cost',
                                        'material_cost_id',
                                        string='Material Cost',
                                        help="Material cost")

    labour_cost_ids = fields.One2many('direct.labour.cost',
                                      'labour_cost_id',
                                      string='Labour Cost', help="Labour cost")

    overhead_cost_ids = fields.One2many('direct.overhead.cost',
                                        'overhead_cost_id',
                                        string='Overhead Cost', help="Overhead "
                                                                     "cost")
    total_material_cost = fields.Float(compute='_compute_total_material_cost',
                                       string='Total Material Cost',
                                       store=True, help='Total Material Cost')
    total_labour_cost = fields.Float(compute='_compute_total_labour_cost',
                                     string='Total Labour Cost',
                                     store=True, help='Total Labour Cost')
    total_overhead_cost = fields.Float(compute='_compute_total_overhead_cost',
                                       string='Total Overhead Cost',
                                       store=True, help='Total Overhead Cost')

    @api.onchange('bom_line_ids')
    def _onchange_bom_line_ids(self):
        """Update material_cost_ids when bom_line_ids is changed"""
        self.material_cost_ids = [Command.clear()] + [
            Command.create({
                'product_id': rec.product_id.id,
                'planned_qty': rec.product_qty,
                'uom_id': rec.product_id.uom_id.id,
                'cost_unit': rec.product_id.lst_price,
            }) for rec in self.bom_line_ids
        ]

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_operations_to_costs()
        return records

    def write(self, vals):
        res = super().write(vals)
        if 'operation_ids' in vals:
            self._sync_operations_to_costs()
        return res

    def _sync_operations_to_costs(self):
        """Ensure all operations have corresponding labour and overhead cost lines."""
        for bom in self:
            bom.operation_ids._sync_process_costs()
            op_ids = bom.operation_ids.ids
            bom.labour_cost_ids.filtered(
                lambda l: l.routing_workcenter_id and l.routing_workcenter_id.id not in op_ids
            ).unlink()
            bom.overhead_cost_ids.filtered(
                lambda l: l.routing_workcenter_id and l.routing_workcenter_id.id not in op_ids
            ).unlink()

    @api.onchange('operation_ids')
    def _onchange_operation_ids(self):
        """Update labour_cost_ids and overhead_cost_ids when
        operation_ids is changed"""
        process = self.env['ir.config_parameter'].sudo()
        process_value = process.get_str(
            'manufacture_process_costing.process_costing_method')
        is_workcenter = (process_value == 'work-center')

        self.labour_cost_ids = [Command.clear()] + [
            Command.create({
                'operation': rec.name,
                'work_center_id': rec.workcenter_id.id if rec.workcenter_id else False,
                'planned_minute': rec.time_cycle,
                'cost_minute': rec.workcenter_id.labour_cost if (is_workcenter and rec.workcenter_id) else 0.0,
                'routing_workcenter_id': rec.id if isinstance(rec.id, int) else False,
            }) for rec in self.operation_ids
        ]
        self.overhead_cost_ids = [Command.clear()] + [
            Command.create({
                'operation': rec.name,
                'work_center_id': rec.workcenter_id.id if rec.workcenter_id else False,
                'planned_minute': rec.time_cycle,
                'cost_minute': rec.workcenter_id.overhead_cost if (is_workcenter and rec.workcenter_id) else 0.0,
                'routing_workcenter_id': rec.id if isinstance(rec.id, int) else False,
            }) for rec in self.operation_ids
        ]

    @api.depends('material_cost_ids.total_cost')
    def _compute_total_material_cost(self):
        """Calculates Total material costs"""
        for result in self:
            result.ensure_one()
            result.total_material_cost = 0.00
            if result.material_cost_ids:
                result.total_material_cost = sum(
                    result.material_cost_ids.mapped('total_cost'))

    @api.depends('labour_cost_ids.total_cost')
    def _compute_total_labour_cost(self):
        """Calculate total labour costs"""
        for result in self:
            result.ensure_one()
            result.total_labour_cost = 0.00
            if result.labour_cost_ids:
                result.total_labour_cost = sum(
                    result.labour_cost_ids.mapped('total_cost'))

    @api.depends('overhead_cost_ids.total_cost')
    def _compute_total_overhead_cost(self):
        """Calculate total overhead costs"""
        for result in self:
            result.ensure_one()
            result.total_overhead_cost = 0.00
            if result.overhead_cost_ids:
                result.total_overhead_cost = sum(
                    result.overhead_cost_ids.mapped('total_cost'))
