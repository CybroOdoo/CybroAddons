# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER GENERAL PUBLIC
#    LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from __future__ import annotations

from odoo import api, fields, models


class EnviroEmissionFactorGasLine(models.Model):
    _name = "enviro.emission.factor.gas.line"
    _description = "Enviro Emission Factor Gas Line"
    _order = "factor_id, sequence, id"

    sequence = fields.Integer(default=10)
    factor_id = fields.Many2one(
        "enviro.emission.factor",
        required=True,
        ondelete="cascade",
        index=True,
    )
    gas_id = fields.Many2one("enviro.gas", required=True)
    gas_quantity_kg = fields.Float(
        string="Gas Quantity kg per Unit",
        required=True,
        digits=(16, 8),
        help="Gas mass emitted per factor unit before applying GWP.",
    )
    global_warming_potential = fields.Float(related="gas_id.global_warming_potential", string="GWP")
    kg_co2e_per_unit = fields.Float(
        string="kgCO2e per Unit",
        compute="_compute_kg_co2e_per_unit",
        store=True,
        digits=(16, 6),
    )

    @api.depends("gas_quantity_kg", "gas_id.global_warming_potential")
    def _compute_kg_co2e_per_unit(self) -> None:
        for line in self:
            line.kg_co2e_per_unit = line.gas_quantity_kg * line.gas_id.global_warming_potential

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines.factor_id._sync_gas_breakdown_total()
        return lines

    def write(self, vals):
        factors = self.factor_id
        result = super().write(vals)
        (factors | self.factor_id)._sync_gas_breakdown_total()
        return result

    def unlink(self):
        factors = self.factor_id
        result = super().unlink()
        factors._sync_gas_breakdown_total()
        return result
