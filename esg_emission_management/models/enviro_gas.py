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
from odoo.exceptions import ValidationError


class EnviroGas(models.Model):
    _name = "enviro.gas"
    _description = "Greenhouse Gas"
    _order = "sequence, name"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    category = fields.Selection(
        selection=[
            ("co2", "Carbon Dioxide"),
            ("ch4", "Methane"),
            ("n2o", "Nitrous Oxide"),
            ("hfc", "Hydrofluorocarbons"),
            ("pfc", "Perfluorocarbons"),
            ("sf6", "Sulfur Hexafluoride"),
            ("nf3", "Nitrogen Trifluoride"),
            ("other", "Other"),
        ],
        default="other",
        required=True,
    )
    global_warming_potential = fields.Float(
        string="GWP",
        required=True,
        digits=(16, 6),
        help="100-year global warming potential relative to CO2.",
    )
    notes = fields.Text()

    _sql_constraints = [
        ("enviro_gas_code_uniq", "unique(code)", "The gas code must be unique."),
        ("enviro_gas_gwp_positive", "CHECK(global_warming_potential > 0)", "GWP must be greater than zero."),
    ]

    @api.constrains("code")
    def _check_code(self) -> None:
        for gas in self:
            if gas.code and gas.code != gas.code.lower():
                raise ValidationError("Gas code must be lowercase.")
