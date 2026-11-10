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
from odoo import api, models


class MrpRoutingWorkcenter(models.Model):
    """Inherits mrp.routing.workcenter to automatically synchronize labour
    and overhead costing lines on the BOM when operations are created,
    updated, or removed."""
    _inherit = 'mrp.routing.workcenter'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_process_costs()
        return records

    def write(self, vals):
        res = super().write(vals)
        if any(f in vals for f in ('name', 'workcenter_id', 'time_cycle', 'bom_id')):
            self._sync_process_costs()
        return res

    def unlink(self):
        labour_lines = self.env['direct.labour.cost'].search([('routing_workcenter_id', 'in', self.ids)])
        overhead_lines = self.env['direct.overhead.cost'].search([('routing_workcenter_id', 'in', self.ids)])
        labour_lines.unlink()
        overhead_lines.unlink()
        return super().unlink()

    def _sync_process_costs(self):
        """Sync operation data into direct.labour.cost and direct.overhead.cost on BOM."""
        process = self.env['ir.config_parameter'].sudo()
        process_value = process.get_str('manufacture_process_costing.process_costing_method')
        is_workcenter = (process_value == 'work-center')

        labour_model = self.env['direct.labour.cost']
        overhead_model = self.env['direct.overhead.cost']

        for op in self:
            if not op.bom_id:
                continue

            # --- Sync Labour Cost ---
            labour = labour_model.search([('routing_workcenter_id', '=', op.id)], limit=1)
            if not labour:
                labour = labour_model.search([
                    ('labour_cost_id', '=', op.bom_id.id),
                    ('routing_workcenter_id', '=', False),
                    ('operation', '=', op.name)
                ], limit=1)
            labour_vals = {
                'labour_cost_id': op.bom_id.id,
                'routing_workcenter_id': op.id,
                'operation': op.name,
                'work_center_id': op.workcenter_id.id if op.workcenter_id else False,
                'planned_minute': op.time_cycle,
            }
            if not labour:
                labour_vals['cost_minute'] = op.workcenter_id.labour_cost if (is_workcenter and op.workcenter_id) else 0.0
                labour_model.create(labour_vals)
            else:
                if is_workcenter and op.workcenter_id:
                    labour_vals['cost_minute'] = op.workcenter_id.labour_cost
                labour.write(labour_vals)

            # --- Sync Overhead Cost ---
            overhead = overhead_model.search([('routing_workcenter_id', '=', op.id)], limit=1)
            if not overhead:
                overhead = overhead_model.search([
                    ('overhead_cost_id', '=', op.bom_id.id),
                    ('routing_workcenter_id', '=', False),
                    ('operation', '=', op.name)
                ], limit=1)
            overhead_vals = {
                'overhead_cost_id': op.bom_id.id,
                'routing_workcenter_id': op.id,
                'operation': op.name,
                'work_center_id': op.workcenter_id.id if op.workcenter_id else False,
                'planned_minute': op.time_cycle,
            }
            if not overhead:
                overhead_vals['cost_minute'] = op.workcenter_id.overhead_cost if (is_workcenter and op.workcenter_id) else 0.0
                overhead_model.create(overhead_vals)
            else:
                if is_workcenter and op.workcenter_id:
                    overhead_vals['cost_minute'] = op.workcenter_id.overhead_cost
                overhead.write(overhead_vals)
